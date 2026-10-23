<template>
  <div>
    <PageHeader :title="t('Give out stock')" :subtitle="t('Record medicine leaving the store, for example given to a patient.')" />

    <div class="grid gap-5 lg:grid-cols-5">
      <form class="card space-y-5 p-5 lg:col-span-3" @submit.prevent="save">
        <div>
          <MedicinePicker v-model="form.medicine" :label="t('Medicine')" required @select="(m) => (picked = m)" />
          <div v-if="picked" class="mt-2 flex flex-wrap items-center gap-2 text-sm">
            <span class="rounded-3 bg-surface-gray-2 px-2 py-0.5 text-ink-gray-7 tabular">
              {{ t('Available: {0} {1}', num(available), t(picked.unit)) }}
            </span>
            <span v-if="picked.expired_qty > 0" class="rounded-3 bg-red-50 px-2 py-0.5 text-red-700">
              {{ t('{0} expired (cannot be given to patients)', num(picked.expired_qty)) }}
            </span>
            <span v-if="picked.nearest_expiry" class="text-ink-gray-5">{{ t('Oldest valid batch expires {0}', date(picked.nearest_expiry)) }}</span>
          </div>
        </div>

        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ t('Quantity') }} <span class="text-ink-red-4">*</span></div>
          <div class="flex items-stretch gap-2">
            <button type="button" class="flex w-12 items-center justify-center rounded-4 border border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-2"
              :aria-label="t('Less')" @click="step(-1)"><span class="lucide-minus size-4" /></button>
            <input v-model.number="form.qty" type="number" min="1" inputmode="numeric"
              class="h-11 w-full flex-1 rounded-4 border border-outline-gray-2 bg-surface-base text-center text-xl font-semibold tabular text-ink-gray-9 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20" />
            <button type="button" class="flex w-12 items-center justify-center rounded-4 border border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-2"
              :aria-label="t('More')" @click="step(1)"><span class="lucide-plus size-4" /></button>
          </div>
          <div class="mt-2 flex flex-wrap gap-1.5">
            <button v-for="n in [1, 5, 10, 20, 30]" :key="n" type="button"
              class="rounded-3 border border-outline-gray-2 px-2.5 py-1 text-sm text-ink-gray-6 hover:border-teal-500 hover:text-teal-700"
              @click="form.qty = n">{{ n }}</button>
          </div>
        </div>

        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ t('Reason') }} <span class="text-ink-red-4">*</span></div>
          <div class="grid gap-2 sm:grid-cols-2">
            <button v-for="r in reasons" :key="r.value" type="button"
              class="flex items-center gap-2.5 rounded-4 border px-3 py-2.5 text-left text-sm transition"
              :class="form.reason === r.value ? 'border-teal-600 bg-teal-50 text-teal-900 ring-1 ring-teal-600' : 'border-outline-gray-2 text-ink-gray-7 hover:border-outline-gray-3'"
              @click="form.reason = r.value">
              <span :class="[r.icon, form.reason === r.value ? 'text-teal-700' : 'text-ink-gray-5']" class="size-4 shrink-0" />
              {{ t(r.value) }}
            </button>
          </div>
        </div>

        <FormControl v-model="form.recipient" :label="recipientLabel" size="md"
          :placeholder="form.reason === 'Dispensed to a patient' ? t('Patient name or file number') : t('Optional')" />

        <ErrorMessage :message="error" />
        <div class="flex justify-end gap-2 border-t border-outline-gray-1 pt-4">
          <Button size="lg" :label="t('Clear')" @click="reset" />
          <Button type="submit" size="lg" variant="solid" icon-left="lucide-check" :loading="saving" :label="t('Record stock out')"
            class="!bg-[#0f766e] hover:!bg-[#115e59]" />
        </div>
      </form>

      <Panel class="lg:col-span-2" :title="t('Given out recently')" icon="lucide-history" :count="recent.length || null">
        <EmptyState v-if="!recent.length" icon="lucide-hand-heart" :title="t('Nothing given out yet')" />
        <ul v-else class="divide-y divide-outline-gray-1">
          <li v-for="(x, i) in recent" :key="i" class="flex items-center gap-3 px-4 py-3">
            <div class="min-w-0 flex-1">
              <div class="truncate text-base font-medium text-ink-gray-9">{{ x.medicine_name }}</div>
              <div class="truncate text-xs text-ink-gray-5">{{ t(x.reason || '') }}<template v-if="x.recipient"> · {{ x.recipient }}</template></div>
            </div>
            <div class="text-right">
              <div class="text-base font-semibold tabular text-ink-gray-8">−{{ num(x.qty) }}</div>
              <div class="text-xs text-ink-gray-5">{{ shortDate(x.date) }}</div>
            </div>
          </li>
        </ul>
      </Panel>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Button, ErrorMessage, FormControl, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import Panel from '@/components/Panel.vue'
import EmptyState from '@/components/EmptyState.vue'
import MedicinePicker from '@/components/MedicinePicker.vue'
import { get, write } from '@/api'
import { t } from '@/i18n'
import { date, num, shortDate } from '@/format'
import { ui, changed } from '@/ui'

const route = useRoute()
const reasons = [
  { value: 'Dispensed to a patient', icon: 'lucide-user-round' },
  { value: 'Transfer to another store or department', icon: 'lucide-truck' },
  { value: 'Damaged stock', icon: 'lucide-package-x' },
  { value: 'Expired stock', icon: 'lucide-calendar-x' },
  { value: 'Other authorized adjustment', icon: 'lucide-sliders-horizontal' },
]
const blank = () => ({ medicine: route.query.medicine || null, qty: 1, reason: route.query.reason || 'Dispensed to a patient', recipient: '' })
const form = reactive(blank())
const picked = ref(null)
const saving = ref(false)
const error = ref('')
const recent = ref([])

const expiredReason = computed(() => form.reason === 'Expired stock')
const available = computed(() => (picked.value ? (expiredReason.value ? picked.value.expired_qty : picked.value.stock - picked.value.expired_qty) : 0))
const recipientLabel = computed(() =>
  form.reason === 'Dispensed to a patient' ? t('Patient') : form.reason.startsWith('Transfer') ? t('Store or department') : t('Note'))

const step = (d) => (form.qty = Math.max(1, (Number(form.qty) || 0) + d))
function reset() {
  Object.assign(form, { ...blank(), medicine: null })
  picked.value = null
  error.value = ''
}

async function save() {
  error.value = ''
  if (!form.medicine) return (error.value = t('Please choose a medicine.'))
  if (!(Number(form.qty) > 0)) return (error.value = t('Please enter a quantity above 0.'))
  if (picked.value && Number(form.qty) > available.value)
    return (error.value = expiredReason.value ? t('Only {0} expired units are in stock.', num(available.value))
      : t('Not enough valid stock. Only {0} available.', num(available.value)))
  saving.value = true
  try {
    const res = await write('give_out', { ...form }, t('Give out'))
    const name = picked.value?.name || form.medicine
    if (res.queued) toast.info(t('Saved offline'), { description: t('{0} × {1} will be sent when you are back online.', num(form.qty), name) })
    else toast.success(t('Stock out recorded'), { description: `${num(form.qty)} × ${name}` })
    reset()
    changed()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function loadRecent() {
  try {
    recent.value = await get('movements', { kind: 'out', limit: 12 })
  } catch {}
}
onMounted(loadRecent)
watch(() => ui.version, loadRecent)
</script>
