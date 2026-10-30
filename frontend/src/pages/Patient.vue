<template>
  <div>
    <div v-if="!p" class="space-y-4"><div class="h-28 animate-pulse rounded-[18px] bg-paper-deep" /><div class="surface h-64 animate-pulse" /></div>
    <template v-else>
      <PageHeader :title="p.patient_name" back="/patients" :back-label="t('Patients')">
        <template #meta>
          <div class="mt-3 flex flex-wrap items-center gap-2">
            <span v-for="chip in chips" :key="chip" class="rounded-full bg-paper-deep px-2.5 py-1 text-[12.5px] text-ink-soft">{{ chip }}</span>
          </div>
        </template>
        <template #actions>
          <Btn icon="lucide-pencil" :label="t('Edit')" @click="openPatient(p.name)" />
          <Btn variant="primary" icon="lucide-stethoscope" :label="t('Record a procedure')" @click="openProcedure(p.name)" />
        </template>
      </PageHeader>

      <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section class="order-2 lg:order-1">
          <div class="mb-3 flex items-baseline justify-between">
            <h2 class="font-display text-[22px] text-ink">{{ t('Care received') }}</h2>
            <span class="text-[12.5px] text-ink-mute">{{ t('{0} procedure(s)', p.procedures.filter((x) => x.state !== 'cancelled').length) }}</span>
          </div>
          <div v-if="!p.procedures.length" class="surface">
            <EmptyState icon="lucide-stethoscope" :title="t('No procedure yet')" :text="t('Procedures you record for this patient appear here.')">
              <Btn variant="primary" icon="lucide-plus" :label="t('Record a procedure')" @click="openProcedure(p.name)" />
            </EmptyState>
          </div>
          <div v-else class="space-y-2.5">
            <ProcedureCard v-for="x in p.procedures" :key="x.name" :p="x" :show-patient="false" />
          </div>
        </section>

        <aside class="order-1 space-y-3 lg:order-2">
          <div class="surface p-5">
            <p class="eyebrow">{{ t('Patient file') }}</p>
            <dl class="mt-3 space-y-3 text-[13.5px]">
              <div class="flex justify-between gap-3"><dt class="text-ink-mute">{{ t('Phone') }}</dt><dd class="text-right font-medium text-ink tabular">{{ p.mobile || '—' }}</dd></div>
              <div class="flex justify-between gap-3"><dt class="text-ink-mute">{{ t('Date of birth') }}</dt><dd class="text-right font-medium text-ink">{{ p.dob ? date(p.dob) : '—' }}</dd></div>
              <div class="flex justify-between gap-3"><dt class="text-ink-mute">{{ t('Blood group') }}</dt><dd class="text-right font-medium text-ink">{{ blood(p.blood_group) || '—' }}</dd></div>
              <div class="flex justify-between gap-3"><dt class="text-ink-mute">{{ t('Registered') }}</dt><dd class="text-right font-medium text-ink">{{ date(p.creation.slice(0, 10)) }}</dd></div>
            </dl>
          </div>
          <div class="rounded-[18px] border p-4" :class="p.allergies ? 'border-alert/15 bg-alert-soft text-alert' : 'border-line bg-card text-ink-mute'">
            <p class="flex items-center gap-2 text-[13px] font-semibold">
              <span class="lucide-triangle-alert size-4" /> {{ t('Allergies') }}
            </p>
            <p class="mt-1 text-[13.5px]" :class="p.allergies ? '' : 'text-ink-mute'">{{ p.allergies || t('None recorded') }}</p>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'frappe-ui'
import Btn from '@/components/Btn.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import ProcedureCard from '@/components/ProcedureCard.vue'
import { get } from '@/api'
import { t } from '@/i18n'
import { date } from '@/format'
import { ageLabel, blood } from '@/care'
import { ui, H, openPatient, openProcedure } from '@/ui'

const props = defineProps({ name: String })
const router = useRouter()
const p = ref(null)
const chips = computed(() => [p.value.sex && t(p.value.sex), ageLabel(p.value.age), blood(p.value.blood_group)].filter(Boolean))

async function load() {
  try {
    p.value = await get(H('patient'), { name: props.name })
  } catch (e) {
    toast.error(e.message)
    router.replace({ name: 'patients' })
  }
}
watch(() => [props.name, ui.version], load, { immediate: true })
</script>
