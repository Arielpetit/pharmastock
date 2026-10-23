<template>
  <div>
    <div v-if="!m" class="space-y-4">
      <div class="h-16 w-1/2 animate-pulse rounded-6 bg-surface-gray-2" />
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4"><div v-for="i in 4" :key="i" class="card h-24 animate-pulse" /></div>
    </div>
    <template v-else>
      <PageHeader :title="m.name" back="/medicines" :back-label="t('Medicines')">
        <template #meta>
          <div class="mt-2 flex flex-wrap items-center gap-2 text-sm text-ink-gray-5">
            <StatusBadge :status="m.status" />
            <span>{{ t(m.category) }}</span>
            <span v-if="m.form || m.strength">· {{ [m.strength, t(m.form || '')].filter(Boolean).join(' · ') }}</span>
          </div>
        </template>
        <template #actions>
          <Button size="md" icon-left="lucide-pencil" :label="t('Edit')" @click="openMedicine(m.code)" />
          <Button size="md" icon-left="lucide-clipboard-list" :label="t('Request')" @click="openRequest(m.code, Math.max(m.minimum * 2 - m.stock, 1))" />
          <Button size="md" icon-left="lucide-hand-heart" :label="t('Give out')" @click="$router.push({ path: '/give-out', query: { medicine: m.code } })" />
          <Button size="md" variant="solid" icon-left="lucide-package-plus" :label="t('Add stock')" class="!bg-[#0f766e] hover:!bg-[#115e59]"
            @click="openAddStock(m.code)" />
        </template>
      </PageHeader>

      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div class="card p-4">
          <div class="text-sm text-ink-gray-5">{{ t('In stock') }}</div>
          <div class="mt-2 text-3xl font-semibold tabular" :class="m.is_out ? 'text-ink-red-4' : m.is_low ? 'text-ink-amber-4' : 'text-ink-gray-9'">
            {{ num(m.stock) }} <span class="text-base font-normal text-ink-gray-5">{{ t(m.unit) }}</span>
          </div>
          <div class="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-gray-2">
            <div class="h-full rounded-full" :class="m.is_out ? 'bg-red-500' : m.is_low ? 'bg-amber-400' : 'bg-teal-500'"
              :style="{ width: `${Math.min(100, Math.max(2, (m.stock / Math.max(m.minimum * 3, 1)) * 100))}%` }" />
          </div>
        </div>
        <div class="card p-4">
          <div class="text-sm text-ink-gray-5">{{ t('Minimum level') }}</div>
          <div class="mt-2 text-3xl font-semibold tabular text-ink-gray-9">{{ num(m.minimum) }}</div>
          <div class="mt-2 text-sm text-ink-gray-5">{{ m.is_low || m.is_out ? t('Below minimum — request more') : t('Alert when stock reaches it') }}</div>
        </div>
        <div class="card p-4">
          <div class="text-sm text-ink-gray-5">{{ t('Nearest expiry') }}</div>
          <div class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ m.nearest_expiry ? date(m.nearest_expiry) : '—' }}</div>
          <div class="mt-2"><ExpiryChip v-if="m.nearest_expiry" :date="m.nearest_expiry" :show-date="false" class="!items-start" /></div>
        </div>
        <div class="card p-4">
          <div class="text-sm text-ink-gray-5">{{ t('Storage location') }}</div>
          <div class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ m.location || '—' }}</div>
          <div class="mt-2 text-sm text-ink-gray-5">{{ t('{0} batch(es) on the shelf', m.batches.length) }}</div>
        </div>
      </div>

      <div v-if="m.has_expired" class="mt-4 flex items-start gap-3 rounded-6 border border-red-200 bg-red-50 p-4 text-red-800">
        <span class="lucide-octagon-alert mt-0.5 size-5 shrink-0" />
        <div class="flex-1 text-sm">
          <div class="font-semibold">{{ t('{0} {1} have expired', num(m.expired_qty), t(m.unit)) }}</div>
          <div>{{ t('Expired stock cannot be given to patients. Remove it from the shelf and record it as expired.') }}</div>
        </div>
        <Button size="sm" theme="red" variant="solid" :label="t('Record as expired')"
          @click="$router.push({ path: '/give-out', query: { medicine: m.code, reason: 'Expired stock' } })" />
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-5">
        <Panel class="lg:col-span-2" :title="t('Batches on the shelf')" icon="lucide-layers" :count="m.batches.length">
          <EmptyState v-if="!m.batches.length" icon="lucide-package-open" :title="t('No stock')" :text="t('Add stock when a delivery arrives.')" />
          <ul v-else class="divide-y divide-outline-gray-1">
            <li v-for="(b, i) in m.batches" :key="b.batch" class="flex items-center gap-3 px-4 py-3">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 text-base font-medium text-ink-gray-9">
                  {{ t('Lot') }} {{ b.batch }}
                  <Badge v-if="i === firstValid" theme="green" size="sm" :label="t('Give out first')" />
                </div>
                <div class="text-xs text-ink-gray-5">{{ t('Expires') }} {{ date(b.expiry_date) }}</div>
              </div>
              <div class="text-right">
                <div class="text-base font-semibold tabular text-ink-gray-9">{{ num(b.qty) }}</div>
                <ExpiryChip :date="b.expiry_date" :days="b.days_left" :show-date="false" />
              </div>
            </li>
          </ul>
        </Panel>

        <Panel class="lg:col-span-3" :title="t('History')" icon="lucide-history">
          <EmptyState v-if="!m.movements.length" icon="lucide-history" :title="t('No movements yet')" />
          <ul v-else class="divide-y divide-outline-gray-1">
            <li v-for="(x, i) in m.movements" :key="i" class="flex items-center gap-3 px-4 py-3">
              <span class="flex size-8 shrink-0 items-center justify-center rounded-full"
                :class="x.direction === 'in' ? 'bg-teal-50 text-teal-700' : 'bg-amber-50 text-amber-700'">
                <span :class="x.direction === 'in' ? 'lucide-arrow-down-left' : 'lucide-arrow-up-right'" class="size-4" />
              </span>
              <div class="min-w-0 flex-1">
                <div class="truncate text-base text-ink-gray-9">{{ t(x.reason) }}<span v-if="x.recipient" class="text-ink-gray-5"> · {{ x.recipient }}</span></div>
                <div class="truncate text-xs text-ink-gray-5">{{ date(x.date) }} · {{ x.by }}<template v-if="x.batch"> · {{ t('Lot') }} {{ x.batch }}</template></div>
              </div>
              <div class="text-right">
                <div class="text-base font-semibold tabular" :class="x.direction === 'in' ? 'text-teal-700' : 'text-ink-gray-8'">
                  {{ x.direction === 'in' ? '+' : '−' }}{{ num(x.qty) }}
                </div>
                <div class="text-xs text-ink-gray-5 tabular">{{ t('left') }} {{ num(x.balance) }}</div>
              </div>
            </li>
          </ul>
        </Panel>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Badge, Button, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import Panel from '@/components/Panel.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import ExpiryChip from '@/components/ExpiryChip.vue'
import { get } from '@/api'
import { t } from '@/i18n'
import { date, num } from '@/format'
import { ui, openAddStock, openMedicine, openRequest } from '@/ui'

const props = defineProps({ code: String })
const m = ref(null)
const firstValid = computed(() => (m.value?.batches || []).findIndex((b) => !b.expired))

async function load() {
  try {
    m.value = await get('medicine', { code: props.code })
  } catch (e) {
    toast.error(e.message)
  }
}
onMounted(load)
watch(() => ui.version, load)
</script>
