"""Builds docs/PharmaStock-Modules.pdf: how ERPNext Stock and Frappe Health work together, module by module.

Everything in it was checked on a running v16 site (native behaviour, no custom screens).

    python3 docs/flows/build_modules.py        # needs Google Chrome
"""
import pathlib
import subprocess

import build as common
from seq import arrow, box, container, diagram, sequence, tspans

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
ul, table = common.ul, common.table


def lane(i, t, sub, tone):
    return (i, t, sub, tone)


USER = lane("U", "User", "storekeeper · nurse", "app")
SE = lane("SE", "Stock Entry", "ERPNext Stock", "stock")
IB = lane("IB", "Item · Batch", "ERPNext Stock", "stock")
LB = lane("LB", "Ledger · Bin", "ERPNext Stock", "stock")
MR = lane("MR", "Material Request", "ERPNext Stock", "stock")


def page(kicker, title, lead, body):
    return f'<section class="sec"><div class="kicker">{kicker}</div><h2>{title}</h2><p class="lead">{lead}</p>{body}</section>'


def fig(svg):
    return f'<div class="fig">{svg}</div>'


def cols(a, b):
    return f'<div class="cols"><div>{a}</div><div>{b}</div></div>'


def h3(t):
    return f"<h3>{t}</h3>"


# ----------------------------------------------------------------------------- figures

def fig_map():
    p = [container(8, 8, 316, 470, "Frappe Health", "health"), container(396, 8, 316, 470, "ERPNext (Stock, Selling)", "stock"),
         box(26, 44, 150, 56, "Patient", "a person receiving care", "health"),
         box(26, 128, 150, 56, "Medication", "a medicine as a clinical product", "health"),
         box(26, 212, 150, 56, "Clinical Procedure Template", "a care and the medicines it uses", "health"),
         box(26, 296, 150, 56, "Clinical Procedure", "one care given to one patient", "health"),
         box(26, 380, 150, 56, "Inpatient Medication Entry", "medicines given to admitted patients", "health"),
         box(430, 44, 150, 56, "Customer", "Selling", "app"),
         box(430, 128, 150, 56, "Item", "every medicine and every service", "stock"),
         box(430, 212, 150, 56, "Batch", "lot number + expiry date", "stock"),
         box(430, 296, 150, 56, "Stock Entry", "Material Receipt / Issue", "stock"),
         box(430, 380, 150, 56, "Stock Ledger · Bin", "every movement, stock per warehouse", "stock"),
         arrow(176, 72, 430, 72, "automatic Customer", lx=303, ly=63),
         arrow(176, 156, 430, 156, "Linked Items → Item + price", lx=303, ly=147),
         arrow(176, 240, 430, 174, "service Item (no stock)", lx=300, ly=212),
         arrow(176, 324, 430, 324, "Complete and Consume\nMaterial Issue", lx=303, ly=311),
         arrow(176, 408, 430, 336, "Material Issue per patient", lx=270, ly=397),
         arrow(505, 184, 505, 212), arrow(505, 352, 505, 380, "posts"),
         tspans(["A Clinical Procedure uses the Items listed on it, from one warehouse."], 360, 468, size=8.6, fill="#6B726E")]
    return diagram(720, 486, p)


def fig_status():
    y = 60
    p = [box(14, y, 110, 56, "Draft", "saved, nothing yet", "app"), box(160, y, 110, 56, "Pending", "submitted", "health"),
         box(306, y, 110, 56, "In Progress", "started", "health"), box(452, y, 110, 56, "Completed", "stock has left", "stock"),
         box(598, y, 108, 56, "Cancelled", "docstatus 2", "warn"),
         arrow(124, y + 28, 160, y + 28, "Submit", ly=y + 17), arrow(270, y + 28, 306, y + 28, "Start", ly=y + 17),
         arrow(416, y + 28, 452, y + 28, "Complete", ly=y + 17), arrow(562, y + 28, 598, y + 28, "Cancel", ly=y + 17, dash=True),
         tspans(["Start: checks the quantity in the warehouse. Short? ERPNext offers to record a Material Receipt for the shortage."], 360, 150, size=9, fill="#3A403D"),
         tspans(["Complete and Consume: creates and submits the Stock Entry (Material Issue). This is the only moment stock moves."], 360, 166, size=9, fill="#3A403D")]
    return diagram(720, 186, p)


def seq_stock_in():
    lanes = [USER, SE, IB, LB, MR]
    steps = [
        ("m", "U", "SE", "New Stock Entry · type Material Receipt · target warehouse · item, quantity, rate, batch"),
        ("m", "SE", "IB", "Checks: item is a stock item · batch belongs to the item · expiry date present for expiry items"),
        ("m", "U", "SE", "Submit"),
        ("m", "SE", "LB", "Stock Ledger Entry +qty · Bin.actual_qty +qty · Batch.batch_qty +qty"),
        ("n", "LB", "Valuation: the item's moving-average rate takes in the incoming rate. A zero rate needs “Allow zero valuation rate” on the row."),
        ("s", "later, on its own"),
        ("m", "LB", "MR", "Bin falls to the item's reorder level (daily check; Stock Settings › Raise Material Request when stock reaches re-order level)"),
        ("m", "MR", "U", "A Material Request (Purchase) appears to approve, order and receive", "ret"),
    ]
    return sequence(lanes, steps)


def seq_stock_out():
    lanes = [USER, SE, IB, LB]
    steps = [
        ("m", "U", "SE", "New Stock Entry · type Material Issue · source warehouse · item, quantity (batch left empty)"),
        ("m", "U", "SE", "Submit"),
        ("m", "SE", "IB", "Choose batches: Stock Settings › Pick Serial / Batch Based On = Expiry → earliest expiry first, expired batches skipped"),
        ("f", "start", "Not enough valid quantity"),
        ("n", "IB", "Error: “Available qty 10 is less than Required qty 15 in the warehouse”. Expired stock does not count. Nothing is posted.", "warn"),
        ("f", "end"),
        ("m", "SE", "LB", "Stock Ledger Entry −qty per batch · Bin and Batch quantities go down"),
        ("n", "LB", "The batches used are listed in a Serial and Batch Bundle attached to the Stock Entry row."),
    ]
    return sequence(lanes, steps)


def seq_medication():
    lanes = [lane("A", "Administrator", "Healthcare Administrator", "app"), lane("M", "Medication", "Frappe Health", "health"),
             lane("I", "Item", "ERPNext Stock", "stock"), lane("P", "Item Price", "ERPNext Selling", "app")]
    steps = [
        ("m", "A", "M", "New Medication: generic name, class, dosage form, strength + unit, and a Linked Items table (item code, item group, stock UOM, billable, rate)"),
        ("m", "M", "I", "On save, one Item per linked row: stock item = yes, sales item = yes, item group and stock UOM from the row"),
        ("n", "I", "The Item is created disabled unless the row is billable and the Medication is enabled. Batch tracking, expiry and reorder level are not set by Health."),
        ("m", "M", "P", "Item Price created on the default selling price list (rate from the row)"),
        ("m", "M", "M", "The row's Item field is filled with the new Item"),
        ("s", "later changes"),
        ("m", "A", "M", "Edit name, group, rate, disabled; remove a row"),
        ("m", "M", "I", "Item and price updated. A removed row disables its Item (never deletes it)."),
    ]
    return sequence(lanes, steps)


def seq_patient():
    lanes = [lane("A", "Registration", "nurse · physician", "app"), lane("P", "Patient", "Frappe Health", "health"),
             lane("C", "Customer", "ERPNext Selling", "app")]
    steps = [
        ("m", "A", "P", "New Patient: first name, sex (required), date of birth, phone, blood group, allergies"),
        ("m", "P", "C", "Healthcare Settings › Link Customer to Patient = yes: a Customer is created with the patient's name"),
        ("m", "P", "P", "Patient.customer is filled; the patient id is the patient name (or a naming series)"),
        ("n", ("P", "C"), "The Customer is what invoices are made to. A clinic that never bills can ignore it."),
    ]
    return sequence(lanes, steps)


def seq_template():
    lanes = [lane("A", "Administrator", "Physician · Healthcare Admin", "app"), lane("T", "Procedure Template", "Frappe Health", "health"),
             lane("I", "Item", "ERPNext Stock", "stock")]
    steps = [
        ("m", "A", "T", "New Clinical Procedure Template: name, item group, description, Consume Stock = yes, and a table of Items + quantities"),
        ("m", "T", "I", "A service Item is created with the template's name: not a stock item, sales item, price from the template's rate"),
        ("n", "T", "The table is a list of defaults. Each procedure copies it and can change the quantities."),
    ]
    return sequence(lanes, steps)


def seq_complete():
    lanes = [lane("N", "Nurse", "Nursing User + Stock User", "app"), lane("C", "Clinical Procedure", "Frappe Health", "health"),
             lane("S", "Stock Entry", "ERPNext Stock", "stock"), lane("L", "Batch · Ledger · Bin", "ERPNext Stock", "stock")]
    steps = [
        ("m", "N", "C", "New Clinical Procedure: patient, template, warehouse, date. The template's items are copied in (Consume Stock = yes)."),
        ("m", "N", "C", "Submit → status Pending"),
        ("m", "N", "C", "Start → checks the warehouse quantity of every item → status In Progress"),
        ("m", "N", "C", "Complete and Consume"),
        ("m", "C", "S", "New Stock Entry · Material Issue · from the procedure's warehouse · one row per item with the procedure's quantity · expense account from Healthcare Settings · submit"),
        ("m", "S", "L", "Batches chosen (earliest expiry first, expired skipped) · ledger −qty · Bin and Batch down"),
        ("m", "C", "C", "Status Completed · end time · consumed items text"),
        ("m", "C", "N", "Stock Entry number shown", "ret"),
        ("n", ("C", "S"), "The procedure does not keep the Stock Entry number. Nothing in the standard records ties the two together afterwards."),
    ]
    return sequence(lanes, steps)


def seq_cancel_native():
    lanes = [lane("P", "Physician", "only role allowed to cancel", "app"), lane("C", "Clinical Procedure", "Frappe Health", "health"),
             lane("S", "Stock Entry", "ERPNext Stock", "stock"), lane("L", "Ledger · Bin", "ERPNext Stock", "stock")]
    steps = [
        ("s", "What happens with the standard Cancel button"),
        ("m", "P", "C", "Cancel the completed procedure"),
        ("m", "C", "C", "docstatus 2 (cancelled). The status text stays “Completed”."),
        ("n", ("S", "L"), "The Stock Entry stays submitted. The ledger is not reversed. The medicines stay counted as used.", "warn"),
        ("s", "Correct way, to put the medicines back"),
        ("m", "P", "S", "1 · Cancel the Stock Entry first"),
        ("m", "S", "L", "Ledger reversed: the quantities go back into the same batches (original rows kept, marked cancelled)"),
        ("m", "P", "C", "2 · Then cancel the Clinical Procedure"),
        ("n", ("C", "S"), "Cancelling the procedure first is allowed, but the Stock Entry must then be found by hand (no link). Doing it in this order needs the link from the previous page."),
    ]
    return sequence(lanes, steps)


def seq_inpatient():
    lanes = [lane("N", "Nurse", "Nursing User", "app"), lane("O", "Medication Order", "Frappe Health", "health"),
             lane("E", "Inpatient Med. Entry", "Frappe Health", "health"), lane("S", "Stock Entry", "ERPNext Stock", "stock")]
    steps = [
        ("m", "N", "O", "Inpatient Medication Order: patient, drug (Item), dosage, date and time"),
        ("m", "N", "E", "Inpatient Medication Entry: pull the pending orders for a day and a warehouse"),
        ("m", "E", "E", "Checks stock for all rows. Shortage → “Insufficient Stock” table, nothing posted."),
        ("m", "E", "S", "Submit → one Stock Entry (Material Issue) with a row per order; each row carries the Patient"),
        ("n", ("E", "S"), "Cancelling the entry cancels its Stock Entries, so stock does come back here. The Stock Entry carries the link."),
    ]
    return sequence(lanes, steps)


# ----------------------------------------------------------------------------- document

def build():
    toc = [
        ("The two modules at a glance", "Who owns what, and where they touch"),
        ("ERPNext Stock on its own", "Stock in, stock out, reorder"),
        ("Frappe Health on its own", "Patient, medication, procedure"),
        ("Connection 1 · Medication and Item", "One medicine, two records"),
        ("Connections 2 and 3 · Patient, Customer, Template", "Automatic companions"),
        ("Connection 4 · Procedure to Stock Entry", "How stock leaves for a patient"),
        ("What ERPNext checks when stock leaves", "Experiments on the running site"),
        ("Connection 5 · Cancelling a procedure", "Standard behaviour and the correct order"),
        ("Connection 6 · Inpatient medication", "The second route from Health to Stock"),
        ("Every way stock comes in and goes out", "With the one we recommend"),
        ("Permissions in the modules", "Standard roles, tested one by one"),
        ("Module setup checklist", "Settings the two modules rely on"),
        ("Gaps in the standard flow", "What to decide or add"),
    ]
    cover = (f'<div class="cover"><img src="data:image/svg+xml;base64,{common.LOGO}"><h1>Health <em>×</em> Stock<br>How the modules work together</h1>'
             '<p>Frappe Health and ERPNext Stock, explained as they behave on their own: what each module owns, how stock comes in and leaves, and exactly where care and stock meet.</p>'
             '<div class="meta">Frappe, ERPNext and Frappe Health version 16 · every behaviour in this document was tried on a running site</div></div>')
    toc_html = ('<div class="toc"><div class="kicker">Contents</div><h1>What this document covers</h1>'
                '<p class="lead">No custom screens, no extra code: only the two standard modules. Sequence diagrams show which record causes which. Where something surprised us, it is stated as a finding, with the test that showed it.</p><ol>'
                + "".join(f"<li>{a}<span>{b}</span></li>" for a, b in toc) + "</ol>"
                '<div class="legend" style="margin-top:8mm"><b style="color:#1B1F1D">Colours:</b>'
                '<span><i style="background:#EDE9DD;border-color:#B9B3A0"></i>person / other module</span>'
                '<span><i style="background:#F6E6C8;border-color:#B7791F"></i>ERPNext Stock</span>'
                '<span><i style="background:#DCE8F3;border-color:#2B5F8A"></i>Frappe Health</span>'
                '<span><i style="background:#FBE9E4;border-color:#B4412D"></i>warning</span></div></div>')
    S = [cover, toc_html]

    S.append(page("Overview", "The two modules at a glance",
        "<b>ERPNext Stock</b> knows what is on the shelf. <b>Frappe Health</b> knows who received care. They meet at a small number of places, and almost all of them are the moment a procedure uses medicines.",
        fig(fig_map())
        + table(["Connection", "Triggered by", "What is created"], [
            ["Medication → Item", "Saving a Medication with linked items", "An Item per linked row (disabled unless billable) and its Item Price"],
            ["Patient → Customer", "Saving a Patient", "A Customer with the patient's name"],
            ["Template → Item", "Saving a procedure template", "A service Item (no stock) and its price"],
            ["Procedure → Stock Entry", "Complete and Consume", "A Material Issue from the procedure's warehouse"],
            ["Inpatient Medication Entry → Stock Entry", "Submit", "A Material Issue with a row per patient order"],
            ["Medication Request / prescription", "Never", "Nothing in stock: prescriptions only ask; billing is separate"]])))

    S.append(page("Stock module", "ERPNext Stock on its own",
        "Every quantity lives in the Stock Ledger. A Stock Entry is the document that adds to it or takes from it. The Bin is the running total per item and warehouse; the Batch holds the same per lot.",
        fig(seq_stock_in()) + cols(
            h3("Stock in: key facts") + ul(["Stock Entry type <b>Material Receipt</b> adds to a warehouse with no supplier. Purchases use Purchase Receipt (same ledger).",
                "Items with expiry need a Batch with an expiry date before they can be received.",
                "The batch quantity and the Bin always equal the sum of the ledger."]),
            h3("Reorder") + ul(["Each Item can have a reorder level per warehouse.",
                "With “Raise Material Request when stock reaches re-order level” on, a daily job raises a request when the Bin falls to that level.",
                "A Material Request never changes stock by itself."]))))

    S.append(page("Stock module", "Stock out in ERPNext Stock",
        "Stock leaves through a Stock Entry of type <b>Material Issue</b>. Batches are chosen by ERPNext, earliest expiry first, and expired lots are never used.",
        fig(seq_stock_out()) + cols(
            h3("Settings that make this work") + ul(["Stock Settings › Pick Serial / Batch Based On = <b>Expiry</b>.",
                "Stock Settings › Use Serial / Batch fields = on (batch chosen on the row).",
                "Item › Has Batch No = yes, Has Expiry Date = yes."]),
            h3("What a user sees") + ul(["Material Issue with a source warehouse and the quantity.",
                "On submit: ledger rows per batch, the batches shown in the bundle.",
                "Too little valid stock: a clear error, nothing is posted."]))))

    S.append(page("Health module", "Frappe Health on its own",
        "Care is recorded on people and procedures. Only one document in the whole care flow, the Clinical Procedure, is able to move stock.",
        fig(fig_status())
        + table(["Record", "Holds", "Moves stock?"], [
            ["Patient", "Name, sex, birth date, phone, blood group, allergies, linked Customer", "no"],
            ["Medication", "Generic name, class, dosage form, strength, linked Items", "no"],
            ["Clinical Procedure Template", "Name, description, items + quantities (defaults)", "no"],
            ["Clinical Procedure", "Patient, template, warehouse, date, items, status", "<b>yes, when completed</b>"],
            ["Inpatient Medication Order / Entry", "Drug orders for admitted patients", "yes, when the entry is submitted"],
            ["Medication Request, Patient Encounter", "Prescriptions and visits", "no"]])
        + '<div class="callout"><b>Roles.</b> Patients can be created by Nursing User, Physician and Laboratory User. Medications by Healthcare Administrator. Procedures by Nursing User and Physician. Details in “Permissions in the modules”.</div>'))

    S.append(page("Connection 1", "Medication and Item",
        "A Medication is the clinical product; an Item is the stock product. Health creates the Item from the Medication's linked-items table.",
        fig(seq_medication()) + cols(
            h3("Findings (tested)") + ul(["The Item is created as a stock item and a sales item, disabled when the row is not billable.",
                "A Medication with no price list set needs the default selling price list, or it cannot be saved.",
                "The batch, expiry and reorder settings of an Item are not touched by Health."]),
            h3("What to do about it") + ul(["Give the Item its batch, expiry and reorder settings in the Stock module (Item defaults can do this for every new Item).",
                "Enable the Item when the medicine is ready to use.",
                "Keep one Item per Medication: the Medication refuses an Item already linked elsewhere."]))))

    S.append(page("Connections 2 and 3", "Patient and Customer, Template and Item",
        "Two companions are created automatically. They matter for billing, not for stock.",
        fig(seq_patient()) + fig(seq_template())))

    S.append(page("Connection 4", "Procedure to Stock Entry",
        "This is the heart of the integration. A procedure lists the Items it uses. When it is completed, ERPNext issues them from the procedure's warehouse.",
        fig(seq_complete()) + cols(
            h3("Rules (tested)") + ul(["Warehouse: the one chosen on the procedure. It is filled from the Healthcare Service Unit's warehouse when a service unit is picked; otherwise the nurse chooses it (Stock Settings has no default warehouse in version 16).",
                "Quantity is the procedure's own, not the template's: it can be changed per patient.",
                "Start checks the total quantity in the warehouse; if short it offers a Material Receipt for the shortage."]),
            h3("Remember") + ul(["Standard cancel does not return stock (next pages).",
                "A procedure with Consume Stock = no never touches stock.",
                "The Stock Entry has no patient on it for procedures."]))))

    S.append(page("Experiments", "What ERPNext checks when stock leaves",
        "Run on a site with Pick Serial / Batch Based On = Expiry. Item with two batches, procedures completed through the standard buttons.",
        table(["Test", "Setup", "Result"], [
            ["Earliest expiry first", "Batch A expires in 100 days, batch B in 300 days; B was received first. Procedure uses 4.", "<b>A</b> was used (the one expiring first)"],
            ["Expired batch is skipped", "Batch A made expired (6 left), B valid (10). Procedure uses 8.", "All 8 came from <b>B</b>; A untouched"],
            ["Not enough valid stock", "B valid 10, A expired 10 (20 in the warehouse). Procedure uses 15.", "Start says OK (it counts expired). <b>Complete is refused</b>: “Available qty 10 is less than Required Qty 15”"],
            ["More than the whole warehouse", "Procedure uses 25 with 20 in the warehouse.", "Start answers “insufficient stock” and offers a Material Receipt"],
            ["Item with no batches", "Plain stock item, 50 received. Procedure uses 2.", "Works; no batch involved"],
            ["Receive into an expired batch", "Material Receipt with an already expired batch.", "Refused: “The batch … has already expired”"]])
        + '<div class="callout"><b>Reading the results.</b> ERPNext protects expiry at the moment of posting: expired lots are never issued and valid lots are used oldest first. The Start check is only a first, rougher warning because it counts every unit in the warehouse.</div>'))

    S.append(page("Connection 5", "Cancelling a procedure",
        "A procedure recorded for the wrong patient has to be undone. The standard Cancel does only half the job.",
        fig(seq_cancel_native()) + cols(
            h3("Tested") + ul(["Cancelling a completed procedure (as Physician): the procedure becomes docstatus 2; its Stock Entry stays submitted; the warehouse quantity does not change.",
                "Nursing User cannot cancel procedures at all (only Physician can)."]),
            h3("Decision") + ul(["Either cancel the Stock Entry and the procedure together, in that order, every time.",
                "Or add a link from the procedure to its Stock Entry, so that one action cancels both."]))))

    S.append(page("Connection 6", "Inpatient medication",
        "The second route from Health to Stock is for admitted patients. It works per order, not per procedure.",
        fig(seq_inpatient()) + table(["", "Clinical Procedure", "Inpatient Medication Entry"], [
            ["Moves stock when", "Complete and Consume", "Submit"],
            ["Patient on the Stock Entry", "no", "yes, on each row"],
            ["Link to its Stock Entry", "none", "Stock Entry › Inpatient Medication Entry"],
            ["Cancelling returns stock", "no (standard)", "yes"],
            ["Used for", "Care at the clinic: dressings, injections", "Wards: scheduled doses for admitted patients"]])))

    S.append(page("All routes", "Every way stock comes in and goes out",
        "Stock only moves through a Stock Entry (or a document that creates one). These are all the routes, and the one we use for each situation.",
        h3("Stock in") + table(["Route", "Record", "When", "Recommended"], [
            ["Delivery with no purchase order", "Stock Entry · Material Receipt", "Donations, first stock, simple deliveries", "<span class='yes'>yes, default</span>"],
            ["Delivery against a purchase order", "Purchase Receipt", "When purchasing is run in ERPNext", "later"],
            ["Move between warehouses", "Stock Entry · Material Transfer", "Store to ward", "if needed"],
            ["Correct a count", "Stock Reconciliation", "Annual or monthly count", "yes, for counts"],
            ["Return of a cancelled use", "Cancel the Stock Entry", "Wrong patient", "see Connection 5"]])
        + h3("Stock out") + table(["Route", "Record", "When", "Recommended"], [
            ["Care given to a patient", "Clinical Procedure → Material Issue", "Dressing, injection, any care", "<span class='yes'>yes, default</span>"],
            ["Admitted patient doses", "Inpatient Medication Entry → Material Issue", "Wards", "if wards exist"],
            ["Damaged, lost, thrown away", "Stock Entry · Material Issue", "Not tied to a patient", "yes"],
            ["Expired stock", "Stock Entry · Material Issue (expired batch)", "Clearing expired lots", "yes"],
            ["Sold or dispensed with an invoice", "Sales Invoice with Update Stock, or Delivery Note", "A pharmacy that bills each sale", "if billing is needed"],
            ["Count surplus or shortage", "Stock Reconciliation", "After a count", "yes, for counts"]])))

    S.append(page("Security", "Permissions in the modules",
        "Standard roles, tested by creating users with one role each and trying each step. Cell = what that role can do on that record.",
        table(["Record", "Nursing User", "Physician", "Healthcare Administrator", "Stock User", "Item Manager"], [
            ["Patient", "read, write, create", "read, write, create", "—", "<span class='no'>no access</span>", "—"],
            ["Medication", "<span class='no'>no access</span>", "<span class='no'>cannot create</span>", "read, write, create", "—", "—"],
            ["Procedure Template", "read", "read, write", "read, write, create", "—", "—"],
            ["Clinical Procedure", "read, write, create, submit", "also cancel", "—", "<span class='no'>no access</span>", "—"],
            ["Item", "read", "read", "—", "read", "read, write, create"],
            ["Stock Entry", "<span class='no'>none</span>", "—", "—", "read, write, create, submit, cancel", "—"],
            ["Material Request", "—", "—", "—", "read, write, create, submit", "—"]], "tight")
        + cols(h3("Tested findings") + ul([
            "A <b>Nursing User alone cannot complete</b> a procedure that uses stock: creating the Stock Entry is refused. Adding the role <b>Stock User</b> fixes it; nothing else is needed.",
            "A Nursing User can create, submit and start a procedure, and read items and patients.",
            "A Stock User can receive stock and raise requests but cannot read patients or procedures.",
            "Only Physician can cancel a procedure."]),
            h3("A workable role set") + ul([
                "<b>Pharmacist:</b> Stock User + Item Manager (create medicines and batches).",
                "<b>Nurse:</b> Nursing User + Stock User (records and completes procedures).",
                "<b>Doctor:</b> Physician + Stock User if they complete procedures.",
                "<b>Administrator:</b> Healthcare Administrator (Medications, templates) + Stock Manager.",
                "<b>Site owner:</b> System Manager."]))))

    S.append(page("Setup", "Module setup checklist",
        "What has to exist in the two modules before the flows above work. Nothing here needs custom code.",
        table(["Where", "Setting", "Why"], [
            ["Company", "Created by the setup wizard; if perpetual inventory is on, a Default Inventory Account", "Stock Entries post to accounts"],
            ["Warehouse", "One warehouse for the pharmacy (e.g. “Pharmacy”)", "Source of every issue, target of every receipt"],
            ["Stock Settings", "Pick Serial / Batch Based On = Expiry · Use Serial / Batch fields = on · Raise Material Request when stock reaches re-order level = on", "Earliest expiry first, expired skipped, reorder"],
            ["Healthcare Service Unit", "Set its warehouse to the pharmacy warehouse (or choose the warehouse on each procedure)", "Procedure warehouse default"],
            ["Item defaults", "Maintain stock, Has Batch No, Has Expiry Date, a batch series", "Items made from Medications become batch and expiry items"],
            ["Item Groups", "A “Medicine” group with categories (analgesic, antibiotic…)", "Lists, reports and medication classes"],
            ["Healthcare Settings", "Link Customer to Patient · patient naming · income / expense accounts", "Patient companions, Stock Entry expense account"],
            ["Price List", "A default selling price list", "Medications and templates need a price"],
            ["Roles", "See the role set above", "Who may do what"]])
        + '<div class="callout warn"><b>Order matters.</b> Create the Item defaults and Stock Settings first, then the Medications. Items already created keep their old settings.</div>'))

    S.append(page("Decisions", "Gaps in the standard flow",
        "These are properties of the standard modules, found by testing. Each one needs a decision, or a small addition.",
        table(["Gap in the standard modules", "Consequence", "Proposed answer"], [
            ["The procedure does not keep its Stock Entry number", "No way to see which stock a procedure used, or to cancel the right entry", "Add a link field on the Stock Entry to the Clinical Procedure, filled when completing"],
            ["Standard Cancel does not return stock", "A mistake leaves the medicines counted as used", "Cancel the Stock Entry with the procedure, in that order, and keep a reason"],
            ["Items from Medication are disabled and not batch / expiry items", "Medicines cannot be used until fixed by hand", "Item defaults for batch and expiry; enable the Item after creating the Medication"],
            ["Start counts expired stock", "A procedure can start with no valid stock and fail at Complete", "Accept: the refusal at Complete protects stock; show valid stock to the nurse"],
            ["A Stock Entry has no reason or recipient", "“Why did stock leave?” is not recorded", "Add two fields on the Stock Entry: reason and recipient"],
            ["Nursing User cannot complete a stock-consuming procedure alone", "Nurses are blocked at the last step", "Give nurses Stock User as well"],
            ["Nurses cannot cancel; only Physician", "A wrong entry needs a doctor", "Decide who may cancel; add the role or a Healthcare Administrator step"],
            ["Prescriptions never move stock", "Dispensing a prescription is not a stock movement", "Dispense through a procedure, or bill with a Sales Invoice that updates stock"]])
        + '<div class="callout"><b>How we answer them.</b> A link field, a reason field and a recipient field are added to the Stock Entry; Item defaults and Stock Settings are configured; the roles above are used. Everything else is standard.</div>'))

    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Health × Stock: how the modules work together</title>'
            f'<style>{common.CSS.replace("PharmaStock · stock and care flows", "Health × Stock · how the modules work together")}</style></head><body>{"".join(S)}</body></html>')
    (HERE / "modules.html").write_text(html)
    out = ROOT / "docs/PharmaStock-Modules.pdf"
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", f"file://{HERE / 'modules.html'}"], check=True, capture_output=True)
    print("wrote", out)


if __name__ == "__main__":
    build()
