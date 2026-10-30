// Small helpers for patients and procedures.
import { t } from './i18n'

// "O Positive" -> "O+"
export const blood = (b) => (b ? b.replace(' Positive', '+').replace(' Negative', '−') : '')

export const ageLabel = (age) => (age === null || age === undefined ? '' : age < 1 ? t('under 1 year') : t('{0} years', age))

// "Female · 34 years · O+"
export const patientMeta = (p) => [p.sex ? t(p.sex) : '', ageLabel(p.age), blood(p.blood_group)].filter(Boolean).join(' · ')

// the medicines a procedure uses: "Paracetamol 500mg × 2, Gauze × 1"
export const usedLine = (items) => (items || []).map((i) => `${i.medicine_name} × ${i.qty}`).join(', ')

// one editable row of MedicineRows
let seq = 0
export const newRow = (medicine = null, qty = 1) => ({ key: `r${Date.now()}${seq++}`, medicine, qty })
