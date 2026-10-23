<template>
  <div>
    <PageHeader :title="t('Medicines')" :subtitle="rows ? t('{0} medicines on your list', rows.length) : ''">
      <template #actions>
        <Button size="md" icon-left="lucide-package-plus" :label="t('Add stock')" @click="openAddStock()" />
        <Button size="md" variant="solid" icon-left="lucide-plus" :label="t('New medicine')" class="!bg-[#0f766e] hover:!bg-[#115e59]"
          @click="openMedicine()" />
      </template>
    </PageHeader>

    <div class="card mb-4 flex flex-col gap-3 p-3 lg:flex-row lg:items-center">
      <div class="relative flex-1">
        <span class="lucide-search pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-gray-4" />
        <input v-model="search" type="search" :placeholder="t('Search by name…')"
          class="h-9 w-full rounded-4 border border-outline-gray-2 bg-surface-base pl-9 pr-3 text-base text-ink-gray-8 placeholder-ink-gray-4 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20" />
      </div>
      <div class="flex gap-2">
        <Select v-model="category" :options="categoryOptions" class="min-w-40 flex-1" size="md" />
        <div class="flex items-center gap-2">
          <FormControl v-model="expiryBefore" type="date" format="D MMM YYYY" size="md" :title="t('Expires before')" :placeholder="t('Expires before…')" class="w-44" />
        </div>
      </div>
    </div>

    <div class="scrollbar-none -mx-4 mb-4 flex gap-1.5 overflow-x-auto px-4 md:mx-0 md:px-0">
      <button v-for="s in statuses" :key="s.value" class="flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition"
        :class="status === s.value ? 'border-teal-600 bg-teal-600 text-white' : 'border-outline-gray-2 bg-surface-base text-ink-gray-6 hover:border-outline-gray-3'"
        @click="status = s.value">
        <span v-if="s.dot" class="size-1.5 rounded-full" :class="status === s.value ? 'bg-white' : s.dot" />
        {{ t(s.label) }}
        <span v-if="counts[s.value] !== undefined" class="tabular opacity-70">{{ counts[s.value] }}</span>
      </button>
    </div>

    <div v-if="!rows" class="card divide-y divide-outline-gray-1">
      <div v-for="i in 6" :key="i" class="h-16 animate-pulse" />
    </div>
    <div v-else-if="!filtered.length" class="card">
      <EmptyState icon="lucide-pill" :title="search || status !== 'all' || category || expiryBefore ? t('No medicine matches') : t('No medicines yet')"
        :text="search || status !== 'all' ? t('Try another search or filter.') : t('Add your first medicine to start tracking stock.')">
        <Button v-if="!search && status === 'all'" variant="solid" icon-left="lucide-plus" :label="t('New medicine')" @click="openMedicine()" />
      </EmptyState>
    </div>
    <template v-else>
      <!-- desktop table -->
      <div class="card hidden overflow-hidden md:block">
        <table class="w-full text-left">
          <thead class="bg-surface-gray-1 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            <tr>
              <th class="px-4 py-2.5">{{ t('Medicine') }}</th>
              <th class="px-4 py-2.5">{{ t('Category') }}</th>
              <th class="px-4 py-2.5 text-right">{{ t('In stock') }}</th>
              <th class="px-4 py-2.5">{{ t('Nearest expiry') }}</th>
              <th class="px-4 py-2.5">{{ t('Location') }}</th>
              <th class="px-4 py-2.5">{{ t('Status') }}</th>
              <th class="w-px px-4 py-2.5" />
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-gray-1">
            <tr v-for="m in filtered" :key="m.code" class="group cursor-pointer transition hover:bg-surface-gray-1" @click="open(m)">
              <td class="px-4 py-3">
                <div class="text-base font-medium text-ink-gray-9">{{ m.name }}</div>
                <div class="text-xs text-ink-gray-5">{{ [m.strength, t(m.form || '')].filter(Boolean).join(' · ') || '—' }}</div>
              </td>
              <td class="px-4 py-3 text-sm text-ink-gray-6">{{ t(m.category) }}</td>
              <td class="px-4 py-3 text-right">
                <div class="text-base font-semibold tabular" :class="m.is_out ? 'text-ink-red-4' : m.is_low ? 'text-ink-amber-4' : 'text-ink-gray-9'">
                  {{ num(m.stock) }} <span class="text-xs font-normal text-ink-gray-5">{{ t(m.unit) }}</span>
                </div>
                <div class="text-xs text-ink-gray-5 tabular">{{ t('min') }} {{ num(m.minimum) }}</div>
              </td>
              <td class="px-4 py-3"><ExpiryChip v-if="m.nearest_expiry" :date="m.nearest_expiry" class="!items-start" /><span v-else class="text-sm text-ink-gray-4">—</span></td>
              <td class="px-4 py-3 text-sm text-ink-gray-6">{{ m.location || '—' }}</td>
              <td class="px-4 py-3"><StatusBadge :status="m.status" /></td>
              <td class="px-4 py-3">
                <Button size="sm" icon-left="lucide-plus" :label="t('Stock')" class="opacity-70 group-hover:opacity-100"
                  @click.stop="openAddStock(m.code)" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- mobile cards -->
      <ul class="space-y-2 md:hidden">
        <li v-for="m in filtered" :key="m.code" class="card flex items-center gap-3 p-3 active:bg-surface-gray-1" @click="open(m)">
          <div class="flex size-10 shrink-0 items-center justify-center rounded-4" :class="tone(m)">
            <span class="lucide-pill size-5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-base font-medium text-ink-gray-9">{{ m.name }}</div>
            <div class="mt-1 flex flex-wrap items-center gap-1.5"><StatusBadge :status="m.status" />
              <span v-if="m.nearest_expiry" class="text-xs text-ink-gray-5">{{ t('exp.') }} {{ date(m.nearest_expiry) }}</span></div>
          </div>
          <div class="text-right">
            <div class="text-lg font-semibold tabular text-ink-gray-9">{{ num(m.stock) }}</div>
            <div class="text-xs text-ink-gray-5">{{ t(m.unit) }}</div>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, FormControl, Select, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import ExpiryChip from '@/components/ExpiryChip.vue'
import { get } from '@/api'
import { t } from '@/i18n'
import { date, num } from '@/format'
import { session } from '@/session'
import { ui, openAddStock, openMedicine } from '@/ui'

const route = useRoute()
const router = useRouter()
const rows = ref(null)
const search = ref(route.query.q || '')
const status = ref(route.query.status || 'all')
const category = ref(route.query.category || '')
const expiryBefore = ref(route.query.before || '')

const statuses = [
  { value: 'all', label: 'All' },
  { value: 'low', label: 'Low stock', dot: 'bg-amber-500' },
  { value: 'out', label: 'Out of stock', dot: 'bg-red-500' },
  { value: 'expiring', label: 'Expiring soon', dot: 'bg-amber-500' },
  { value: 'expired', label: 'Expired', dot: 'bg-red-500' },
  { value: 'ok', label: 'In stock', dot: 'bg-green-500' },
]
const categoryOptions = computed(() => [
  { label: t('All categories'), value: '' },
  ...session.options.categories.map((c) => ({ label: t(c), value: c })),
])

const match = (m, s) =>
  s === 'all' ? true : s === 'ok' ? m.status === 'ok' : s === 'low' ? m.is_low || m.is_out : s === 'out' ? m.is_out :
    s === 'expiring' ? m.is_expiring : s === 'expired' ? m.has_expired : true

const base = computed(() => {
  const q = search.value.trim().toLowerCase()
  return (rows.value || []).filter((m) =>
    (!q || m.name.toLowerCase().includes(q) || m.code.toLowerCase().includes(q)) &&
    (!category.value || m.category === category.value) &&
    (!expiryBefore.value || (m.nearest_expiry && m.nearest_expiry <= expiryBefore.value)))
})
const filtered = computed(() => base.value.filter((m) => match(m, status.value)))
const counts = computed(() => Object.fromEntries(statuses.map((s) => [s.value, base.value.filter((m) => match(m, s.value)).length])))
const tone = (m) => (m.is_out || m.has_expired ? 'bg-red-50 text-red-600' : m.is_low || m.is_expiring ? 'bg-amber-50 text-amber-600' : 'bg-teal-50 text-teal-700')
const open = (m) => router.push({ name: 'medicine', params: { code: m.code } })

watch([search, status, category, expiryBefore], () => {
  router.replace({ query: { ...(search.value && { q: search.value }), ...(status.value !== 'all' && { status: status.value }),
    ...(category.value && { category: category.value }), ...(expiryBefore.value && { before: expiryBefore.value }) } })
})

async function load() {
  try {
    rows.value = await get('medicines')
  } catch (e) {
    toast.error(e.message)
    rows.value = rows.value || []
  }
}
onMounted(load)
watch(() => ui.version, load)
</script>
