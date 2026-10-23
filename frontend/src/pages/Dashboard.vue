<template>
  <div>
    <div class="rise mb-8 flex flex-wrap items-end justify-between gap-5">
      <div>
        <p class="eyebrow mb-2">{{ date(new Date(), { weekday: 'long', day: 'numeric', month: 'long' }) }}</p>
        <h1 class="font-display text-[36px] leading-[1.05] text-ink md:text-[44px]">{{ greeting }}, <em class="italic text-apo">{{ firstName }}</em></h1>
        <p v-if="data" class="mt-2.5 text-[15px] text-ink-mute">{{ summary }}</p>
      </div>
      <div class="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto">
        <Btn icon="lucide-clipboard-list" :label="t('Request stock')" @click="openRequest()" />
        <Btn class="hidden sm:inline-flex" icon="lucide-hand-heart" :label="t('Give out')" to="/give-out" />
        <Btn variant="primary" icon="lucide-plus" :label="t('Add stock')" @click="openAddStock()" />
      </div>
    </div>

    <div v-if="!data" class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div v-for="i in 4" :key="i" class="surface h-[150px] animate-pulse" />
    </div>
    <template v-else>
      <div class="grid grid-cols-2 gap-3 md:gap-4 lg:grid-cols-4">
        <StatCard :label="t('Medicines')" :value="num(c.medicines)" icon="lucide-pill" to="/medicines" :hint="t('on your list')" />
        <StatCard :label="t('Units in stock')" :value="num(c.units)" icon="lucide-boxes" tone="ink" to="/reports?tab=stock" :hint="t('all medicines')" />
        <StatCard :label="t('Low or out of stock')" :value="num(c.low)" icon="lucide-trending-down" :tone="c.low ? 'red' : 'green'"
          to="/medicines?status=low" :hint="c.low ? t('need restocking') : t('all above minimum')" :hint-tone="c.low ? 'red' : 'green'" />
        <StatCard :label="t('Expiring in 90 days')" :value="num(c.expiring)" icon="lucide-calendar-clock" :tone="c.expiring || c.expired ? 'amber' : 'green'"
          to="/medicines?status=expiring" :hint="c.expired ? t('{0} with expired stock', c.expired) : c.expiring ? t('give these out first') : t('none expired')"
          :hint-tone="c.expired ? 'red' : c.expiring ? 'amber' : 'green'" />
      </div>

      <div class="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <Panel :title="t('Stock activity')">
          <template #actions>
            <div class="flex items-center gap-4 text-[12px] text-ink-mute">
              <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-apo-mid" />{{ t('In') }}</span>
              <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-[#E3B27A]" />{{ t('Out') }}</span>
              <span class="hidden sm:inline">{{ t('last 14 days') }}</span>
            </div>
          </template>
          <div class="px-5 pb-5">
            <div class="relative h-48">
              <div class="absolute inset-0 flex flex-col justify-between">
                <div v-for="i in 4" :key="i" class="border-t border-dashed border-line" />
              </div>
              <div class="relative flex h-full items-end gap-1 sm:gap-2">
                <div v-for="d in data.activity" :key="d.date" class="group relative flex h-full flex-1 items-end justify-center gap-[3px]">
                  <div class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 hidden -translate-x-1/2 whitespace-nowrap rounded-[10px] bg-ink px-2.5 py-1.5 text-[11.5px] text-white shadow-lift group-hover:block">
                    <span class="font-semibold">{{ shortDate(d.date) }}</span> · {{ t('In') }} {{ num(d.in) }} · {{ t('Out') }} {{ num(d.out) }}
                  </div>
                  <div class="w-full max-w-[10px] rounded-full bg-apo-mid transition-all" :style="{ height: bar(d.in) }" />
                  <div class="w-full max-w-[10px] rounded-full bg-[#E3B27A] transition-all" :style="{ height: bar(d.out) }" />
                </div>
              </div>
            </div>
            <div class="mt-3 flex gap-1 sm:gap-2">
              <div v-for="(d, i) in data.activity" :key="d.date" class="flex-1 text-center text-[11px] text-ink-faint tabular">
                {{ i % 2 === 1 || i === data.activity.length - 1 ? new Date(d.date + 'T00:00:00').getDate() : '' }}
              </div>
            </div>
          </div>
        </Panel>

        <Panel :title="t('Needs attention')" :count="data.low.length || null">
          <template #actions><RouterLink to="/medicines?status=low" class="text-[13px] font-medium text-ink-mute hover:text-ink">{{ t('See all') }}</RouterLink></template>
          <EmptyState v-if="!data.low.length" icon="lucide-circle-check" :title="t('All good')" :text="t('Every medicine is above its minimum level.')" />
          <ul v-else class="px-2 pb-2">
            <li v-for="m in data.low" :key="m.code">
              <RouterLink :to="`/medicines/${encodeURIComponent(m.code)}`" class="flex items-center gap-3 rounded-[12px] px-3 py-3 transition hover:bg-paper">
                <div class="min-w-0 flex-1">
                  <div class="truncate text-[14px] font-semibold text-ink">{{ m.name }}</div>
                  <BlisterGauge class="mt-2" :stock="m.stock" :minimum="m.minimum" />
                </div>
                <div class="text-right">
                  <div class="font-display text-[22px] leading-none tabular" :class="m.is_out ? 'text-alert' : 'text-warn'">{{ num(m.stock) }}</div>
                  <div class="mt-1 text-[12px] text-ink-mute tabular">{{ t('min') }} {{ num(m.minimum) }}</div>
                </div>
              </RouterLink>
            </li>
          </ul>
        </Panel>
      </div>

      <div class="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.7fr)]">
        <Panel :title="t('Expiring soon')" :count="data.expiring.length || null">
          <template #actions><RouterLink to="/reports?tab=expiry" class="text-[13px] font-medium text-ink-mute hover:text-ink">{{ t('See all') }}</RouterLink></template>
          <EmptyState v-if="!data.expiring.length" icon="lucide-calendar-check" :title="t('Nothing expiring')" :text="t('No batch expires in the next 90 days.')" />
          <ul v-else class="px-2 pb-2">
            <li v-for="b in data.expiring" :key="b.batch" class="flex items-center gap-3 rounded-[12px] px-3 py-3">
              <div class="min-w-0 flex-1">
                <div class="truncate text-[14px] font-semibold text-ink">{{ b.medicine_name }}</div>
                <div class="mt-1 text-[12.5px] text-ink-mute"><span class="font-label text-[11.5px]">{{ b.batch }}</span> · {{ num(b.qty) }} {{ t(b.unit) }}</div>
              </div>
              <ExpiryChip :date="b.expiry_date" :days="b.days_left" align="end" />
            </li>
          </ul>
        </Panel>

        <Panel :title="t('Recent movements')">
          <template #actions><RouterLink to="/reports" class="text-[13px] font-medium text-ink-mute hover:text-ink">{{ t('See all') }}</RouterLink></template>
          <EmptyState v-if="!data.recent.length" icon="lucide-arrow-left-right" :title="t('No movements yet')" :text="t('Stock you add or give out appears here.')" />
          <ul v-else class="px-2 pb-2">
            <li v-for="(m, i) in data.recent" :key="i" class="flex items-center gap-3 rounded-[12px] px-3 py-2.5">
              <span class="flex size-9 shrink-0 items-center justify-center rounded-full"
                :class="m.direction === 'in' ? 'bg-apo-soft text-apo' : 'bg-warn-soft text-warn'">
                <span :class="m.direction === 'in' ? 'lucide-arrow-down-left' : 'lucide-arrow-up-right'" class="size-4" />
              </span>
              <div class="min-w-0 flex-1">
                <div class="truncate text-[14px] font-semibold text-ink">{{ m.medicine_name }}</div>
                <div class="truncate text-[12.5px] text-ink-mute">{{ t(m.reason) }}<template v-if="m.recipient"> · {{ m.recipient }}</template> · {{ m.by }}</div>
              </div>
              <div class="text-right">
                <div class="font-display text-[19px] leading-none tabular" :class="m.direction === 'in' ? 'text-apo' : 'text-ink'">
                  {{ m.direction === 'in' ? '+' : '−' }}{{ num(m.qty) }}
                </div>
                <div class="mt-1 text-[12px] text-ink-mute">{{ shortDate(m.date) }}</div>
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
import { toast } from 'frappe-ui'
import Btn from '@/components/Btn.vue'
import StatCard from '@/components/StatCard.vue'
import Panel from '@/components/Panel.vue'
import EmptyState from '@/components/EmptyState.vue'
import ExpiryChip from '@/components/ExpiryChip.vue'
import BlisterGauge from '@/components/BlisterGauge.vue'
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
// one plain sentence about today, so the dashboard starts with what matters
const summary = computed(() => {
  const parts = []
  if (c.value.low) parts.push(t('{0} medicine(s) to restock', c.value.low))
  if (c.value.expired) parts.push(t('{0} with expired stock', c.value.expired))
  else if (c.value.expiring) parts.push(t('{0} expiring soon', c.value.expiring))
  if (session.isAdmin && c.value.pending) parts.push(t('{0} request(s) to approve', c.value.pending))
  return parts.length ? parts.join(' · ') : t('Everything is in order today.')
})
const peak = computed(() => Math.max(1, ...(data.value?.activity || []).flatMap((d) => [d.in, d.out])))
const bar = (v) => (v ? `${Math.max(5, (v / peak.value) * 100)}%` : '3px')

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
