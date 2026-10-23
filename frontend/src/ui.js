// Shared dialog state, so any page can open "Add stock", "New medicine" or "Request stock",
// and a counter pages watch to reload after a stock change.
import { reactive } from 'vue'

export const ui = reactive({
  version: 0,
  addStock: { open: false, medicine: null },
  medicine: { open: false, code: null },
  request: { open: false, medicine: null, qty: null },
  sync: { open: false },
})

export const changed = () => ui.version++
export const openAddStock = (medicine = null) => Object.assign(ui.addStock, { open: true, medicine })
export const openMedicine = (code = null) => Object.assign(ui.medicine, { open: true, code })
export const openRequest = (medicine = null, qty = null) => Object.assign(ui.request, { open: true, medicine, qty })
