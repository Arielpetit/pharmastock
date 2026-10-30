<p align="center"><img src="docs/logo.png" alt="Pharmastock" width="380"></p>

# PharmaStock

Simple medicine stock management for health centers, built on ERPNext Stock.
Pharmacy staff use a clean installable web app (PWA) at `/pharmacy`; ERPNext keeps the
stock records underneath. English and French.

| | |
|---|---|
| **Dashboard** | stock figures, 14-day activity, low stock, expiring batches, recent movements |
| **Medicines** | list with search, category, status and expiry filters; add a medicine with its first stock; **+ Stock** on every row |
| **Medicine page** | stock, minimum, nearest expiry, location, batches (oldest first), full history |
| **Give out stock** | medicine, quantity, reason, patient; always takes the earliest *valid* batch, never expired stock to patients |
| **Stock requests** | staff ask, administrators approve or reject; low stock creates requests automatically |
| **Reports** | movements, expiry, stock levels; download for Excel, print |
| **Staff** (admin) | add people, give the Staff or Administrator role, reset passwords, disable |
| **Offline** | the app opens without internet; stock in/out and requests made offline are sent later, exactly once |

## Design

Soft and calm: warm paper background, white cards, midnight-ink pill buttons, one apothecary green.
Newsreader (serif) for titles and figures, Figtree for text, IBM Plex Mono only for lot numbers and
expiry stamps, printed like on a medicine box. The signature is the **blister pack**: the logo is a
blister with one pill taken, and every medicine's stock is shown as a blister strip (filled pockets
against three times the minimum level). Fonts are bundled, so the look holds offline.
Screenshots: `docs/design/`.

## How it fits together

```
PWA (Vue 3 + frappe-ui)  →  pharmastock.api (Python, in the site)  →  ERPNext Stock  →  database
/pharmacy                    checks the pharmacy role, one call per action
```

- **Roles**: `Pharmacy Staff` and `Pharmacy Admin`. Neither has access to the ERPNext desk; the API
  does the stock work on their behalf after checking the role, and every record keeps the real user.
- **ERPNext pieces used**: Item (medicine), Batch (lot + expiry), Warehouse "Pharmacy", Stock Entry
  (Material Receipt / Material Issue), Material Request (stock request), Stock Ledger (history).
- **Setup on install** (`pharmastock/setup/install.py`): roles, custom fields, medicine categories,
  units, bell notifications, batch settings, and the "Pharmacy" store for the default company.

### Patients and procedures (Frappe Health)

`pharmastock/health.py` adds the care side, stored in Frappe Health (`healthcare` app):

- **Medicine ↔ Medication**: every medicine the pharmacy adds is an ERPNext Item *and* a Frappe Health
  Medication linked to it (same name, category = medication class, strength parsed from "500mg").
  Editing, archiving or deleting the medicine updates the Medication. Existing medicines are synced
  on `bench migrate`.
- **Patients**: registered from the app (`/pharmacy/patients`) as Frappe Health Patients.
- **Procedure types**: Clinical Procedure Templates with the medicines they use each time.
- **Procedures**: a Clinical Procedure for a patient. *Done now* takes its medicines out of the
  Pharmacy store right away (valid batches, earliest expiry first; stock movement reason
  "Used in a procedure", linked to the procedure); *Planned* waits until it is marked as done.

## Requirements

Frappe / ERPNext / Frappe Health (`healthcare`) **version 16**. A company must exist (ERPNext setup wizard done) before install,
otherwise create the store afterwards:

```bash
bench --site <site> execute pharmastock.setup.install.create_warehouse
```

If the company uses perpetual inventory, it needs a *Default Inventory Account* (Company settings),
or stock postings fail. The installer warns about this but does not change accounting settings.

## Install on a site

```bash
bench get-app https://github.com/<you>/pharmastock --branch main
bench --site <site> install-app pharmastock
```

On Frappe Cloud / Press: add the GitHub repo under the bench's **Apps**, deploy, then install the
app on the site. The built front end is committed (`pharmastock/public/frontend`,
`pharmastock/www/pharmacy.html`), so the server needs no Node build step.

Docker (`frappe_docker`): add the repo to `apps.json` and rebuild the image.

Then create users in the app (**Staff** page, as an administrator) or give them the
`Pharmacy Staff` / `Pharmacy Admin` role. Users open `https://<site>/pharmacy`.

## Develop

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev            # http://localhost:8090/pharmacy, API proxied to SITE_URL (default http://localhost:8088)
npm run build          # writes pharmastock/public/frontend and pharmastock/www/pharmacy.html — commit both
npm run icons          # re-renders PWA icons from public/logo-mark.svg
```

Translations: English is in the code, French in `frontend/src/fr.js`.

## Tests

```bash
# API: 23 checks — stock in/out, earliest expiry first, refusals, duplicate protection, requests, permissions
python3 tests/api_smoke.py http://localhost:8088 <staff-email> <staff-pw> <admin-email> <admin-pw>

# Browser (headless Chrome, needs puppeteer-core): 21 checks — full staff and admin journeys,
# PWA install, offline use and sync, mobile and French; screenshots in docs/screenshots
node tests/e2e.mjs http://localhost:8088 <staff-email> <staff-pw> <admin-email> <admin-pw> docs/screenshots

# Frappe Health: 17 checks — patient, procedure type, done/planned procedures and the stock they use
python3 tests/health_smoke.py http://localhost:8088 <staff-email> <staff-pw>
```

## Files

```
pharmastock/api.py               server API used by the app
pharmastock/setup/install.py     install / migrate setup
pharmastock/service_worker.py    serves the PWA service worker at /pharmacy/sw.js
pharmastock/www/pharmacy.*       the app page (built)
frontend/                        Vue 3 + frappe-ui source
docs/screenshots/                screenshots from the browser test
```
