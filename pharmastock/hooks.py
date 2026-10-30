app_name = "pharmastock"
app_title = "PharmaStock"
app_publisher = "NEURAX"
app_description = "Simple medicine stock management for health centers"
app_email = "dev@neurax.local"
app_license = "mit"

required_apps = ["frappe", "erpnext", "healthcare"]

after_install = "pharmastock.setup.install.after_install"
after_migrate = "pharmastock.setup.install.after_migrate"
setup_wizard_complete = "pharmastock.setup.install.after_setup_wizard"

# the app lives at /pharmacy; every sub-path is handled by the single-page app
website_route_rules = [{"from_route": "/pharmacy/<path:app_path>", "to_route": "pharmacy"}]

# serves the PWA service worker at /pharmacy/sw.js so it can control the whole app
page_renderer = ["pharmastock.service_worker.ServiceWorkerPage"]

# pharmacy users land in the app after logging in on the standard login page
role_home_page = {"Pharmacy Staff": "pharmacy", "Pharmacy Admin": "pharmacy"}

add_to_apps_screen = [
	{
		"name": "pharmastock",
		"logo": "/assets/pharmastock/images/logo-mark.svg",
		"title": "PharmaStock",
		"route": "/pharmacy",
	}
]
