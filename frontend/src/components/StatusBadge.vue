<template>
  <Badge :theme="meta.theme" :label="t(meta.label)" size="md" variant="subtle">
    <template #prefix><span class="size-1.5 rounded-full" :class="meta.dot" /></template>
  </Badge>
</template>

<script setup>
import { computed } from 'vue'
import { Badge } from 'frappe-ui'
import { t } from '@/i18n'

const props = defineProps({ status: String })
const STATUS = {
  ok: { theme: 'green', label: 'In stock', dot: 'bg-green-500' },
  low: { theme: 'amber', label: 'Low stock', dot: 'bg-amber-500' },
  out: { theme: 'red', label: 'Out of stock', dot: 'bg-red-500' },
  expiring: { theme: 'amber', label: 'Expiring soon', dot: 'bg-amber-500' },
  expired: { theme: 'red', label: 'Expired', dot: 'bg-red-500' },
  pending: { theme: 'blue', label: 'Waiting for approval', dot: 'bg-blue-500' },
  approved: { theme: 'green', label: 'Approved', dot: 'bg-green-500' },
  rejected: { theme: 'red', label: 'Rejected', dot: 'bg-red-500' },
  ordered: { theme: 'violet', label: 'Ordered', dot: 'bg-violet-500' },
  received: { theme: 'green', label: 'Received', dot: 'bg-green-500' },
  cancelled: { theme: 'gray', label: 'Cancelled', dot: 'bg-gray-400' },
}
const meta = computed(() => STATUS[props.status] || { theme: 'gray', label: props.status || '—', dot: 'bg-gray-400' })
</script>
