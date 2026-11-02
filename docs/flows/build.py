"""Builds docs/PharmaStock-Flows.pdf: the stock and care flows of PharmaStock, with sequence diagrams.

    python3 docs/flows/build.py        # writes docs/flows/flows.html and docs/PharmaStock-Flows.pdf (needs Google Chrome)
"""
import base64
import pathlib
import subprocess

from seq import box, arrow, container, diagram, sequence, tspans

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
FONTS = ROOT / "frontend/node_modules"


def font(path):
    return base64.b64encode((FONTS / path).read_bytes()).decode()


LOGO = base64.b64encode((ROOT / "docs/logo-mark.svg").read_bytes()).decode()

APP = ("APP", "App", "PWA at /pharmacy", "app")
API = ("API", "PharmaStock API", "api.py · health.py", "api")
STK = ("STK", "ERPNext Stock", "Item · Batch · Stock Entry", "stock")
HLT = ("HLT", "Frappe Health", "Patient · Procedure", "health")


def ul(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def table(head, rows, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def flow(num, title, lead, svg, rules, result, extra=""):
    return (f'<section class="flow"><div class="kicker">Flow {num}</div><h2>{title}</h2><p class="lead">{lead}</p>'
            f'<div class="fig">{svg}</div><div class="cols"><div><h3>Rules and errors</h3>{ul(rules)}</div>'
            f'<div><h3>What exists afterwards</h3>{ul(result)}</div></div>{extra}</section>')


# ----------------------------------------------------------------------------- figures

def fig_architecture():
    p = [container(8, 8, 704, 118, "1 · The user's side", "app"),
         box(30, 44, 150, 62, "Pharmacist / nurse", "Staff or Admin role", "app"),
         box(210, 44, 200, 62, "PharmaStock app (PWA)", "Vue 3 · works offline for stock · /pharmacy", "app"),
         box(440, 44, 250, 62, "Session + CSRF token", "login at /login, cookie, role checked on every call", "app"),
         arrow(180, 75, 210, 75), arrow(410, 75, 440, 75, both=True),
         container(8, 150, 704, 100, "2 · Our code (one Python process, inside the Frappe site)", "api"),
         box(30, 180, 200, 56, "api.py", "medicines, stock in/out, requests, reports", "api"),
         box(260, 180, 200, 56, "health.py", "patients, procedure types, procedures", "api"),
         box(490, 180, 200, 56, "Role check, then write", "elevated write, owner kept", "api"),
         arrow(360, 106, 360, 150, "HTTPS · whitelisted method calls"),
         container(8, 274, 340, 122, "3 · ERPNext Stock", "stock"),
         box(26, 306, 150, 70, "Item · Batch", "one Item per medicine; one Batch per lot with its expiry", "stock"),
         box(190, 306, 144, 70, "Stock Entry · Ledger", "every in and out; Bin = stock per warehouse", "stock"),
         container(372, 274, 340, 122, "4 · Frappe Health", "health"),
         box(390, 306, 150, 70, "Medication", "the same medicine as a clinical product", "health"),
         box(554, 306, 140, 70, "Patient · Procedure", "templates and procedures per patient", "health"),
         arrow(150, 236, 150, 274, "", both=True), arrow(540, 236, 540, 274, "", both=True),
         arrow(334, 340, 372, 340, "link", dash=True, both=True),
         box(150, 412, 420, 38, "Database (MariaDB) · scheduler · notifications", "", "ink")]
    return diagram(720, 462, p)


def fig_links():
    p = [container(8, 8, 346, 394, "ERPNext Stock", "stock"), container(366, 8, 346, 394, "Frappe Health", "health"),
         box(30, 44, 150, 54, "Item", "the medicine (stock item)", "stock"),
         box(30, 140, 150, 54, "Batch", "lot number + expiry date", "stock"),
         box(30, 236, 150, 54, "Stock Entry", "Receipt (in) · Issue (out)", "stock"),
         box(30, 332, 150, 46, "Stock Ledger Entry", "", "stock"),
         box(200, 332, 140, 46, "Warehouse “Pharmacy”", "", "stock"),
         box(392, 44, 150, 54, "Medication", "same name as the Item", "health"),
         box(556, 44, 140, 54, "Medication Linked Item", "points to the Item", "health"),
         box(392, 140, 150, 54, "Patient", "+ ERPNext Customer", "health"),
         box(556, 140, 140, 54, "Procedure Template", "medicines + quantities", "health"),
         box(392, 236, 150, 54, "Clinical Procedure", "patient · template · status", "health"),
         box(556, 236, 140, 54, "Procedure Item", "medicine + qty used", "health"),
         arrow(180, 71, 392, 71, "Item.custom_medication  ↔  Medication", lx=286, ly=62, both=True),
         arrow(542, 71, 556, 71),
         arrow(105, 98, 105, 140, "1 Item → many Batches", lx=105, ly=124),
         arrow(105, 194, 105, 236, "lot used on each line", lx=105, ly=220),
         arrow(105, 290, 105, 332, "posts", lx=105, ly=316),
         arrow(180, 355, 200, 355),
         arrow(467, 194, 467, 236, "procedure for a patient", lx=467, ly=220),
         arrow(626, 194, 626, 236, "copied as defaults", lx=626, ly=220, dash=True),
         arrow(556, 263, 542, 263),
         arrow(392, 263, 180, 263, "Stock Entry.custom_clinical_procedure", lx=286, ly=254, dash=True),
         tspans(["Procedure Item.item_code → Item", "(the medicine used)"], 626, 312, size=8.6, fill="#6B726E")]
    return diagram(720, 410, p)


def fig_permissions():
    lanes = [APP, API, ("FW", "Frappe", "users · roles · session", "ink"), ("DOC", "ERPNext + Health", "documents", "stock")]
    steps = [
        ("m", "APP", "API", "Any call, with the session cookie and CSRF token"),
        ("m", "API", "FW", "Who is this user, and which roles?"),
        ("n", "API", "Guest or no pharmacy role → 403 “You do not have access to the pharmacy”. Admin-only action with only the Staff role → 403.", "warn"),
        ("f", "start", "Writes only, after the check passed"),
        ("m", "API", "FW", "set_user(Administrator) for this call only; real user and roles are remembered"),
        ("m", "API", "DOC", "Create / submit documents. owner = the real user"),
        ("m", "API", "FW", "set_user(real user) again, always, even after an error"),
        ("f", "end"),
    ]
    return sequence(lanes, steps)


# sequence figures ---------------------------------------------------------------------------------

def fig_create_medicine():
    steps = [
        ("m", "APP", "API", "POST save_medicine(name, category, unit, form, strength, location, minimum, optional first stock)"),
        ("n", "API", "Role check: Pharmacy Staff or Admin. Then the write runs with full rights; the real user stays the owner."),
        ("n", "API", "Validate: name given · category is a Medicine group · name not already used (an archived one with that name is brought back)."),
        ("m", "API", "STK", "Insert Item: stock item, batches + expiry on, series BATCH-.#####, reorder level in warehouse Pharmacy = minimum, dosage form, strength, location"),
        ("m", "STK", "API", "Item code = medicine name", "ret"),
        ("m", "API", "HLT", "sync_medication: insert Medication (generic name, class = category, dosage form, strength “500mg” → 500 + mg, orderable)"),
        ("m", "API", "HLT", "Insert Medication Linked Item (item_code and item = the Item)"),
        ("m", "API", "STK", "Write Item.custom_medication = the Medication name"),
        ("f", "start", "Only if a first quantity was entered"),
        ("m", "API", "STK", "Receive stock: Batch + Stock Entry · Material Receipt (Flow 2)"),
        ("f", "end"),
        ("m", "API", "APP", "{ code } → the app opens the medicine page", "ret"),
    ]
    return sequence([APP, API, STK, HLT], steps)


def fig_add_stock():
    steps = [
        ("m", "APP", "API", "POST add_stock(medicine, qty, price, date, expiry, lot, client_id)"),
        ("n", "API", "Role check. A client_id already recorded → return the first result, record nothing twice (safe retry)."),
        ("n", "API", "Validate: qty > 0 · expiry given and after the received date · medicine exists."),
        ("n", "API", "Lot number given and it already exists → it must be the same medicine with the same expiry. Otherwise a new Batch is made."),
        ("m", "API", "STK", "Insert Batch (item, expiry date, lot number)"),
        ("m", "API", "STK", "Insert + submit Stock Entry · Material Receipt → warehouse Pharmacy, qty, rate, batch. Zero price allowed."),
        ("n", "STK", "Stock Ledger Entry +qty · Bin (stock per warehouse) · Batch quantity all go up.", "stock"),
        ("n", "STK", "Nightly: stock ≤ reorder level → ERPNext creates a Material Request automatically → bell alert to administrators.", "stock"),
        ("m", "API", "APP", "{ stock_entry, batch }", "ret"),
    ]
    return sequence([APP, API, STK], steps)


def fig_patient():
    steps = [
        ("m", "APP", "API", "POST save_patient(first_name, last_name, sex, dob, mobile, blood_group, allergies)"),
        ("n", "API", "Role check. Validate: first name given · sex is Female or Male · birth date not in the future · blood group from the list."),
        ("m", "API", "HLT", "Insert Patient (owner = the real user)"),
        ("n", "HLT", "Frappe Health names it after the patient name (adds “- 2” if taken) and creates the linked ERPNext Customer.", "health"),
        ("m", "HLT", "API", "Patient id", "ret"),
        ("m", "API", "APP", "{ name, patient_name } → the app opens the patient file", "ret"),
    ]
    return sequence([APP, API, HLT], steps)


def fig_template():
    steps = [
        ("m", "APP", "API", "POST save_procedure_template(template, description, items = [ {medicine, qty} ])"),
        ("n", "API", "Role check. Validate: name given and not used before · each medicine active · each quantity > 0."),
        ("m", "API", "HLT", "Insert Clinical Procedure Template: item group “Clinical Procedures”, not billable, consume stock = yes when it lists medicines, items = medicines + quantities"),
        ("m", "HLT", "STK", "Frappe Health creates a service Item for the template (not a stock item, price 0)"),
        ("m", "API", "APP", "{ name }", "ret"),
        ("n", ("API", "HLT"), "The quantities are defaults. They can be changed for each patient when the procedure is recorded."),
    ]
    return sequence([APP, API, HLT, STK], steps)


def fig_record():
    steps = [
        ("m", "APP", "API", "POST record_procedure(patient, template, items, date, notes, complete, client_id)"),
        ("n", "API", "Role check. client_id already recorded → return the first result. Validate: patient and template exist · date not in the future · items default to the template's."),
        ("m", "API", "HLT", "Insert + submit Clinical Procedure (patient, template, warehouse Pharmacy, items, client_id) → status Pending"),
        ("f", "start", "complete = 1 (“Done now”), or later “Mark as done”"),
        ("n", "API", "Allocate batches per medicine: valid (not expired) batches only, earliest expiry first. Not enough → the whole request fails and nothing is saved."),
        ("m", "API", "STK", "Insert + submit Stock Entry · Material Issue from Pharmacy, one line per batch. Reason “Used in a procedure”, recipient = patient, link = the procedure"),
        ("n", "STK", "Stock Ledger Entry −qty per batch · Bin and Batch quantities go down.", "stock"),
        ("m", "API", "HLT", "Procedure status = Completed, end time, consumption details"),
        ("f", "end"),
        ("m", "API", "APP", "{ name, stock_entry, status }", "ret"),
    ]
    return sequence([APP, API, STK, HLT], steps)


def fig_cancel():
    steps = [
        ("m", "APP", "API", "POST cancel_procedure(name, reason)"),
        ("n", "API", "Role check (staff or admin). Already cancelled → refused. Completed without a reason → refused. Planned: reason optional."),
        ("f", "start", "Completed procedure only"),
        ("m", "API", "STK", "Cancel the linked Stock Entry (Material Issue)"),
        ("n", "STK", "ERPNext reverses the ledger: the medicines go back into the same batches. The original rows are kept, marked cancelled.", "stock"),
        ("f", "end"),
        ("m", "API", "HLT", "Cancel the Clinical Procedure (status Cancelled)"),
        ("m", "API", "HLT", "Save the reason and who cancelled"),
        ("m", "API", "APP", "{ name, stock_returned }", "ret"),
    ]
    return sequence([APP, API, STK, HLT], steps)


def fig_remove():
    steps = [
        ("m", "APP", "API", "POST give_out(medicine, qty, reason, recipient, date, client_id)"),
        ("n", "API", "Role check. client_id already recorded → return the first result. Validate: qty > 0 · reason is in the list."),
        ("n", "API", "Allocate batches. Normal reasons: valid batches, earliest expiry first. Reason “Expired stock”: expired batches only. Not enough → refused, nothing saved."),
        ("m", "API", "STK", "Insert + submit Stock Entry · Material Issue from Pharmacy: one line per batch, reason, recipient"),
        ("n", "STK", "Stock Ledger Entry −qty per batch · Bin and Batch quantities go down.", "stock"),
        ("m", "API", "APP", "{ stock_entry, batches }", "ret"),
    ]
    return sequence([APP, API, STK], steps)


def fig_request():
    lanes = [("S", "Staff", "any pharmacy user", "app"), ("A", "Administrator", "Pharmacy Admin", "app"), API, STK]
    steps = [
        ("m", "S", "API", "POST request_stock(medicine, qty, urgency, reason, client_id)"),
        ("m", "API", "STK", "Insert Material Request (Purchase) as a draft. Needed by = today + 14 / 3 / 0 days (Routine / Urgent / Emergency)"),
        ("n", "STK", "Notification: bell alert to the administrators.", "stock"),
        ("s", "later"),
        ("m", "A", "API", "POST decide_request(name, approve | reject, note). Admins only."),
        ("m", "API", "STK", "Approve: submit the Material Request. Reject: mark rejected (stays a draft, note saved)."),
        ("n", ("API", "STK"), "A request never adds stock. Stock goes up only when the delivery is recorded with Add stock (Flow 2)."),
    ]
    return sequence(lanes, steps)


# ----------------------------------------------------------------------------- document

CSS = f"""
@font-face {{ font-family: 'Newsreader'; src: url(data:font/woff2;base64,{font('@fontsource-variable/newsreader/files/newsreader-latin-opsz-normal.woff2')}); font-weight: 200 800; }}
@font-face {{ font-family: 'Newsreader'; font-style: italic; src: url(data:font/woff2;base64,{font('@fontsource-variable/newsreader/files/newsreader-latin-opsz-italic.woff2')}); font-weight: 200 800; }}
@font-face {{ font-family: 'Figtree'; src: url(data:font/woff2;base64,{font('@fontsource-variable/figtree/files/figtree-latin-wght-normal.woff2')}); font-weight: 300 900; }}
@font-face {{ font-family: 'Plex'; src: url(data:font/woff2;base64,{font('@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2')}); }}
@page {{ size: A4; margin: 15mm 14mm 16mm; @bottom-right {{ content: counter(page); font: 8pt Figtree; color: #8a908c; }} @bottom-left {{ content: "PharmaStock · stock and care flows"; font: 8pt Figtree; color: #8a908c; }} }}
@page :first {{ margin: 0; @bottom-right {{ content: none; }} @bottom-left {{ content: none; }} }}
* {{ box-sizing: border-box; }}
body {{ font: 9.4pt/1.45 Figtree, sans-serif; color: #1B1F1D; margin: 0; }}
h1, h2, h3 {{ font-family: Newsreader, serif; font-weight: 500; margin: 0; }}
h1 {{ font-size: 25pt; line-height: 1.1; margin: 0 0 3mm; }}
h2 {{ font-size: 19pt; line-height: 1.15; margin: 0 0 2mm; }}
h3 {{ font-family: Figtree; font-size: 8pt; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: #6B726E; margin: 0 0 1.5mm; }}
p {{ margin: 0 0 2.5mm; }}
.kicker {{ font-size: 8pt; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #2F6B57; margin-bottom: 1.5mm; }}
.lead {{ font-size: 10.4pt; color: #3A403D; max-width: 160mm; }}
.cover {{ page-break-after: always; height: 297mm; background: #173F33; color: #fff; padding: 30mm 22mm; position: relative; }}
.cover img {{ width: 22mm; border-radius: 5mm; }}
.cover h1 {{ font-size: 40pt; margin-top: 70mm; color: #fff; }}
.cover h1 em {{ color: #A9D1BE; }}
.cover p {{ color: #c9ddd3; font-size: 12pt; max-width: 125mm; }}
.cover .meta {{ position: absolute; left: 22mm; bottom: 22mm; font-size: 9pt; color: #9fc2b1; }}
.toc {{ page-break-after: always; }}
.toc ol {{ columns: 2; column-gap: 12mm; padding-left: 5mm; margin: 4mm 0 0; }}
.toc li {{ margin-bottom: 2mm; break-inside: avoid; }}
.toc li span {{ display: block; font-size: 8.4pt; color: #6B726E; }}
.flow, .sec {{ page-break-before: always; }}
.fig {{ border: .3mm solid #E4E0D4; border-radius: 3mm; padding: 3mm; margin: 3mm 0 4mm; background: #fff; }}
.cols {{ display: grid; grid-template-columns: 1.25fr 1fr; gap: 6mm; }}
ul {{ margin: 0; padding-left: 4.2mm; }} li {{ margin-bottom: 1.2mm; }}
table {{ width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; font-size: 8.6pt; }}
th {{ text-align: left; font-size: 7.6pt; letter-spacing: .06em; text-transform: uppercase; color: #6B726E; border-bottom: .4mm solid #1B1F1D; padding: 1.5mm 2mm; }}
td {{ border-bottom: .2mm solid #E4E0D4; padding: 1.7mm 2mm; vertical-align: top; }}
td:first-child {{ font-weight: 600; }}
table.tight td {{ padding: 1mm 2mm; }} table.tight {{ margin: 1mm 0 3mm; }}
.yes {{ color: #2F6B57; font-weight: 700; }} .no {{ color: #B4412D; font-weight: 700; }}
code, .mono {{ font-family: Plex, monospace; font-size: 8pt; background: #F3F0E6; padding: .2mm 1mm; border-radius: 1mm; }}
.callout {{ border-left: 1mm solid #2F6B57; background: #EEF5F1; padding: 3mm 4mm; border-radius: 0 2mm 2mm 0; margin: 3mm 0; }}
.callout.warn {{ border-color: #B7791F; background: #FBF3E3; }}
.legend {{ display: flex; gap: 4mm; flex-wrap: wrap; font-size: 8pt; color: #6B726E; margin-top: 1mm; }}
.legend i {{ display: inline-block; width: 3mm; height: 3mm; border-radius: 1mm; margin-right: 1.2mm; vertical-align: -.5mm; border: .2mm solid; }}
"""


def build():
    sections = []

    toc_items = [
        ("The idea in one page", "Two modules, one medicine, one source of truth"),
        ("How the records are linked", "Which Stock record matches which Health record"),
        ("Flow 1 · Create a medicine", "Item in Stock, Medication in Health, kept in step"),
        ("Flow 2 · Receive stock", "Batch, expiry, Stock Entry, automatic reorder"),
        ("Flow 3 · Register a patient", "Patient and linked Customer"),
        ("Flow 4 · Create a procedure type", "Template with the medicines it uses"),
        ("Flow 5 · Record a procedure", "The only way stock reaches a patient"),
        ("Flow 6 · Cancel a procedure", "Stock returns, history stays"),
        ("Flow 7 · Remove stock", "Damaged, expired, transfer, adjustment"),
        ("Flow 8 · Request stock", "Request, approval, delivery"),
        ("Keeping medicines in sync", "Edit, archive, delete, restore"),
        ("Permissions", "Roles, the elevated write, the matrix"),
        ("Offline, safe retries, notifications", "What works without a connection"),
        ("Where everything is in the ERPNext desk", "For administrators"),
        ("Setup and limits", "Install, Press, what is not built yet"),
    ]
    cover = (f'<div class="cover"><img src="data:image/svg+xml;base64,{LOGO}"><h1>Pharma<em>stock</em><br>Stock and care flows</h1>'
             '<p>How a medicine, a patient and a procedure move through ERPNext Stock and Frappe Health, step by step, with the rules and the permissions behind each one.</p>'
             '<div class="meta">Version 16 (Frappe, ERPNext, Frappe Health) · github.com/Arielpetit/pharmastock · written from the source code</div></div>')
    toc = ('<div class="toc"><div class="kicker">Contents</div><h1>What this document covers</h1>'
           '<p class="lead">Each flow page has the same layout: a sequence diagram, then the rules and errors, then what exists afterwards. Numbers in the diagram match the steps in order.</p><ol>'
           + "".join(f"<li>{a}<span>{b}</span></li>" for a, b in toc_items) + "</ol>"
           '<div class="legend" style="margin-top:8mm"><b style="color:#1B1F1D">Colours:</b>'
           '<span><i style="background:#EDE9DD;border-color:#B9B3A0"></i>App / user</span>'
           '<span><i style="background:#DCEBE3;border-color:#2F6B57"></i>PharmaStock API</span>'
           '<span><i style="background:#F6E6C8;border-color:#B7791F"></i>ERPNext Stock</span>'
           '<span><i style="background:#DCE8F3;border-color:#2B5F8A"></i>Frappe Health</span></div></div>')
    sections += [cover, toc]

    sections.append(
        '<section class="sec"><div class="kicker">Overview</div><h2>The idea in one page</h2>'
        '<p class="lead">A health center needs two things that normally live apart: the <b>pharmacy stock</b> and the <b>patient care</b>. '
        'PharmaStock keeps both in ERPNext, in two standard modules, and joins them through one rule: <b>medicine only leaves the stock for a reason, and a patient only receives medicine through a procedure.</b></p>'
        f'<div class="fig">{fig_architecture()}</div>'
        + table(["Module", "Owns", "Examples"], [
            ["ERPNext Stock", "Quantities, batches, expiry, every movement (the ledger)", "Item, Batch, Stock Entry, Stock Ledger, Bin, Material Request"],
            ["Frappe Health", "People and care", "Patient, Medication, Clinical Procedure Template, Clinical Procedure"],
            ["PharmaStock", "The screens, the rules between the two, the permissions", "api.py, health.py, the /pharmacy app"]])
        + '<div class="callout"><b>One request, one transaction.</b> Every button is one call to the API. The API writes to Stock and Health together; if any step fails (for example not enough valid stock), nothing is saved. No half-finished records.</div>'
        '<div class="callout warn"><b>How stock reaches a patient.</b> Medicine given to a patient is recorded through a <b>procedure</b> (Flow 5). The Remove stock page (Flow 7) covers the reasons that have no patient: damaged, expired, transfer, other adjustment. The older “Dispensed to a patient” reason still exists on that page.</div>'
        '</section>')

    sections.append(
        '<section class="sec"><div class="kicker">Overview</div><h2>How the records are linked</h2>'
        '<p class="lead">One medicine is <b>one Item</b> in Stock and <b>one Medication</b> in Health, pointing at each other. A procedure copies its medicines from a template, and the stock it uses is a normal Stock Entry linked back to the procedure.</p>'
        f'<div class="fig">{fig_links()}</div>'
        + table(["User action", "ERPNext Stock record", "Frappe Health record"], [
            ["Add a medicine", "Item (+ Batch + Stock Entry if first stock)", "Medication + Medication Linked Item"],
            ["Receive a delivery", "Batch + Stock Entry · Material Receipt", "—"],
            ["Register a patient", "—", "Patient (+ Customer in ERPNext)"],
            ["Create a procedure type", "service Item (created by Health)", "Clinical Procedure Template + items"],
            ["Record a procedure", "Stock Entry · Material Issue (reason “Used in a procedure”)", "Clinical Procedure + items"],
            ["Remove stock (no patient)", "Stock Entry · Material Issue", "—"],
            ["Request stock", "Material Request", "—"]])
        + '</section>')

    sections.append(flow(1, "Create a medicine",
        "The pharmacist adds a medicine once. The API creates the Stock side and the Health side together, so they cannot drift apart.",
        fig_create_medicine(),
        ["Name is required. The category must be one of the Medicine item groups.",
         "A name already in use is refused: “already exists. Open it and use Add Stock instead.”",
         "An archived medicine with the same name is restored with the new details.",
         "The unit (“Counted in”) is fixed at creation. Minimum stock sets the reorder level (reorder quantity = twice the minimum).",
         "Strength “500mg” becomes 500 mg in Health; text that does not parse stays on the Item and is stored as 0 mg."],
        ["Item: stock item with batch and expiry tracking, reorder level, owner = the user.",
         "Medication with the same name, linked both ways to the Item.",
         "Optionally a Batch and a Stock Entry · Material Receipt for the first stock."]))

    sections.append(flow(2, "Receive stock",
        "Every delivery is recorded with an expiry date. Stock is tracked per batch, so the oldest valid batch can always be used first.",
        fig_add_stock(),
        ["Quantity must be above 0. The expiry date is required and must be after the date received.",
         "A lot number that exists must belong to the same medicine and have the same expiry date, otherwise it is refused.",
         "Price can be 0 (donations); stock is then valued at zero.",
         "Sending the same client_id twice records one delivery only.",
         "Low stock is not checked here: ERPNext's nightly job creates the reorder request."],
        ["A Batch (if new) with its expiry date.",
         "A submitted Stock Entry · Material Receipt, owner = the user.",
         "Stock Ledger Entry +qty; Bin and Batch quantities updated."]))

    sections.append(flow(3, "Register a patient",
        "Patients are Frappe Health records. The pharmacy app only asks for what a clinic needs at the desk.",
        fig_patient(),
        ["First name and sex are required. Sex is Female or Male.",
         "Date of birth cannot be in the future. Blood group must be from the list.",
         "Two patients with the same name get “- 2”, “- 3”… as their id. Search by name or phone in the app.",
         "Patients are never deleted from the app. The list shows active patients."],
        ["Patient (Frappe Health), owner = the user.",
         "A linked ERPNext Customer, created by Frappe Health.",
         "Age is calculated, never stored."]))

    sections.append(flow(4, "Create a procedure type",
        "A procedure type is a care you give often (wound dressing, injection) and the medicines it uses each time.",
        fig_template(),
        ["Name required and unique. Medicines must be active; quantities above 0.",
         "A type can use no medicine at all (consume stock = no).",
         "A type can be hidden (“no longer used”). It stays in old records and can be shown again.",
         "Editing a type changes future procedures only; recorded procedures keep their own medicines."],
        ["Clinical Procedure Template with its items (Frappe Health).",
         "A service Item named like the template (created by Health, not a stock item).",
         "Item group “Clinical Procedures”."]))

    sections.append(flow(5, "Record a procedure",
        "This is how medicine reaches a patient. The procedure and the stock movement are created together and linked.",
        fig_record(),
        ["Date cannot be in the future. Medicines default to the template; the nurse can change quantities or add medicines.",
         "“Done now”: stock leaves immediately. “Planned”: the procedure waits (status Pending) and nothing leaves until “Mark as done”.",
         "Only valid batches are used, earliest expiry first. Expired batches are never used here.",
         "Not enough valid stock for any medicine → refused, nothing saved.",
         "The stock movement shows “Used in a procedure” with the patient's name; the same client_id twice records one procedure."],
        ["Clinical Procedure (submitted) with items, status Completed or Pending.",
         "Stock Entry · Material Issue, linked to the procedure, one line per batch used.",
         "The patient file lists the procedure; reports list the movement."]))

    sections.append(flow(6, "Cancel a procedure",
        "A procedure recorded by mistake can be cancelled by staff or an administrator. Stock comes back; nothing is erased.",
        fig_cancel(),
        ["A completed procedure needs a reason (for example “Recorded for the wrong patient”).",
         "A planned procedure can be cancelled without a reason; no stock is involved.",
         "A procedure can be cancelled once. It cannot be reopened; record a new one instead.",
         "The medicines return to the same batches they came from, with their original expiry dates."],
        ["Stock Entry cancelled: ledger reversed, stock back up.",
         "Reports, medicine history and dashboard still show the original movement, marked Cancelled, quantity struck through.",
         "The procedure stays in the patient file as Cancelled with the reason and who cancelled it."]))

    sections.append(flow(7, "Remove stock without a patient",
        "Some stock leaves for reasons that have no patient. The Remove stock page records them, with a reason, against the oldest valid batch.",
        fig_remove(),
        ["Quantity above 0. A reason is required from the list.",
         "“Expired stock” uses expired batches only; every other reason uses valid batches only.",
         "A medicine with only expired stock cannot be given out except as “Expired stock”.",
         "The recipient field is free text (patient name or file number, store name…)."],
        ["Stock Entry · Material Issue with reason and recipient.",
         "Ledger −qty per batch.",
         "Visible in Reports and in the medicine history."],
        table(["Reason", "Batches used", "Has a patient?"], [
            ["Used in a procedure (Flow 5)", "valid, earliest expiry first", "yes, through the procedure"],
            ["Dispensed to a patient", "valid, earliest expiry first", "free text name"],
            ["Transfer to another store or department", "valid, earliest expiry first", "no"],
            ["Damaged stock", "valid, earliest expiry first", "no"],
            ["Expired stock", "expired only", "no"],
            ["Other authorized adjustment", "valid, earliest expiry first", "no"]])))

    sections.append(flow(8, "Request stock",
        "Staff ask for medicine to be ordered. An administrator decides. The request never changes the stock.",
        fig_request(),
        ["Urgency sets the needed-by date: Routine +14 days, Urgent +3, Emergency today.",
         "Only an administrator can approve or reject. A request can be decided once.",
         "Approve submits the Material Request; reject keeps it as a draft marked rejected, with the note.",
         "ERPNext also creates a request by itself when stock falls to the minimum (reorder level)."],
        ["Material Request (draft, then submitted if approved).",
         "Bell notification to the administrators.",
         "The delivery itself is recorded later with Receive stock (Flow 2)."]))

    sections.append(
        '<section class="sec"><div class="kicker">Maintenance</div><h2>Keeping medicines in sync</h2>'
        '<p class="lead">Stock is the source of truth; Health follows. A pharmacy change on a medicine updates its Medication in the same request.</p>'
        + table(["Action in the app", "Stock (Item)", "Health (Medication)"], [
            ["Create", "Item created", "Medication + Linked Item created, Item.custom_medication set"],
            ["Edit name, category, form, strength", "Item updated", "Medication updated (class, dosage form, strength + unit, name field). Its id is not renamed."],
            ["Change the minimum or the location", "Item reorder level / location", "no change (not clinical data)"],
            ["Delete, never used", "Item deleted", "Medication and Linked Item deleted"],
            ["Delete, has history or in a procedure", "Item archived (disabled); ledger kept", "Medication disabled"],
            ["Add the same name again", "Archived Item restored", "Medication re-enabled and updated"],
            ["Delete while stock remains", "refused: give it out or record it as expired first", "no change"]])
        + '<div class="callout"><b>Direction.</b> The sync is one way, from the pharmacy app into Health. A Medication edited by hand in the ERPNext desk does not change the Item. Existing medicines are synchronised when the app is installed or updated (<code>bench migrate</code>).</div>'
        '<h3>Reminder: how a medicine is identified</h3>'
        + table(["Where", "Identifier"], [["Item", "item code = the medicine name (e.g. “Paracetamol 500mg Tablet”)"],
                                            ["Medication", "same string; “name (form)” if a Medication of that name already existed"],
                                            ["Batch", "BATCH-00001… or the lot number typed by the pharmacist"]])
        + '</section>')

    sections.append(
        '<section class="sec"><div class="kicker">Security</div><h2>Permissions</h2>'
        '<p class="lead">Two pharmacy roles use the app. Neither has access to the ERPNext desk. The API checks the role on every call, then does the work for them with full rights, so nobody needs permissions on ERPNext documents.</p>'
        f'<div class="fig">{fig_permissions()}</div>'
        + table(["Action", "Pharmacy Staff", "Pharmacy Admin"], [
            ["Sign in, dashboard, medicine list, reports, notifications", '<span class="yes">yes</span>', '<span class="yes">yes</span>'],
            ["Add, edit, delete a medicine", '<span class="yes">yes</span>', '<span class="yes">yes</span>'],
            ["Receive stock · Remove stock · Request stock", '<span class="yes">yes</span>', '<span class="yes">yes</span>'],
            ["Approve or reject a stock request", '<span class="no">no</span>', '<span class="yes">yes</span>'],
            ["Register and edit patients", '<span class="yes">yes</span>', '<span class="yes">yes</span>'],
            ["Create, edit, hide procedure types", '<span class="yes">yes</span>', '<span class="yes">yes</span>'],
            ["Record, complete, cancel a procedure", '<span class="yes">yes</span>', '<span class="yes">yes</span>'],
            ["Create users, change roles, disable users", '<span class="no">no</span>', '<span class="yes">yes</span>'],
            ["ERPNext desk (/desk), any ERPNext screen", '<span class="no">no</span>', '<span class="no">no</span>']], "tight")
        + '<div class="cols"><div><h3>How it is enforced</h3>' + ul([
            "Both roles have <code>desk_access = 0</code>: the desk answers “Not Permitted”.",
            "Every API method starts with the role check. The screens hide what a role cannot do, but the server decides.",
            "Only <code>boot</code> is open to guests, and it returns nothing without a session.",
            "Each record keeps the real user as owner; a cancellation also keeps its reason and author."]) + '</div><div><h3>Managing users</h3>' + ul([
            "The administrator creates users in the Staff page: name, email, role, first password.",
            "Only the two pharmacy roles can be given there. A user with other ERPNext roles is changed by a System Manager only.",
            "An administrator cannot remove their own admin access.",
            "Administrator / System Manager keep the desk for setup and repair."]) + '</div></div></section>')

    sections.append(
        '<section class="sec"><div class="kicker">Reliability</div><h2>Offline, safe retries, notifications</h2>'
        '<p class="lead">Health centers lose connection. Stock work continues; care work needs a connection because it needs patients and live stock.</p>'
        + table(["Works offline (queued, sent later)", "Needs a connection"], [
            ["Receive stock · Remove stock · Request stock", "Register patient · procedure types · record, complete, cancel a procedure"],
            ["Reading the last loaded lists and dashboard", "Approve or reject a request · manage staff · reports with new filters"]])
        + '<div class="callout"><b>Safe retries.</b> The app gives every write a unique <code>client_id</code>. If the same call arrives twice (a double tap, or an offline queue sent again) the server returns the first result and records nothing new. Stock is never counted twice.</div>'
        '<h3>Notifications (bell)</h3>'
        + table(["Event", "Who is told", "Created by"], [
            ["A batch expires within 60 days", "Staff and Admin", "ERPNext notification on Batch"],
            ["Stock fell to the minimum; a reorder request was created", "Admin", "ERPNext auto reorder + notification"],
            ["A stock request is waiting for approval", "Admin", "Notification on Material Request"]])
        + '<h3>Behaviour with expiry</h3>' + ul([
            "Every outgoing movement picks valid batches by earliest expiry first.",
            "Expired stock can only leave as “Expired stock”.",
            "The dashboard, medicine list and reports flag low, expiring and expired stock."]) + '</section>')

    sections.append(
        '<section class="sec"><div class="kicker">For administrators</div><h2>Where everything is in the ERPNext desk</h2>'
        '<p class="lead">The desk is for the site owner. Everything the app creates is a standard ERPNext or Frappe Health record, so it can be inspected there.</p>'
        + table(["To see", "Open in the desk", "Look for"], [
            ["Medicines", "/desk/item (filter item group: Medicine)", "custom dosage form, strength, Medication link"],
            ["Medications (Health)", "/desk/medication", "linked items table"],
            ["Batches and expiry", "/desk/batch", "quantity and expiry per lot"],
            ["Every stock movement", "/desk/query-report/Stock Ledger", "voucher = Stock Entry"],
            ["Stock Entries", "/desk/stock-entry", "Reason, Recipient, Clinical Procedure"],
            ["Patients", "/desk/patient", "linked Customer"],
            ["Procedure types", "/desk/clinical-procedure-template", "items = medicines used"],
            ["Procedures", "/desk/clinical-procedure", "status, cancel reason"],
            ["Stock requests", "/desk/material-request", "urgency, decision note"],
            ["Users and roles", "/desk/user", "roles Pharmacy Staff / Pharmacy Admin"],
            ["Installed apps", "/desk/installed-applications", "frappe, erpnext, healthcare, pharmastock"]])
        + '<div class="callout warn"><b>Do not edit stock records by hand in the desk.</b> Create movements through the app so reasons, owners and links stay complete. Cancelling a Stock Entry in the desk without cancelling its procedure leaves a procedure that no longer matches the stock.</div></section>')

    sections.append(
        '<section class="sec"><div class="kicker">Operations</div><h2>Setup and limits</h2>'
        '<h3>What the installation needs</h3>' + ul([
            "Frappe, ERPNext and <b>Frappe Health</b>, all version 16, on the same bench. PharmaStock lists Health as a required app.",
            "A company created by the ERPNext setup wizard (country Cameroon, currency XAF). The “Pharmacy” warehouse is created for it.",
            "On install and on every <code>bench migrate</code>: roles, custom fields, medicine categories, units, bell notifications, and a Medication for every existing medicine.",
            "On Frappe Cloud / Press: add Frappe Health to the bench group, add the GitHub repository as an app, deploy, then install the app on each clinic site."])
        + '<h3>Test coverage</h3>' + table(["Test", "Checks", "Covers"], [
            ["tests/api_smoke.py", "23", "Stock in and out, earliest expiry first, refusals, retries, requests, permissions"],
            ["tests/health_smoke.py", "26", "Patient, procedure type, done and planned procedures, stock used, cancelling, history"],
            ["tests/e2e.mjs", "21", "Browser: staff and admin journeys, offline, French, phone"],
            ["tests/care_e2e.mjs", "14", "Browser: medicine, patient, type, procedures, cancel, dashboard"]])
        + '<h3>Not built yet</h3>' + ul([
            "Consultations, practitioners and appointments (Frappe Health has them; they need practitioner setup first).",
            "Billing and invoices for procedures (types are created as not billable).",
            "Offline recording of patients and procedures.",
            "Two-way sync: editing a Medication in the desk does not update the Item.",
            "Email or push notifications (bell only)."]) + '</section>')

    html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>PharmaStock · stock and care flows</title><style>{CSS}</style></head><body>{"".join(sections)}</body></html>'
    (HERE / "flows.html").write_text(html)
    out = ROOT / "docs/PharmaStock-Flows.pdf"
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", f"file://{HERE / 'flows.html'}"], check=True, capture_output=True)
    print("wrote", out)


if __name__ == "__main__":
    build()
