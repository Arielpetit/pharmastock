<template>
  <span class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[12px] font-medium" :class="meta.cls">
    <span class="size-1.5 rounded-full" :class="meta.dot" />{{ t(meta.label) }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { t } from '@/i18n'

const props = defineProps({ status: String })
const green = { cls: 'bg-apo-soft text-apo-deep', dot: 'bg-apo-mid' }
const amber = { cls: 'bg-warn-soft text-warn', dot: 'bg-[#d9973f]' }
const red = { cls: 'bg-alert-soft text-alert', dot: 'bg-alert' }
const blue = { cls: 'bg-[#E8EEF7] text-[#2F4E7A]', dot: 'bg-[#5B7DB1]' }
const gray = { cls: 'bg-paper-deep text-ink-soft', dot: 'bg-ink-faint' }
const STATUS = {
  ok: { ...green, label: 'In stock' },
  low: { ...amber, label: 'Low stock' },
  out: { ...red, label: 'Out of stock' },
  expiring: { ...amber, label: 'Expiring soon' },
  expired: { ...red, label: 'Expired' },
  pending: { ...blue, label: 'Waiting for approval' },
  approved: { ...green, label: 'Approved' },
  rejected: { ...red, label: 'Rejected' },
  ordered: { ...blue, label: 'Ordered' },
  received: { ...green, label: 'Received' },
  cancelled: { ...gray, label: 'Cancelled' },
}
const meta = computed(() => STATUS[props.status] || { ...gray, label: props.status || '—' })
</script>
