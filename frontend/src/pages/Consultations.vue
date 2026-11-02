<template>
  <div>
    <PageHeader :eyebrow="t('Care')" :title="t('Consultations')" :subtitle="t('Appointments of the day, and what each doctor found and prescribed.')">
      <template #actions>
        <Btn icon="lucide-calendar-plus" :label="t('Book an appointment')" @click="openAppointment()" />
        <Btn variant="primary" icon="lucide-plus" :label="t('New consultation')" to="/consultations/new" />
      </template>
    </PageHeader>

    <div class="mb-4 inline-flex rounded-full border border-line bg-card p-1 shadow-card">
      <button v-for="x in tabs" :key="x.value" class="flex items-center gap-2 rounded-full px-4 py-1.5 text-[13px] font-medium transition"
        :class="tab === x.value ? 'bg-ink text-on-ink' : 'text-ink-soft hover:text-ink'" @click="tab = x.value">
        <span :class="x.icon" class="size-4" /> {{ t(x.label) }}
      </button>
    </div>

    <!-- appointments of one day -->
    <template v-if="tab === 'appointments'">
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <button class="flex size-10 items-center justify-center rounded-full border border-line bg-card text-ink-soft shadow-card hover:text-ink" :aria-label="t('Previous day')" @click="shift(-1)"><span class="lucide-chevron-left size-4" /></button>
        <div class="min-w-[11rem] rounded-full border border-line bg-card px-5 py-2 text-center text-[14px] font-semibold text-ink shadow-card">
          {{ date(day, { weekday: 'long', day: 'numeric', month: 'long' }) }}
        </div>
        <button class="flex size-10 items-center justify-center rounded-full border border-line bg-card text-ink-soft shadow-card hover:text-ink" :aria-label="t('Next day')" @click="shift(1)"><span class="lucide-chevron-right size-4" /></button>
        <Btn v-if="day !== today()" variant="ghost" size="sm" :label="t('Today')" @click="day = today()" />
      </div>
      <div v-if="!appts" class="space-y-2.5"><div v-for="i in 3" :key="i" class="surface h-[84px] animate-pulse" /></div>
      <div v-else-if="!appts.length" class="surface">
        <EmptyState icon="lucide-calendar" :title="t('No appointment this day')" :text="t('Book one, or start a consultation for a patient who walked in.')">
          <Btn variant="primary" icon="lucide-calendar-plus" :label="t('Book an appointment')" @click="openAppointment()" />
        </EmptyState>
      </div>
      <ul v-else class="space-y-2.5">
        <li v-for="a in appts" :key="a.name" class="surface flex flex-wrap items-center gap-x-4 gap-y-3 p-4 md:px-5" :class="a.state === 'cancelled' && 'opacity-60'">
          <div class="w-14 shrink-0 text-center">
            <div class="font-display text-[24px] leading-none tabular text-ink">{{ a.time }}</div>
            <div class="mt-1 text-[11px] text-ink-mute">{{ t('{0} min', a.duration) }}</div>
          </div>
          <Initials :name="a.patient_name" />
          <div class="min-w-0 flex-1">
            <RouterLink :to="{ name: 'patient', params: { name: a.patient } }" class="block truncate text-[15px] font-semibold text-ink hover:underline">{{ a.patient_name }}</RouterLink>
            <p class="mt-0.5 truncate text-[12.5px] text-ink-mute">{{ a.practitioner_name }}<template v-if="a.notes"> · {{ a.notes }}</template></p>
          </div>
          <StatusBadge :status="a.state" />
          <div class="flex w-full justify-end gap-2 sm:w-auto">
            <template v-if="a.state === 'waiting'">
              <Btn v-if="a.consultation" size="sm" variant="brand" icon="lucide-notebook-pen" :label="t('Continue')" :to="{ name: 'consultation', params: { name: a.consultation } }" />
              <Btn v-else size="sm" variant="brand" icon="lucide-notebook-pen" :label="t('Start consultation')"
                :to="{ name: 'consultation', params: { name: 'new' }, query: { patient: a.patient, appointment: a.name } }" />
              <Btn size="sm" variant="ghost" :label="t('Cancel')" @click="cancel(a)" />
            </template>
            <Btn v-else-if="a.consultation" size="sm" :label="t('Open')" :to="{ name: 'consultation', params: { name: a.consultation } }" />
          </div>
        </li>
      </ul>
    </template>

    <!-- all consultations -->
    <template v-else>
      <label class="relative mb-4 block">
        <span class="lucide-search pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-ink-mute" />
        <input v-model="search" type="search" :placeholder="t('Search by patient, symptom or diagnosis…')"
          class="h-11 w-full rounded-full border border-line bg-card pl-11 pr-4 text-[14px] text-ink shadow-card outline-none transition placeholder:text-ink-faint focus:border-apo-mid focus:ring-4 focus:ring-apo/10" />
      </label>
      <div v-if="!rows" class="space-y-2.5"><div v-for="i in 4" :key="i" class="surface h-28 animate-pulse" /></div>
      <div v-else-if="!filtered.length" class="surface">
        <EmptyState icon="lucide-notebook-pen" :title="search ? t('No consultation matches') : t('No consultation yet')"
          :text="t('A consultation records what the doctor found and prescribed.')">
          <Btn v-if="!search" variant="primary" icon="lucide-plus" :label="t('New consultation')" to="/consultations/new" />
        </EmptyState>
      </div>
      <template v-else>
        <div class="grid gap-2.5 xl:grid-cols-2"><ConsultationCard v-for="c in paged.items.value" :key="c.name" :c="c" /></div>
        <Pager v-model:page="paged.page.value" :pages="paged.pages.value" :total="paged.total.value" :size="paged.size" />
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { dialog, toast } from 'frappe-ui'
import Btn from '@/components/Btn.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import Initials from '@/components/Initials.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import ConsultationCard from '@/components/ConsultationCard.vue'
import Pager from '@/components/Pager.vue'
import { usePaged } from '@/paging'
import { get, post } from '@/api'
import { t } from '@/i18n'
import { date, today } from '@/format'
import { ui, changed, H, openAppointment } from '@/ui'

const route = useRoute()
const router = useRouter()
const tabs = [
  { value: 'appointments', label: 'Appointments', icon: 'lucide-calendar-clock' },
  { value: 'history', label: 'Consultations', icon: 'lucide-notebook-pen' },
]
const tab = ref(route.query.tab === 'history' ? 'history' : 'appointments')
const day = ref(today())
const appts = ref(null)
const rows = ref(null)
const search = ref('')

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return (rows.value || []).filter((c) => !q || [c.patient_name, ...c.symptoms, ...c.diagnoses].join(' ').toLowerCase().includes(q))
})
const paged = usePaged(filtered, 10)

function shift(n) {
  const d = new Date(day.value + 'T12:00:00')
  d.setDate(d.getDate() + n)
  day.value = d.toISOString().slice(0, 10)
}

function cancel(a) {
  dialog.danger({
    title: t('Cancel this appointment?'), message: `${a.patient_name} · ${a.time}`, confirmLabel: t('Cancel the appointment'),
    onConfirm: async () => {
      try {
        await post(H('cancel_appointment'), { name: a.name })
        toast.success(t('Appointment cancelled'))
        changed()
      } catch (e) {
        toast.error(e.message)
      }
    },
  })
}

async function load() {
  try {
    if (tab.value === 'appointments') appts.value = await get(H('appointments'), { date: day.value })
    else rows.value = await get(H('consultations'), { limit: 300 })
  } catch (e) {
    toast.error(e.message)
  }
}
watch(tab, () => router.replace({ query: tab.value === 'history' ? { tab: 'history' } : {} }))
watch([tab, day, () => ui.version], () => { if (tab.value === 'appointments') appts.value = null; load() }, { immediate: true })
</script>
