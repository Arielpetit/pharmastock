// End-to-end test of the care flow (patients, procedure types, procedures) in headless Chrome.
//
// Usage: node tests/care_e2e.mjs <site-url> <staff-email> <staff-pw> <admin-email> <admin-pw> [screenshot-dir]
// Needs `puppeteer-core` and Google Chrome. Creates a medicine "Care Paracetamol <random>", a patient, a procedure type and procedures.
import puppeteer from 'puppeteer-core'
import fs from 'fs'

const [SITE, S_USER, S_PW, A_USER, A_PW, SHOTS = 'screenshots'] = process.argv.slice(2)
fs.mkdirSync(SHOTS, { recursive: true })
const MED = `Care Paracetamol ${Math.random().toString(36).slice(2, 6)}`
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
let passed = 0
const errors = []

async function check(label, ok, extra = '') {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${label}${extra ? ' — ' + extra : ''}`)
  if (!ok) {
    try {
      await current.screenshot({ path: `${SHOTS}/FAILED.png` })
      console.log((await current.evaluate(() => document.body.innerText)).slice(0, 1200))
    } catch {}
    throw new Error(`failed: ${label}`)
  }
  passed++
}

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--lang=en-GB'],
})

async function newPage(width = 1366, height = 860) {
  const ctx = await browser.createBrowserContext()
  const page = await ctx.newPage()
  await page.setViewport({ width, height, deviceScaleFactor: 1 })
  page.on('console', (m) => m.type() === 'error' && !/socket\.io|favicon/i.test(m.text()) && errors.push(m.text()))
  page.on('pageerror', (e) => errors.push(String(e)))
  return page
}

// ---- helpers that drive the real UI ------------------------------------------------------
const byText = (page, text, tag = '*') =>
  page.waitForSelector(`::-p-xpath(//${tag}[normalize-space(.)=${JSON.stringify(text)} or .//text()[normalize-space(.)=${JSON.stringify(text)}]][not(ancestor::*[@aria-hidden="true"])])`, { visible: true, timeout: 10000 })
async function click(page, text, tag = 'button') {
  const el = await byText(page, text, tag)
  await el.click()
  await sleep(350)
}
async function field(page, label, scope = 'body') {
  return page.evaluateHandle((label, scope) => {
    const root = document.querySelector(scope === 'dialog' ? '[role="dialog"]' : 'body')
    const labels = [...root.querySelectorAll('label, .text-xs, div, span')].filter((l) => !l.closest('aside, nav') && l.childElementCount <= 2 && l.textContent.replace('*', '').trim().startsWith(label) && l.textContent.length < label.length + 40)
    for (const l of labels) {
      let el = l
      for (let i = 0; i < 5 && el; i++, el = el.parentElement) {
        const input = el.querySelector('input:not([type="hidden"]), textarea, button[role="combobox"]')
        if (input) return input
      }
    }
    return null
  }, label, scope)
}
async function fill(page, label, value, scope = 'body') {
  const h = await field(page, label, scope)
  const ok = await page.evaluate((el, value) => {
    if (!el) return false
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype
    el.focus()
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value)
    el.dispatchEvent(new Event('input', { bubbles: true }))
    el.dispatchEvent(new Event('change', { bubbles: true }))
    el.blur() // date pickers commit typed text on blur
    return true
  }, h, String(value))
  if (!ok) throw new Error(`field not found: ${label}`)
}
async function choose(page, label, option, scope = 'body') {
  const h = await field(page, label, scope)
  await h.click()
  await sleep(300)
  const opt = await page.waitForSelector(`::-p-xpath(//*[@role="option"][.//text()[normalize-space(.)=${JSON.stringify(option)}]])`, { visible: true, timeout: 5000 })
  await opt.click()
  await sleep(300)
}
async function pickMedicine(page, name, scope = 'body') {
  const h = await field(page, 'Medicine', scope)
  await h.click()
  await sleep(200)
  await page.keyboard.type(name.slice(0, 12))
  const opt = await page.waitForSelector(`::-p-xpath(//*[@role="option"][.//text()[normalize-space(.)=${JSON.stringify(name)}]])`, { visible: true, timeout: 8000 })
  await opt.click()
  await sleep(400)
}
const text = (page) => page.evaluate(() => document.querySelector('main')?.innerText || document.body.innerText)
async function waitText(page, needle, timeout = 10000) {
  try {
    await page.waitForFunction((n) => (document.querySelector('main')?.innerText || document.body.innerText).includes(n), { timeout }, needle)
  } catch (e) {
    await page.screenshot({ path: `${SHOTS}/FAILED.png` })
    console.log(`Did not find "${needle}" on ${page.url()}. Page text:\n` + (await page.evaluate(() => document.body.innerText)).slice(0, 1200))
    console.log('Console errors:', [...new Set(errors)].join(' | '))
    throw e
  }
}
const api = (page, method, args = {}) =>
  page.evaluate(async (method, args) => {
    const r = await fetch(`/api/method/pharmastock.api.${method}?${new URLSearchParams(args)}`)
    return (await r.json()).message
  }, method, args)
async function login(page, user, pw) {
  await page.goto(`${SITE}/pharmacy/login`, { waitUntil: 'networkidle0' })
  await fill(page, 'Email', user)
  await fill(page, 'Password', pw)
  await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), click(page, 'Log in')])
  await waitText(page, 'Good')
}
const shot = (page, name) => page.screenshot({ path: `${SHOTS}/${name}.png` })

let current
process.on('unhandledRejection', async (e) => {
  console.log('ERROR', e.message)
  try {
    await current.screenshot({ path: `${SHOTS}/FAILED.png` })
    console.log('PAGE TEXT:', (await current.evaluate(() => document.body.innerText)).slice(0, 1500))
  } catch {}
  console.log('Console errors:', [...new Set(errors)].join(' | '))
  process.exit(1)
})


const tag = MED.slice(-4)
const PAT = `Awa Ndong${tag}`
const TPL = `Wound dressing ${tag}`
const staff = await newPage()
current = staff
await login(staff, S_USER, S_PW)

// 1. the pharmacist adds a medicine (Item + batch + stock entry, and a Medication in Frappe Health)
await click(staff, 'Medicines', 'a')
await waitText(staff, 'medicines on your list')
await click(staff, 'New medicine')
await fill(staff, 'Medicine name', MED, 'dialog')
await choose(staff, 'Category', 'Analgesic', 'dialog')
await choose(staff, 'Dosage form', 'Tablet', 'dialog')
await fill(staff, 'Strength', '500mg', 'dialog')
await choose(staff, 'Counted in', 'Tablet', 'dialog')
await fill(staff, 'Minimum stock', '10', 'dialog')
await fill(staff, 'Quantity received', '100', 'dialog')
await fill(staff, 'Expiry date', '2029-05-31', 'dialog')
await click(staff, 'Add medicine')
await waitText(staff, 'Batches on the shelf')
let med = await api(staff, 'medicine', { code: MED })
await check('1. medicine added with 100 in stock', med.stock === 100)
await shot(staff, 'care-1-medicine')

// 2. register a patient
await click(staff, 'Patients', 'a')
await waitText(staff, 'patients registered')
await click(staff, 'New patient', 'button')
await fill(staff, 'First name', 'Awa', 'dialog')
await fill(staff, 'Last name', `Ndong${tag}`, 'dialog')
await click(staff, 'Female', '*[@role="dialog"]//button')
await fill(staff, 'Date of birth', '1991-03-14', 'dialog')
await fill(staff, 'Phone', '+237 677 00 11 22', 'dialog')
await choose(staff, 'Blood group', 'O+', 'dialog')
await fill(staff, 'Allergies', 'Penicillin', 'dialog')
await shot(staff, 'care-2-new-patient')
await click(staff, 'Register patient')
await waitText(staff, 'Care received')
await check('2. patient registered and opened', (await text(staff)).includes(PAT) && (await text(staff)).includes('Penicillin'))
await shot(staff, 'care-3-patient')

// 3. procedure type: a wound dressing that uses 2 tablets
await click(staff, 'Procedures', 'a')
await waitText(staff, 'Care given to patients')
await click(staff, 'Procedure types', 'button')
await click(staff, 'New procedure type')
await fill(staff, 'Name', TPL, 'dialog')
await fill(staff, 'Description', 'Clean the wound and cover it', 'dialog')
const combo = await staff.waitForSelector('[role="dialog"] input[role="combobox"], [role="dialog"] button[role="combobox"]', { visible: true })
await combo.click()
await sleep(200)
await staff.keyboard.type(MED.slice(0, 12))
const opt = await staff.waitForSelector(`::-p-xpath(//*[@role="option"][.//text()[normalize-space(.)=${JSON.stringify(MED)}]])`, { visible: true, timeout: 8000 })
await opt.click()
await sleep(300)
const qty = await staff.waitForSelector('[role="dialog"] input[type="number"]', { visible: true })
await qty.click({ clickCount: 3 })
await staff.keyboard.type('2')
await shot(staff, 'care-4-procedure-type')
await click(staff, 'Create')
await waitText(staff, TPL)
await check('3. procedure type saved with its medicine', (await text(staff)).includes(MED) && (await text(staff)).includes('× 2'))
await shot(staff, 'care-5-types')

// 4. record the procedure for the patient: done now, takes 2 tablets out of the stock
await click(staff, 'Record a procedure', 'button')
await sleep(600)
const patBox = await field(staff, 'Patient', 'dialog')
await patBox.click()
await sleep(200)
await staff.keyboard.type('Awa Ndong')
const patOpt = await staff.waitForSelector(`::-p-xpath(//*[@role="option"][.//text()[contains(., ${JSON.stringify(PAT)})]])`, { visible: true, timeout: 8000 })
await patOpt.click()
await sleep(300)
await click(staff, TPL, '*[@role="dialog"]//button')
await sleep(300)
await fill(staff, 'Notes', 'Left leg, healing well', 'dialog')
await shot(staff, 'care-6-record')
await click(staff, 'Record and take from stock')
await sleep(2000)
med = await api(staff, 'medicine', { code: MED })
await check('4. procedure done: stock 100 - 2 = 98', med.stock === 98)
await check('4. stock movement says "Used in a procedure" for the patient',
  med.movements.some((m) => m.reason === 'Used in a procedure' && m.recipient === PAT && m.qty === 2))

// 5. a planned procedure: nothing leaves the stock until it is marked done
await click(staff, 'Record a procedure', 'button')
await sleep(600)
const patBox2 = await field(staff, 'Patient', 'dialog')
await patBox2.click()
await sleep(200)
await staff.keyboard.type('Awa Ndong')
await (await staff.waitForSelector(`::-p-xpath(//*[@role="option"][.//text()[contains(., ${JSON.stringify(PAT)})]])`, { visible: true, timeout: 8000 })).click()
await sleep(300)
await click(staff, TPL, '*[@role="dialog"]//button')
await click(staff, 'Planned', '*[@role="dialog"]//button')
await click(staff, 'Save as planned')
await sleep(1800)
med = await api(staff, 'medicine', { code: MED })
await check('5. planned procedure does not touch the stock (still 98)', med.stock === 98)
await click(staff, 'Recorded', 'button')
await click(staff, 'Planned', 'button')
const done = await staff.waitForSelector('::-p-xpath(//main//button[normalize-space(.)="Mark as done"])', { visible: true })
await done.click()
await sleep(500)
await click(staff, 'Mark as done', '*[@role="dialog"]//button')
await sleep(2000)
med = await api(staff, 'medicine', { code: MED })
await check('5. marking it done takes 2 more out (96)', med.stock === 96)

// 6. the patient file and the dashboard
await click(staff, 'Patients', 'a')
await waitText(staff, PAT)
await (await staff.waitForSelector(`::-p-xpath(//main//*[normalize-space(.)=${JSON.stringify(PAT)}])`, { visible: true })).click()
await waitText(staff, 'Care received')
await check('6. patient file shows both procedures', ((await text(staff)).match(new RegExp(TPL, 'g')) || []).length === 2)
await shot(staff, 'care-7-patient-file')
await click(staff, 'Dashboard', 'a')
await waitText(staff, 'Procedures this month')
await check('6. dashboard shows the care section', (await text(staff)).includes('Recent procedures') && (await text(staff)).includes(PAT))
await shot(staff, 'care-8-dashboard')

// 7. phone
const phone = await newPage(390, 844)
current = phone
await login(phone, S_USER, S_PW)
await phone.goto(`${SITE}/pharmacy/procedures`, { waitUntil: 'networkidle0' })
await waitText(phone, PAT)
await shot(phone, 'care-9-phone-procedures')
await phone.goto(`${SITE}/pharmacy/`, { waitUntil: 'networkidle0' })
await waitText(phone, 'Procedures this month')
await shot(phone, 'care-10-phone-dashboard')
await check('7. care screens render on a phone', true)

console.log(`\n${passed} checks passed`)
console.log(errors.length ? `Console errors:\n- ${[...new Set(errors)].join('\n- ')}` : 'No console errors')
await browser.close()
