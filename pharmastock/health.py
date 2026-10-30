"""Patients and clinical procedures, stored in Frappe Health (the `healthcare` app).

The pharmacy keeps one record per medicine in each module:

- ERPNext Stock: the Item, its batches and every stock movement (see `api.py`).
- Frappe Health: a Medication linked to that Item, so doctors and nurses find the same medicine
  in prescriptions and procedures. `sync_medication` keeps it in step whenever the pharmacy adds,
  edits, archives or brings back a medicine.

A clinical procedure is done for a patient from a template (e.g. "Wound dressing"). The template
lists the medicines it uses. Completing the procedure takes those medicines out of the pharmacy
store with the same rules as a stock out: valid batches only, earliest expiry first.
"""

import json
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

from pharmastock.api import (
	_allocate,
	_company,
	_existing,
	_keep_owner,
	_owner,
	_require_staff,
	_submit,
	_user_names,
	_warehouse,
	_writes,
)

PROCEDURE_REASON = "Used in a procedure"
PROCEDURE_GROUP = "Clinical Procedures"
GENDERS = ["Female", "Male"]
BLOOD_GROUPS = ["A Positive", "A Negative", "B Positive", "B Negative", "AB Positive", "AB Negative", "O Positive", "O Negative"]
# strength units as typed in the app ("500mg", "1 g", "5ml") -> UOM used by Frappe Health
STRENGTH_UNITS = {"mg": "mg", "g": "g", "mcg": "mcg", "µg": "mcg", "ug": "mcg", "ml": "ml", "iu": "IU", "ui": "IU", "%": "%"}


def has_health():
	return "healthcare" in frappe.get_installed_apps()


def _require_health():
	if not has_health():
		frappe.throw(_("Patients and procedures need the Frappe Health app on this site."))


def _ensure(doctype, name, **fields):
	if not frappe.db.exists(doctype, name):
		frappe.get_doc({"doctype": doctype, **fields}).insert(ignore_permissions=True)
	return name


# ------------------------------------------------------------------ medicine <-> medication


def _parse_strength(text):
	"""'500mg' -> (500.0, 'mg'). Anything else -> (0, 'mg'), the text stays on the Item."""
	m = re.match(r"^\s*([\d.,]+)\s*([a-zA-Zµ%]+)?", text or "")
	if not m:
		return 0, _ensure("UOM", "mg", uom_name="mg", enabled=1)
	value = flt(m.group(1).replace(",", "."))
	unit = STRENGTH_UNITS.get((m.group(2) or "mg").lower(), "mg")
	return value, _ensure("UOM", unit, uom_name=unit, enabled=1)


def _medication_of(code):
	return frappe.db.get_value("Medication Linked Item", {"item": code, "parenttype": "Medication"}, "parent")


def sync_medication(code):
	"""Create or update the Frappe Health Medication for a pharmacy medicine (an ERPNext Item).

	Written straight to the database on update: Medication's own save hooks rename the Item and
	create prices, which the pharmacy does not want.
	"""
	if not has_health() or not frappe.db.exists("Item", code):
		return None
	item = frappe.db.get_value("Item", code, ["item_name", "item_group", "custom_dosage_form", "custom_strength", "stock_uom",
											  "disabled"], as_dict=True)
	strength, strength_uom = _parse_strength(item.custom_strength)
	fields = {
		"generic_name": item.item_name,
		"medication_class": _ensure("Medication Class", item.item_group, medication_class=item.item_group),
		"dosage_form": _ensure("Dosage Form", item.custom_dosage_form or "Other", dosage_form=item.custom_dosage_form or "Other"),
		"strength": strength,
		"strength_uom": strength_uom,
		"disabled": item.disabled,
		"is_orderable": 1,
	}
	name = _medication_of(code)
	if name:
		frappe.db.set_value("Medication", name, fields)
		frappe.db.set_value("Medication Linked Item", {"parent": name, "item": code}, "item_group", item.item_group)
	else:
		med = frappe.get_doc({"doctype": "Medication", **fields})
		# named like the medicine, unless a Medication of that name already exists (e.g. created in the desk)
		med.name = code if not frappe.db.exists("Medication", code) else f"{code} ({item.custom_dosage_form or item.stock_uom})"
		med.flags.name_set = True
		med.insert(ignore_permissions=True)
		frappe.get_doc({
			"doctype": "Medication Linked Item", "parent": med.name, "parenttype": "Medication", "parentfield": "linked_items",
			"idx": 1, "item_code": code, "item": code, "item_group": item.item_group, "stock_uom": item.stock_uom, "is_billable": 0,
		}).db_insert()
		name = med.name
	if frappe.get_meta("Item").has_field("custom_medication"):
		frappe.db.set_value("Item", code, "custom_medication", name, update_modified=False)
	return name


def remove_medication(code, delete=False):
	"""The medicine was archived (disable its Medication) or deleted (delete the Medication too)."""
	if not has_health():
		return
	name = _medication_of(code)
	if not name:
		return
	if delete:
		frappe.db.delete("Medication Linked Item", {"parent": name, "parenttype": "Medication"})
		frappe.delete_doc("Medication", name, ignore_permissions=True, force=True)
	else:
		frappe.db.set_value("Medication", name, "disabled", 1)


def sync_all_medications():
	"""Give every pharmacy medicine its Medication (after an update, or after installing Frappe Health)."""
	from pharmastock.api import _medicine_groups

	groups = _medicine_groups()
	if not has_health() or not groups:
		return
	for code in frappe.get_all("Item", filters={"item_group": ["in", groups], "is_stock_item": 1}, pluck="name"):
		try:
			sync_medication(code)
		except Exception:
			frappe.log_error(f"PharmaStock: could not sync Medication for {code}")


# ------------------------------------------------------------------ patients


def _age(dob):
	if not dob:
		return None
	dob, today = getdate(dob), getdate()
	return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _patient_row(p):
	p.age = _age(p.dob)
	return p


@frappe.whitelist()
def patients(search=None):
	"""Patients, most recent first, with their number of procedures and the date of the last one."""
	_require_staff()
	_require_health()
	conditions, values = ["p.status = 'Active'"], {}
	if search:
		conditions.append("(p.patient_name like %(s)s or p.mobile like %(s)s or p.name like %(s)s)")
		values["s"] = f"%{search}%"
	rows = frappe.db.sql(
		f"""
		select p.name, p.patient_name, p.first_name, p.last_name, p.sex, p.dob, p.mobile, p.blood_group, p.creation,
			(select count(*) from `tabClinical Procedure` cp where cp.patient = p.name and cp.docstatus = 1) as procedures,
			(select max(cp.start_date) from `tabClinical Procedure` cp where cp.patient = p.name and cp.docstatus = 1) as last_visit
		from `tabPatient` p
		where {" and ".join(conditions)}
		order by p.creation desc
		limit 500
		""",
		values,
		as_dict=True,
	)
	return [_patient_row(r) for r in rows]


@frappe.whitelist()
def patient(name):
	_require_staff()
	_require_health()
	if not frappe.db.exists("Patient", name):
		frappe.throw(_("Patient not found"), frappe.DoesNotExistError)
	p = frappe.db.get_value("Patient", name, ["name", "patient_name", "first_name", "last_name", "sex", "dob", "mobile",
											  "blood_group", "allergies", "medical_history", "creation", "owner"], as_dict=True)
	_patient_row(p)
	p.procedures = procedures(patient=name)
	return p


@frappe.whitelist(methods=["POST"])
@_writes(admin=False)
def save_patient(first_name, sex, last_name=None, dob=None, mobile=None, blood_group=None, allergies=None,
				 medical_history=None, name=None):
	"""Register a patient in Frappe Health, or update one when `name` is given."""
	_require_health()
	first_name = (first_name or "").strip()
	if not first_name:
		frappe.throw(_("Please enter the patient's first name"))
	if sex not in GENDERS:
		frappe.throw(_("Please choose the patient's sex"))
	if blood_group and blood_group not in BLOOD_GROUPS:
		blood_group = None
	if dob and getdate(dob) > getdate():
		frappe.throw(_("The date of birth cannot be in the future"))
	fields = {"first_name": first_name, "last_name": (last_name or "").strip(), "sex": sex, "dob": dob or None,
			  "mobile": (mobile or "").strip(), "blood_group": blood_group, "allergies": allergies or "",
			  "medical_history": medical_history or ""}
	if name:
		doc = frappe.get_doc("Patient", name)
		doc.update(fields)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "Patient", "owner": _owner(), **fields})
		doc.insert(ignore_permissions=True)
		_keep_owner(doc)
	return {"name": doc.name, "patient_name": doc.patient_name}


# ------------------------------------------------------------------ procedure templates


def _items_arg(items):
	"""[{medicine, qty}] from the app -> validated rows for a Clinical Procedure Item table."""
	if isinstance(items, str):
		items = json.loads(items or "[]")
	rows = []
	for row in items or []:
		code, qty = row.get("medicine"), flt(row.get("qty"))
		if not code:
			continue
		if qty <= 0:
			frappe.throw(_("Please enter a quantity above 0 for {0}").format(code))
		item = frappe.db.get_value("Item", {"name": code, "disabled": 0}, ["name", "item_name", "stock_uom"], as_dict=True)
		if not item:
			frappe.throw(_("Medicine not found: {0}").format(code))
		rows.append({"item_code": item.name, "item_name": item.item_name, "qty": qty, "uom": item.stock_uom,
					 "stock_uom": item.stock_uom, "conversion_factor": 1, "transfer_qty": qty})
	return rows


def _item_rows(parent, parenttype):
	return frappe.get_all("Clinical Procedure Item", filters={"parent": parent, "parenttype": parenttype},
						  fields=["item_code as medicine", "item_name as medicine_name", "qty", "stock_uom as unit"], order_by="idx")


@frappe.whitelist()
def procedure_templates(include_disabled=0):
	_require_staff()
	_require_health()
	filters = {} if cint(include_disabled) else {"disabled": 0}
	rows = frappe.get_all("Clinical Procedure Template", filters=filters,
						  fields=["name", "template", "description", "disabled", "consume_stock", "modified"], order_by="template asc")
	counts = dict(frappe.db.sql("""select procedure_template, count(*) from `tabClinical Procedure`
		where docstatus = 1 group by procedure_template"""))
	for r in rows:
		r.items = _item_rows(r.name, "Clinical Procedure Template")
		r.used = counts.get(r.name, 0)
	return rows


@frappe.whitelist(methods=["POST"])
@_writes(admin=False)
def save_procedure_template(template, items, description=None, name=None, disabled=0):
	"""Create or edit a procedure template and the medicines it uses."""
	_require_health()
	template = (template or "").strip()
	if not template:
		frappe.throw(_("Please enter the name of the procedure"))
	rows = _items_arg(items)
	fields = {"description": (description or "").strip() or template, "consume_stock": 1 if rows else 0,
			  "disabled": cint(disabled)}
	if name:
		doc = frappe.get_doc("Clinical Procedure Template", name)
		doc.update(fields)
		doc.set("items", rows)
		doc.save(ignore_permissions=True)
		return {"name": doc.name}
	if frappe.db.exists("Clinical Procedure Template", template):
		frappe.throw(_("A procedure named {0} already exists").format(template), frappe.DuplicateEntryError)
	group = _ensure("Item Group", PROCEDURE_GROUP, item_group_name=PROCEDURE_GROUP, parent_item_group="All Item Groups", is_group=0)
	# Frappe Health also creates a (service) Item for the procedure, named like the template
	item_code = template if not frappe.db.exists("Item", template) else f"{template} (procedure)"
	doc = frappe.get_doc({"doctype": "Clinical Procedure Template", "owner": _owner(), "template": template, "item_code": item_code,
						  "item_group": group, "is_billable": 0, "rate": 0, "items": rows, **fields})
	doc.insert(ignore_permissions=True)
	_keep_owner(doc)
	return {"name": doc.name}


# ------------------------------------------------------------------ procedures


def _procedure_rows(filters, limit=100):
	rows = frappe.get_all("Clinical Procedure", filters=filters,
						  fields=["name", "patient", "patient_name", "procedure_template", "start_date", "status", "notes",
								  "owner", "creation", "consume_stock", "actual_end_datetime", "docstatus", "custom_cancel_reason",
								  "custom_cancelled_by"],
						  order_by="start_date desc, creation desc", limit=cint(limit))
	names = _user_names([r.owner for r in rows] + [r.custom_cancelled_by for r in rows])
	entries = {}
	if rows and frappe.get_meta("Stock Entry").has_field("custom_clinical_procedure"):
		entries = dict(frappe.get_all("Stock Entry", filters={"custom_clinical_procedure": ["in", [r.name for r in rows]],
																"docstatus": 1}, fields=["custom_clinical_procedure", "name"], as_list=True))
	for r in rows:
		r.items = _item_rows(r.name, "Clinical Procedure")
		r.by = names.get(r.owner, r.owner)
		r.cancelled_by = names.get(r.custom_cancelled_by, r.custom_cancelled_by)
		r.stock_entry = entries.get(r.name)
		r.state = "cancelled" if r.docstatus == 2 else "done" if r.status == "Completed" else "planned"
	return rows


@frappe.whitelist()
def procedures(patient=None, status=None, limit=100):
	"""Recorded procedures, newest first (cancelled ones included). status: planned | done | cancelled."""
	_require_staff()
	_require_health()
	filters = {"docstatus": ["in", [1, 2]]}
	if patient:
		filters["patient"] = patient
	if status == "done":
		filters["docstatus"] = 1
		filters["status"] = "Completed"
	elif status == "planned":
		filters["status"] = ["in", ["Pending", "In Progress"]]
	elif status == "cancelled":
		filters["docstatus"] = 2
	return _procedure_rows(filters, limit)


def _complete(cp):
	"""Take the procedure's medicines out of the pharmacy store, then mark it completed."""
	if cp.status == "Completed":
		return frappe.db.get_value("Stock Entry", {"custom_clinical_procedure": cp.name, "docstatus": 1}, "name")
	entry = None
	patient_name = cp.patient_name or frappe.db.get_value("Patient", cp.patient, "patient_name")
	needed = {}
	for row in cp.items:
		needed[row.item_code] = needed.get(row.item_code, 0) + flt(row.qty)
	if cp.consume_stock and needed:
		lines = []
		for code, qty in needed.items():
			try:
				plan = _allocate(code, qty, expired=False)
			except frappe.ValidationError as e:
				frappe.clear_last_message()
				frappe.throw(_("{0}: {1}").format(frappe.db.get_value("Item", code, "item_name"), str(e)))
			lines += [{"item_code": code, "qty": q, "s_warehouse": cp.warehouse, "use_serial_batch_fields": 1, "batch_no": b}
					  for b, q in plan]
		se = _submit(frappe.get_doc({
			"doctype": "Stock Entry", "owner": _owner(), "stock_entry_type": "Material Issue", "company": cp.company,
			"set_posting_time": 1, "posting_date": getdate(cp.start_date or nowdate()), "from_warehouse": cp.warehouse,
			"custom_reason": PROCEDURE_REASON, "custom_recipient": patient_name, "custom_clinical_procedure": cp.name,
			"items": lines,
		}))
		entry = se.name
	details = "\n".join(f"{r.item_name}: {frappe.format(r.qty)} {r.stock_uom}" for r in cp.items)
	cp.db_set({"status": "Completed", "actual_end_datetime": now_datetime(), "consumption_details": details})
	return entry


@frappe.whitelist(methods=["POST"])
@_writes(admin=False)
def record_procedure(patient, template, items=None, date=None, notes=None, complete=1, client_id=None):
	"""Record a procedure for a patient. With `complete`, its medicines leave the store right away."""
	_require_health()
	if client_id and (done := frappe.db.get_value("Clinical Procedure", {"custom_client_id": client_id}, "name")):
		return {"name": done, "duplicate": True}
	if not frappe.db.exists("Patient", patient):
		frappe.throw(_("Please choose a patient"))
	if not frappe.db.exists("Clinical Procedure Template", template):
		frappe.throw(_("Please choose a procedure"))
	rows = _items_arg(items) if items is not None else [
		{"item_code": r.medicine, "item_name": r.medicine_name, "qty": r.qty, "uom": r.unit, "stock_uom": r.unit,
		 "conversion_factor": 1, "transfer_qty": r.qty} for r in _item_rows(template, "Clinical Procedure Template")]
	date = getdate(date or nowdate())
	if date > getdate():
		frappe.throw(_("The date cannot be in the future"))
	cp = frappe.get_doc({
		"doctype": "Clinical Procedure", "owner": _owner(), "patient": patient, "procedure_template": template,
		"patient_name": frappe.db.get_value("Patient", patient, "patient_name"),
		"company": _company(), "warehouse": _warehouse(), "start_date": date, "consume_stock": 1 if rows else 0,
		"notes": notes or "", "items": rows, "custom_client_id": client_id,
	})
	cp.flags.ignore_permissions = True
	cp.insert()
	cp.submit()
	_keep_owner(cp)
	entry = _complete(cp) if cint(complete) else None
	return {"name": cp.name, "stock_entry": entry, "status": frappe.db.get_value("Clinical Procedure", cp.name, "status")}


@frappe.whitelist(methods=["POST"])
@_writes(admin=False)
def complete_procedure(name):
	"""Finish a planned procedure: its medicines leave the store now."""
	_require_health()
	cp = frappe.get_doc("Clinical Procedure", name)
	if cp.docstatus != 1 or cp.status == "Cancelled":
		frappe.throw(_("This procedure was cancelled"))
	return {"name": cp.name, "stock_entry": _complete(cp)}


@frappe.whitelist(methods=["POST"])
@_writes(admin=False)
def cancel_procedure(name, reason=None):
	"""Cancel a procedure (pharmacy staff and administrators).

	A planned one is simply cancelled. A completed one needs a reason: its stock movement is cancelled
	too, so the medicines go back into the same batches. The original movement stays in the history,
	marked as cancelled, and the procedure stays in the patient's file as cancelled.
	"""
	_require_health()
	cp = frappe.get_doc("Clinical Procedure", name)
	if cp.docstatus == 2:
		frappe.throw(_("This procedure is already cancelled"))
	reason = (reason or "").strip()
	completed = cp.status == "Completed"
	if completed and not reason:
		frappe.throw(_("Please give the reason for cancelling this procedure"))
	if completed:
		for se in frappe.get_all("Stock Entry", filters={"custom_clinical_procedure": cp.name, "docstatus": 1}, pluck="name"):
			entry = frappe.get_doc("Stock Entry", se)
			entry.flags.ignore_permissions = True
			entry.cancel()
	cp.flags.ignore_permissions = True
	cp.cancel()
	cp.db_set({"custom_cancel_reason": reason, "custom_cancelled_by": _owner()}, update_modified=False)
	return {"name": cp.name, "stock_returned": completed}


def care_summary():
	"""Numbers and latest procedures for the dashboard."""
	month = nowdate()[:8] + "01"
	week = frappe.utils.add_days(nowdate(), -6)
	done = {"docstatus": 1, "status": "Completed"}
	by_day = dict(frappe.db.sql(
		"""select start_date, count(*) from `tabClinical Procedure`
		where docstatus = 1 and status = 'Completed' and start_date >= %s group by start_date""", week))
	return {
		"patients": frappe.db.count("Patient", {"status": "Active"}),
		"new_patients": frappe.db.count("Patient", {"status": "Active", "creation": [">=", month]}),
		"procedures_month": frappe.db.count("Clinical Procedure", {**done, "start_date": [">=", month]}),
		"planned": frappe.db.count("Clinical Procedure", {"docstatus": 1, "status": ["in", ["Pending", "In Progress"]]}),
		"week": [{"date": str(frappe.utils.add_days(week, i)), "count": by_day.get(getdate(frappe.utils.add_days(week, i)), 0)}
				 for i in range(7)],
		"recent": _procedure_rows({"docstatus": 1}, limit=5),
		"top_templates": frappe.db.sql(
			"""select procedure_template as name, count(*) as n from `tabClinical Procedure`
			where docstatus = 1 and status = 'Completed' and start_date >= %s group by procedure_template order by n desc limit 4""",
			month, as_dict=True),
	}
