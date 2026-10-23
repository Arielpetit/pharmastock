<template>
  <span v-if="date" class="inline-flex flex-col items-end leading-tight">
    <span class="rounded-3 px-1.5 py-0.5 text-xs font-semibold tabular" :class="tone">{{ label }}</span>
    <span v-if="showDate" class="mt-0.5 text-xs text-ink-gray-5">{{ fmt(date) }}</span>
  </span>
  <span v-else class="text-sm text-ink-gray-4">—</span>
</template>

<script setup>
import { computed } from 'vue'
import { t } from '@/i18n'
import { date as fmt, daysUntil } from '@/format'

const props = defineProps({ date: String, days: Number, showDate: { type: Boolean, default: true } })
const d = computed(() => (props.days ?? daysUntil(props.date)))
const label = computed(() => {
  const n = d.value
  if (n < 0) return t('Expired')
  if (n === 0) return t('Today')
  if (n <= 90) return t('{0} days', n)
  if (n < 730) return t('{0} months', Math.floor(n / 30.4))
  return t('{0} years', Math.floor(n / 365))
})
const tone = computed(() =>
  d.value < 0 ? 'bg-red-50 text-red-700' : d.value <= 30 ? 'bg-red-50 text-red-600' : d.value <= 90 ? 'bg-amber-50 text-amber-700' : 'bg-surface-gray-2 text-ink-gray-6',
)
</script>
