"""Smoke test of patients and procedures (Frappe Health) against a running site.

Usage: python3 tests/health_smoke.py http://localhost:8088 <staff-email> <staff-pw>
Creates "ZZ Health Test <random>" medicine, a patient, a procedure template and two procedures.
"""
import http.cookiejar, json, os, sys, urllib.error, urllib.parse, urllib.request, uuid

BASE, S_USER, S_PW = sys.argv[1:4]


class Client:
	def __init__(self, user, pw):
		self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
		self.req("POST", "login", {"usr": user, "pwd": pw}, form=True)
		self.csrf = self.get("boot")["csrf_token"]

	def req(self, verb, method, data=None, form=False):
		# "boot" -> pharmastock.api.boot, "health.patients" -> pharmastock.health.patients
		path = method if method == "login" else f"pharmastock.{method}" if "." in method else f"pharmastock.api.{method}"
		url, body, headers = f"{BASE}/api/method/{path}", None, {}
		if os.environ.get("SITE_HOST"):
			headers["Host"] = os.environ["SITE_HOST"]
		if verb == "GET" and data:
			url += "?" + urllib.parse.urlencode(data)
		elif data is not None:
			body = urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
			headers["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
			if getattr(self, "csrf", None):
				headers["X-Frappe-CSRF-Token"] = self.csrf
		try:
			return json.loads(self.op.open(urllib.request.Request(url, body, headers, method=verb)).read()).get("message")
		except urllib.error.HTTPError as e:
			raw = e.read().decode()
			try:
				msg = json.loads(json.loads(raw).get("_server_messages", "[]"))[0]
				msg = json.loads(msg).get("message")
			except Exception:
				msg = raw[:300]
			raise AssertionError(f"{e.code} {msg}")

	def get(self, m, data=None):
		return self.req("GET", m, data)

	def post(self, m, data):
		return self.req("POST", m, data)


ok = 0


def check(label, cond):
	global ok
	print(("PASS " if cond else "FAIL ") + label)
	if not cond:
		raise SystemExit(1)
	ok += 1


def fails(label, fn, text):
	try:
		fn()
	except AssertionError as e:
		check(f"{label} ({e})", text.lower() in str(e).lower())
		return
	check(label + " (no error raised)", False)


staff = Client(S_USER, S_PW)
boot = staff.get("boot")
check("boot says Frappe Health is installed", boot["health"] is True)
check("boot lists sexes", "Female" in boot["options"]["genders"])

tag = uuid.uuid4().hex[:5]
med = f"ZZ Health Test {tag}"
staff.post("save_medicine", {"name": med, "category": "Analgesic", "unit": "Tablet", "form": "Tablet", "strength": "500mg",
							 "minimum": 5, "qty": 40, "expiry": "2030-01-31"})
stock = lambda: staff.get("medicine", {"code": med})["stock"]
check("medicine created with 40 in stock", stock() == 40)

# the patient
p = staff.post("health.save_patient", {"first_name": "Test", "last_name": f"Patient {tag}", "sex": "Female", "dob": "1990-05-01",
									   "mobile": "+237600000000", "blood_group": "O Positive"})
check("patient registered in Frappe Health", p["patient_name"] == f"Test Patient {tag}")
check("patient is in the list", any(r["name"] == p["name"] for r in staff.get("health.patients", {"search": tag})))
fails("a patient needs a sex", lambda: staff.post("health.save_patient", {"first_name": "X", "sex": ""}), "sex")

# the procedure template uses 3 tablets
tpl_name = f"ZZ Dressing {tag}"
tpl = staff.post("health.save_procedure_template", {"template": tpl_name, "description": "Test", "items": [{"medicine": med, "qty": 3}]})
listed = [t for t in staff.get("health.procedure_templates") if t["name"] == tpl["name"]]
check("template saved with its medicine", listed and listed[0]["items"][0]["qty"] == 3)
fails("template names are unique", lambda: staff.post("health.save_procedure_template", {"template": tpl_name, "items": []}), "already exists")

# done now: stock goes down by 3 (template) -> 37
done = staff.post("health.record_procedure", {"patient": p["name"], "template": tpl["name"], "complete": 1, "client_id": f"t-{tag}"})
check("procedure completed with a stock entry", done["status"] == "Completed" and done["stock_entry"])
check("stock went down by 3", stock() == 37)
again = staff.post("health.record_procedure", {"patient": p["name"], "template": tpl["name"], "complete": 1, "client_id": f"t-{tag}"})
check("same client_id is not recorded twice", again.get("duplicate") and stock() == 37)

# planned with edited quantity: nothing moves until completed
planned = staff.post("health.record_procedure", {"patient": p["name"], "template": tpl["name"], "complete": 0,
												  "items": [{"medicine": med, "qty": 5}]})
check("planned procedure does not move stock", planned["status"] == "Pending" and stock() == 37)
staff.post("health.complete_procedure", {"name": planned["name"]})
check("completing it takes 5 out", stock() == 32)

fails("cannot use more than in stock", lambda: staff.post("health.record_procedure", {
	"patient": p["name"], "template": tpl["name"], "items": [{"medicine": med, "qty": 999}]}), "not enough")
check("failed procedure left stock untouched", stock() == 32)

detail = staff.get("health.patient", {"name": p["name"]})
check("patient shows 2 completed procedures", len([x for x in detail["procedures"] if x["state"] == "done"]) == 2)
moves = staff.get("movements", {"medicine": med})
check("movement says 'Used in a procedure' with the patient", any(
	m["reason"] == "Used in a procedure" and m["recipient"] == p["patient_name"] for m in moves))

print(f"\n{ok} checks passed")
