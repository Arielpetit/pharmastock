// English is written in the code; French comes from fr.js. Missing French keys fall back to English.
import { ref } from 'vue'
import dayjs from 'dayjs/esm'
import 'dayjs/esm/locale/fr'
import fr from './fr'

const saved = (() => {
  try {
    return localStorage.getItem('pharmastock.lang')
  } catch {
    return null
  }
})()

export const lang = ref(saved || ((navigator.language || 'en').startsWith('fr') ? 'fr' : 'en'))
document.documentElement.lang = lang.value
dayjs.locale(lang.value)

export function setLanguage(code) {
  lang.value = code && code.startsWith('fr') ? 'fr' : 'en'
  document.documentElement.lang = lang.value
  dayjs.locale(lang.value)
  try {
    localStorage.setItem('pharmastock.lang', lang.value)
  } catch {}
}

// ERPNext's own names that read badly in English
const en = { Nos: 'units' }

/** Translate, then fill {0}, {1}… with the extra arguments. */
export function t(text, ...args) {
  let out = (lang.value === 'fr' ? fr[text] : en[text]) || text
  args.forEach((a, i) => (out = out.replaceAll(`{${i}}`, a)))
  return out
}
