<template>
  <div>
    <PageHeader :title="t('Reports')" :subtitle="t('Movements, expiry and stock levels. Download any report for Excel.')">
      <template #actions>
        <Button size="md" icon-left="lucide-printer" :label="t('Print')" @click="print" />
        <Button size="md" icon-left="lucide-download" :label="t('Download (Excel)')" :disabled="!current.length" @click="exportCsv" />
      </template>
    </PageHeader>

    <div class="mb-4 inline-flex rounded-4 bg-surface-gray-2 p-1 print:hidden">
      <button v-for="x in tabs" :key="x.value" class="flex items-center gap-2 rounded-3 px-3 py-1.5 text-sm font-medium transition"
        :class="tab === x.value ? 'bg-surface-base text-ink-gray-9 shadow-sm' : 'text-ink-gray-6 hover:text-ink-gray-8'" @click="tab = x.value">
        <span :class="x.icon" class="size-4" /> <span class="hidden sm:inline">{{ t(x.label) }}</span>
      </button>
    </div>

    <!-- filters -->
    <div class="card mb-4 flex flex-wrap items-end gap-3 p-3 print:hidden">
      <template v-if="tab === 'movements'">
        <FormControl v-model="from" type="date" format="D MMM YYYY" :label="t('From')" size="md" class="w-40" />
        <FormControl v-model="to" type="date" format="D MMM YYYY" :label="t('To')" size="md" class="w-40" />
        <FormControl v-model="kind" type="select" :label="t('Type')" size="md" class="w-40"
          :options="[{ label: t('All'), value: '' }, { label: t('Stock in'), value: 'in' }, { label: t('Stock out'), value: 'out' }]" />
        <div class="min-w-56 flex-1"><MedicinePicker v-model="medicine" :label="t('Medicine')" /></div>
        <Button v-if="medicine" size="md" variant="ghost" icon-left="lucide-x" :label="t('Any medicine')" @click="medicine = null" />
      </template>
      <template v-else-if="tab === 'expiry'">
        <FormControl v-model="days" type="select" :label="t('Expiring within')" size="md" class="w-48"
          :options="[30, 60, 90, 180, 365].map((d) => ({ label: t('{0} days', d), value: String(d) }))" />
      </template>
      <template v-else>
        <FormControl v-model="stockFilter" type="select" :label="t('Show')" size="md" class="w-56"
          :options="[{ label: t('All medicines'), value: 'all' }, { label: t('Low or out of stock'), value: 'low' }]" />
      </template>
      <div class="ml-auto self-center text-sm text-ink-gray-5">{{ t('{0} rows', current.length) }}</div>
    </div>

    <div class="card overflow-x-auto">
      <div v-if="loading" class="p-10 text-center"><LoadingIndicator class="mx-auto size-5 text-ink-gray-5" /></div>
      <EmptyState v-else-if="!current.length" icon="lucide-file-search" :title="t('Nothing to show')" :text="t('Change the filters to see more.')" />

      <table v-else-if="tab === 'movements'" class="w-full min-w-[720px] text-left text-sm">
        <thead class="bg-surface-gray-1 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
          <tr><th class="px-4 py-2.5">{{ t('Date') }}</th><th class="px-4 py-2.5">{{ t('Medicine') }}</th><th class="px-4 py-2.5 text-right">{{ t('Quantity') }}</th>
            <th class="px-4 py-2.5">{{ t('Reason') }}</th><th class="px-4 py-2.5">{{ t('Lot') }}</th><th class="px-4 py-2.5">{{ t('By') }}</th>
            <th class="px-4 py-2.5 text-right">{{ t('Balance') }}</th></tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1">
          <tr v-for="(r, i) in movements" :key="i">
            <td class="whitespace-nowrap px-4 py-2.5 text-ink-gray-6">{{ date(r.date) }}</td>
            <td class="px-4 py-2.5 font-medium text-ink-gray-9">{{ r.medicine_name }}</td>
            <td class="px-4 py-2.5 text-right font-semibold tabular" :class="r.direction === 'in' ? 'text-teal-700' : 'text-ink-gray-8'">
              {{ r.direction === 'in' ? '+' : '−' }}{{ num(r.qty) }}</td>
            <td class="px-4 py-2.5 text-ink-gray-7">{{ t(r.reason || '') }}<span v-if="r.recipient" class="text-ink-gray-5"> · {{ r.recipient }}</span></td>
            <td class="px-4 py-2.5 text-ink-gray-6">{{ r.batch || '—' }}</td>
            <td class="px-4 py-2.5 text-ink-gray-6">{{ r.by }}</td>
            <td class="px-4 py-2.5 text-right tabular text-ink-gray-6">{{ num(r.balance) }}</td>
          </tr>
        </tbody>
      </table>

      <table v-else-if="tab === 'expiry'" class="w-full min-w-[640px] text-left text-sm">
        <thead class="bg-surface-gray-1 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
          <tr><th class="px-4 py-2.5">{{ t('Medicine') }}</th><th class="px-4 py-2.5">{{ t('Lot') }}</th><th class="px-4 py-2.5">{{ t('Expiry date') }}</th>
            <th class="px-4 py-2.5">{{ t('Time left') }}</th><th class="px-4 py-2.5 text-right">{{ t('Quantity') }}</th><th class="px-4 py-2.5">{{ t('Location') }}</th></tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1">
          <tr v-for="r in expiry" :key="r.batch" :class="r.expired && 'bg-red-50/50'">
            <td class="px-4 py-2.5 font-medium text-ink-gray-9">{{ r.medicine_name }}</td>
            <td class="px-4 py-2.5 text-ink-gray-6">{{ r.batch }}</td>
            <td class="px-4 py-2.5 text-ink-gray-7">{{ date(r.expiry_date) }}</td>
            <td class="px-4 py-2.5"><ExpiryChip :date="r.expiry_date" :days="r.days_left" :show-date="false" class="!items-start" /></td>
            <td class="px-4 py-2.5 text-right font-semibold tabular text-ink-gray-9">{{ num(r.qty) }} <span class="font-normal text-ink-gray-5">{{ t(r.unit) }}</span></td>
            <td class="px-4 py-2.5 text-ink-gray-6">{{ r.location || '—' }}</td>
          </tr>
        </tbody>
      </table>

      <table v-else class="w-full min-w-[640px] text-left text-sm">
        <thead class="bg-surface-gray-1 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
          <tr><th class="px-4 py-2.5">{{ t('Medicine') }}</th><th class="px-4 py-2.5">{{ t('Category') }}</th><th class="px-4 py-2.5 text-right">{{ t('In stock') }}</th>
            <th class="px-4 py-2.5 text-right">{{ t('Minimum') }}</th><th class="px-4 py-2.5">{{ t('Nearest expiry') }}</th><th class="px-4 py-2.5">{{ t('Status') }}</th></tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1">
          <tr v-for="r in stock" :key="r.code">
            <td class="px-4 py-2.5 font-medium text-ink-gray-9">{{ r.name }}</td>
            <td class="px-4 py-2.5 text-ink-gray-6">{{ t(r.category) }}</td>
            <td class="px-4 py-2.5 text-right font-semibold tabular text-ink-gray-9">{{ num(r.stock) }} <span class="font-normal text-ink-gray-5">{{ t(r.unit) }}</span></td>
            <td class="px-4 py-2.5 text-right tabular text-ink-gray-6">{{ num(r.minimum) }}</td>
            <td class="px-4 py-2.5 text-ink-gray-6">{{ r.nearest_expiry ? date(r.nearest_expiry) : '—' }}</td>
            <td class="px-4 py-2.5"><StatusBadge :status="r.status" /></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, FormControl, LoadingIndicator, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import ExpiryChip from '@/components/ExpiryChip.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import MedicinePicker from '@/components/MedicinePicker.vue'
import { get } from '@/api'
import { t } from '@/i18n'
import { date, downloadCsv, num, today } from '@/format'
import { ui } from '@/ui'

const route = useRoute()
const router = useRouter()
const tabs = [
  { value: 'movements', label: 'Movements', icon: 'lucide-arrow-left-right' },
  { value: 'expiry', label: 'Expiry', icon: 'lucide-calendar-clock' },
  { value: 'stock', label: 'Stock levels', icon: 'lucide-boxes' },
]
const tab = ref(route.query.tab || 'movements')
const monthAgo = () => { const d = new Date(); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10) }
const from = ref(monthAgo())
const to = ref(today())
const kind = ref('')
const medicine = ref(null)
const days = ref('90')
const stockFilter = ref('all')
const movements = ref([])
const expiry = ref([])
const allStock = ref([])
const loading = ref(false)

const stock = computed(() => (stockFilter.value === 'low' ? allStock.value.filter((r) => r.is_low || r.is_out) : allStock.value))
const current = computed(() => (tab.value === 'movements' ? movements.value : tab.value === 'expiry' ? expiry.value : stock.value))

async function load() {
  loading.value = true
  try {
    if (tab.value === 'movements')
      movements.value = await get('movements', { from_date: from.value, to_date: to.value, kind: kind.value, medicine: medicine.value, limit: 1000 })
    else if (tab.value === 'expiry') expiry.value = await get('expiring', { days: days.value })
    else allStock.value = await get('medicines')
  } catch (e) {
    toast.error(e.message)
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  if (tab.value === 'movements')
    downloadCsv(`movements_${from.value}_${to.value}.csv`,
      [t('Date'), t('Medicine'), t('Direction'), t('Quantity'), t('Reason'), t('Recipient'), t('Lot'), t('By'), t('Balance')],
      movements.value.map((r) => [r.date, r.medicine_name, r.direction === 'in' ? t('In') : t('Out'), r.qty, t(r.reason || ''), r.recipient, r.batch, r.by, r.balance]))
  else if (tab.value === 'expiry')
    downloadCsv(`expiry_${today()}.csv`, [t('Medicine'), t('Lot'), t('Expiry date'), t('Days left'), t('Quantity'), t('Unit'), t('Location')],
      expiry.value.map((r) => [r.medicine_name, r.batch, r.expiry_date, r.days_left, r.qty, r.unit, r.location]))
  else
    downloadCsv(`stock_${today()}.csv`, [t('Medicine'), t('Category'), t('In stock'), t('Unit'), t('Minimum'), t('Nearest expiry'), t('Status')],
      stock.value.map((r) => [r.name, t(r.category), r.stock, r.unit, r.minimum, r.nearest_expiry, r.status]))
}

const print = () => window.print()

watch(tab, () => router.replace({ query: { tab: tab.value } }))
watch([tab, from, to, kind, medicine, days], load, { immediate: true })
watch(() => ui.version, load)
</script>
