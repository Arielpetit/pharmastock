<template>
  <div>
    <PageHeader :title="t('Stock requests')"
      :subtitle="session.isAdmin ? t('Approve or reject what your team asks for.') : t('Ask for medicines you need before ordering.')">
      <template #actions>
        <Button size="md" variant="solid" icon-left="lucide-plus" :label="t('New request')" class="!bg-[#0f766e] hover:!bg-[#115e59]"
          @click="openRequest()" />
      </template>
    </PageHeader>

    <div class="mb-4 flex items-start gap-3 rounded-6 bg-blue-50 p-4 text-sm text-blue-900">
      <span class="lucide-info mt-0.5 size-4 shrink-0 text-blue-600" />
      <p>{{ t('A request means "we need it". Stock only goes up when the delivery arrives and someone records it with Add stock.') }}</p>
    </div>

    <div class="scrollbar-none -mx-4 mb-4 flex gap-1.5 overflow-x-auto px-4 md:mx-0 md:px-0">
      <button v-for="s in tabs" :key="s.value" class="flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition"
        :class="status === s.value ? 'border-teal-600 bg-teal-600 text-white' : 'border-outline-gray-2 bg-surface-base text-ink-gray-6 hover:border-outline-gray-3'"
        @click="status = s.value">
        {{ t(s.label) }} <span class="tabular opacity-70">{{ count(s.value) }}</span>
      </button>
    </div>

    <div v-if="!rows" class="card divide-y divide-outline-gray-1"><div v-for="i in 4" :key="i" class="h-20 animate-pulse" /></div>
    <div v-else-if="!shown.length" class="card">
      <EmptyState icon="lucide-clipboard-list" :title="t('No requests here')" :text="t('Requests you send appear in this list.')" />
    </div>
    <ul v-else class="space-y-2">
      <li v-for="r in shown" :key="r.name" class="card p-4">
        <div class="flex flex-wrap items-start gap-3">
          <div class="flex size-10 shrink-0 items-center justify-center rounded-4" :class="urgencyTone(r.urgency)">
            <span :class="r.automatic ? 'lucide-bot' : 'lucide-clipboard-list'" class="size-5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-base font-semibold text-ink-gray-9">{{ r.medicine_name || r.medicine }}</span>
              <span class="text-base font-semibold tabular text-ink-gray-7">× {{ num(r.qty) }}</span>
              <Badge v-if="r.urgency && r.urgency !== 'Routine'" :theme="r.urgency === 'Emergency' ? 'red' : 'amber'" :label="t(r.urgency)" size="sm" />
            </div>
            <div class="mt-1 text-sm text-ink-gray-5">
              {{ r.requested_by }} · {{ date(r.date) }} · {{ t('needed by {0}', date(r.needed_by)) }}
            </div>
            <p v-if="r.reason" class="mt-2 text-sm text-ink-gray-7">“{{ r.reason }}”</p>
            <p v-if="r.note" class="mt-1 text-sm text-ink-gray-5">{{ t('Note') }}: {{ r.note }}</p>
          </div>
          <div class="flex flex-col items-end gap-2">
            <StatusBadge :status="r.state" />
            <div v-if="session.isAdmin && r.state === 'pending'" class="flex gap-2">
              <Button size="sm" theme="red" variant="subtle" :label="t('Reject')" @click="decide(r, 'reject')" />
              <Button size="sm" variant="solid" :label="t('Approve')" class="!bg-[#0f766e] hover:!bg-[#115e59]" @click="decide(r, 'approve')" />
            </div>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, dialog, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import { get, post } from '@/api'
import { t } from '@/i18n'
import { date, num } from '@/format'
import { session } from '@/session'
import { ui, changed, openRequest } from '@/ui'

const route = useRoute()
const router = useRouter()
const rows = ref(null)
const status = ref(route.query.status || 'all')
const tabs = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Waiting for approval' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
]
const shown = computed(() => (rows.value || []).filter((r) => status.value === 'all' || r.state === status.value))
const count = (s) => (rows.value || []).filter((r) => s === 'all' || r.state === s).length
const urgencyTone = (u) => (u === 'Emergency' ? 'bg-red-50 text-red-600' : u === 'Urgent' ? 'bg-amber-50 text-amber-600' : 'bg-blue-50 text-blue-600')

watch(status, () => router.replace({ query: status.value === 'all' ? {} : { status: status.value } }))

function decide(r, action) {
  const approve = action === 'approve'
  dialog.prompt({
    title: approve ? t('Approve this request?') : t('Reject this request?'),
    message: `${r.medicine_name} × ${num(r.qty)}`,
    theme: approve ? 'green' : 'red',
    confirmLabel: approve ? t('Approve') : t('Reject'),
    fields: [{ name: 'note', label: t('Note (optional)'), type: 'textarea' }],
    onConfirm: async ({ values }) => {
      await post('decide_request', { name: r.name, action, note: values?.note || '' })
      toast.success(approve ? t('Request approved') : t('Request rejected'))
      changed()
    },
  })
}

async function load() {
  try {
    rows.value = await get('requests')
  } catch (e) {
    toast.error(e.message)
    rows.value = rows.value || []
  }
}
onMounted(load)
watch(() => ui.version, load)
</script>
