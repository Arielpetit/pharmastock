<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-ink-gray-5">{{ date(new Date(), { weekday: 'long', day: 'numeric', month: 'long' }) }}</p>
        <h1 class="mt-1 text-2xl font-semibold tracking-tight text-ink-gray-9">{{ greeting }}, {{ firstName }}</h1>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button size="md" icon-left="lucide-clipboard-list" :label="t('Request stock')" @click="openRequest()" />
        <Button size="md" icon-left="lucide-hand-heart" :label="t('Give out')" @click="$router.push('/give-out')" />
        <Button size="md" variant="solid" icon-left="lucide-package-plus" :label="t('Add stock')"
          class="!bg-[#0f766e] hover:!bg-[#115e59]" @click="openAddStock()" />
      </div>
    </div>

    <div v-if="!data" class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
      <div v-for="i in 5" :key="i" class="card h-[118px] animate-pulse" />
    </div>
    <template v-else>
      <div class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <StatCard :label="t('Medicines')" :value="num(c.medicines)" icon="lucide-pill" tone="teal" to="/medicines"
          :hint="t('on your list')" />
        <StatCard :label="t('Units in stock')" :value="num(c.units)" icon="lucide-boxes" tone="blue" to="/reports?tab=stock"
          :hint="t('all medicines')" />
        <StatCard :label="t('Low or out of stock')" :value="num(c.low)" icon="lucide-trending-down" :tone="c.low ? 'red' : 'teal'"
          to="/medicines?status=low" :hint="c.low ? t('need restocking') : t('all above minimum')"
          :hint-class="c.low ? 'text-ink-red-4 font-medium' : ''" />
        <StatCard :label="t('Expiring in 90 days')" :value="num(c.expiring)" icon="lucide-calendar-clock" :tone="c.expiring || c.expired ? 'amber' : 'teal'"
          to="/medicines?status=expiring" :hint="c.expired ? t('{0} with expired stock', c.expired) : t('none expired')"
          :hint-class="c.expired ? 'text-ink-red-4 font-medium' : ''" />
        <StatCard class="col-span-2 md:col-span-1" :label="t('Pending requests')" :value="num(c.pending)" icon="lucide-clipboard-list"
          tone="violet" to="/requests?status=pending" :hint="session.isAdmin && c.pending ? t('waiting for you') : t('waiting for approval')" />
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-3">
        <Panel class="lg:col-span-2" :title="t('Stock activity')" icon="lucide-activity">
          <template #actions>
            <div class="flex items-center gap-3 text-xs text-ink-gray-5">
              <span class="flex items-center gap-1.5"><span class="size-2 rounded-1 bg-teal-500" />{{ t('In') }}</span>
              <span class="flex items-center gap-1.5"><span class="size-2 rounded-1 bg-amber-400" />{{ t('Out') }}</span>
              <span>{{ t('last 14 days') }}</span>
            </div>
          </template>
          <div class="px-4 pb-3 pt-5">
            <div class="flex h-40 items-end gap-1.5 sm:gap-2">
              <div v-for="d in data.activity" :key="d.date" class="group relative flex h-full flex-1 flex-col justify-end">
                <div class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 whitespace-nowrap rounded-3 bg-surface-gray-9 px-2 py-1 text-xs text-white group-hover:block">
                  {{ shortDate(d.date) }} · {{ t('In') }} {{ num(d.in) }} · {{ t('Out') }} {{ num(d.out) }}
                </div>
                <div class="flex h-full items-end justify-center gap-px">
                  <div class="w-1/2 max-w-3 rounded-t-1 bg-teal-500 transition-all" :style="{ height: bar(d.in) }" />
                  <div class="w-1/2 max-w-3 rounded-t-1 bg-amber-400 transition-all" :style="{ height: bar(d.out) }" />
                </div>
              </div>
            </div>
            <div class="mt-2 flex gap-1.5 sm:gap-2">
              <div v-for="(d, i) in data.activity" :key="d.date" class="flex-1 text-center text-[10px] text-ink-gray-4 tabular">
                {{ i % 2 === 1 ? new Date(d.date + 'T00:00:00').getDate() : '' }}
              </div>
            </div>
          </div>
        </Panel>

        <Panel :title="t('Needs attention')" icon="lucide-triangle-alert" icon-class="text-amber-600" :count="data.low.length || null">
          <EmptyState v-if="!data.low.length" icon="lucide-circle-check" :title="t('All good')" :text="t('Every medicine is above its minimum level.')" />
          <ul v-else class="divide-y divide-outline-gray-1">
            <li v-for="m in data.low" :key="m.code">
              <RouterLink :to="`/medicines/${encodeURIComponent(m.code)}`" class="flex items-center gap-3 px-4 py-3 hover:bg-surface-gray-1">
                <div class="min-w-0 flex-1">
                  <div class="truncate text-base font-medium text-ink-gray-9">{{ m.name }}</div>
                  <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-gray-2">
                    <div class="h-full rounded-full" :class="m.is_out ? 'bg-red-500' : 'bg-amber-400'" :style="{ width: pct(m.stock, m.minimum) }" />
                  </div>
                </div>
                <div class="text-right">
                  <div class="text-base font-semibold tabular" :class="m.is_out ? 'text-ink-red-4' : 'text-ink-amber-4'">{{ num(m.stock) }}</div>
                  <div class="text-xs text-ink-gray-5 tabular">{{ t('min') }} {{ num(m.minimum) }}</div>
                </div>
              </RouterLink>
            </li>
          </ul>
        </Panel>
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-3">
        <Panel :title="t('Expiring soon')" icon="lucide-calendar-clock" icon-class="text-amber-600">
          <template #actions><RouterLink to="/reports?tab=expiry" class="text-sm text-ink-gray-5 hover:text-ink-gray-8">{{ t('See all') }}</RouterLink></template>
          <EmptyState v-if="!data.expiring.length" icon="lucide-calendar-check" :title="t('Nothing expiring')" :text="t('No batch expires in the next 90 days.')" />
          <ul v-else class="divide-y divide-outline-gray-1">
            <li v-for="b in data.expiring" :key="b.batch" class="flex items-center gap-3 px-4 py-3">
              <div class="min-w-0 flex-1">
                <div class="truncate text-base font-medium text-ink-gray-9">{{ b.medicine_name }}</div>
                <div class="text-xs text-ink-gray-5">{{ t('Lot') }} {{ b.batch }} · {{ num(b.qty) }} {{ t(b.unit) }}</div>
              </div>
              <ExpiryChip :days="b.days_left" :date="b.expiry_date" />
            </li>
          </ul>
        </Panel>

        <Panel class="lg:col-span-2" :title="t('Recent movements')" icon="lucide-arrow-left-right">
          <template #actions><RouterLink to="/reports" class="text-sm text-ink-gray-5 hover:text-ink-gray-8">{{ t('See all') }}</RouterLink></template>
          <EmptyState v-if="!data.recent.length" icon="lucide-arrow-left-right" :title="t('No movements yet')" :text="t('Stock you add or give out appears here.')" />
          <ul v-else class="divide-y divide-outline-gray-1">
            <li v-for="(m, i) in data.recent" :key="i" class="flex items-center gap-3 px-4 py-3">
              <span class="flex size-8 shrink-0 items-center justify-center rounded-full"
                :class="m.direction === 'in' ? 'bg-teal-50 text-teal-700' : 'bg-amber-50 text-amber-700'">
                <span :class="m.direction === 'in' ? 'lucide-arrow-down-left' : 'lucide-arrow-up-right'" class="size-4" />
              </span>
              <div class="min-w-0 flex-1">
                <div class="truncate text-base font-medium text-ink-gray-9">{{ m.medicine_name }}</div>
                <div class="truncate text-xs text-ink-gray-5">{{ t(m.reason) }}<template v-if="m.recipient"> · {{ m.recipient }}</template> · {{ m.by }}</div>
              </div>
              <div class="text-right">
                <div class="text-base font-semibold tabular" :class="m.direction === 'in' ? 'text-teal-700' : 'text-ink-gray-8'">
                  {{ m.direction === 'in' ? '+' : '−' }}{{ num(m.qty) }}
                </div>
                <div class="text-xs text-ink-gray-5">{{ shortDate(m.date) }}</div>
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
import { Button, toast } from 'frappe-ui'
import StatCard from '@/components/StatCard.vue'
import Panel from '@/components/Panel.vue'
import EmptyState from '@/components/EmptyState.vue'
import ExpiryChip from '@/components/ExpiryChip.vue'
import { get } from '@/api'
import { t } from '@/i18n'
import { date, num, shortDate } from '@/format'
import { session } from '@/session'
import { ui, openAddStock, openRequest } from '@/ui'

const data = ref(null)
const c = computed(() => data.value?.counts || {})
const firstName = computed(() => (session.user.full_name || '').split(' ')[0])
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? t('Good morning') : h < 18 ? t('Good afternoon') : t('Good evening')
})
const peak = computed(() => Math.max(1, ...(data.value?.activity || []).flatMap((d) => [d.in, d.out])))
const bar = (v) => (v ? `${Math.max(4, (v / peak.value) * 100)}%` : '0')
const pct = (stock, min) => `${Math.min(100, Math.max(3, (stock / Math.max(min, 1)) * 100))}%`

async function load() {
  try {
    data.value = await get('dashboard')
  } catch (e) {
    toast.error(e.message)
  }
}
onMounted(load)
watch(() => ui.version, load)
</script>
