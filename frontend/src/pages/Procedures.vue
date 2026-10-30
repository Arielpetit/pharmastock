<template>
  <div>
    <PageHeader :eyebrow="t('Care')" :title="t('Procedures')" :subtitle="t('Care given to patients, and the medicines each one uses.')">
      <template #actions>
        <Btn icon="lucide-list-plus" :label="t('New procedure type')" @click="openTemplate()" />
        <Btn variant="primary" icon="lucide-stethoscope" :label="t('Record a procedure')" @click="openProcedure()" />
      </template>
    </PageHeader>

    <div class="mb-4 inline-flex rounded-full border border-line bg-card p-1 shadow-card">
      <button v-for="x in tabs" :key="x.value" class="flex items-center gap-2 rounded-full px-4 py-1.5 text-[13px] font-medium transition"
        :class="tab === x.value ? 'bg-ink text-on-ink' : 'text-ink-soft hover:text-ink'" @click="tab = x.value">
        <span :class="x.icon" class="size-4" /> {{ t(x.label) }}
      </button>
    </div>

    <!-- recorded procedures -->
    <template v-if="tab === 'records'">
      <div class="scrollbar-none -mx-4 mb-4 flex gap-1.5 overflow-x-auto px-4 md:mx-0 md:px-0">
        <button v-for="s in states" :key="s.value" class="flex shrink-0 items-center gap-2 rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition"
          :class="state === s.value ? 'border-ink bg-ink text-on-ink' : 'border-line bg-card text-ink-soft hover:border-line-strong hover:text-ink'"
          @click="state = s.value">
          {{ t(s.label) }} <span class="tabular" :class="state === s.value ? 'text-on-ink/60' : 'text-ink-faint'">{{ count(s.value) }}</span>
        </button>
      </div>
      <div v-if="!rows" class="space-y-2.5"><div v-for="i in 4" :key="i" class="surface h-28 animate-pulse" /></div>
      <div v-else-if="!shown.length" class="surface">
        <EmptyState icon="lucide-stethoscope" :title="t('No procedures here')" :text="t('Record the care you give, and the medicines used leave the stock.')">
          <Btn variant="primary" icon="lucide-plus" :label="t('Record a procedure')" @click="openProcedure()" />
        </EmptyState>
      </div>
      <template v-else>
        <div class="grid gap-2.5 xl:grid-cols-2">
          <ProcedureCard v-for="x in paged.items.value" :key="x.name" :p="x" />
        </div>
        <Pager v-model:page="paged.page.value" :pages="paged.pages.value" :total="paged.total.value" :size="paged.size" />
      </template>
    </template>

    <!-- procedure types -->
    <template v-else>
      <div v-if="!templates" class="grid gap-2.5 md:grid-cols-2"><div v-for="i in 4" :key="i" class="surface h-36 animate-pulse" /></div>
      <div v-else-if="!templates.length" class="surface">
        <EmptyState icon="lucide-list-plus" :title="t('No procedure types yet')"
          :text="t('First create the cares you give, like a wound dressing, with the medicines they use.')">
          <Btn variant="primary" icon="lucide-plus" :label="t('New procedure type')" @click="openTemplate()" />
        </EmptyState>
      </div>
      <div v-else class="grid gap-2.5 md:grid-cols-2 xl:grid-cols-3">
        <article v-for="tp in templates" :key="tp.name" class="surface flex flex-col p-5" :class="tp.disabled && 'opacity-60'">
          <div class="flex items-start justify-between gap-3">
            <h3 class="font-display text-[20px] leading-tight text-ink">{{ tp.template }}</h3>
            <span v-if="tp.disabled" class="rounded-full bg-paper-deep px-2 py-0.5 text-[11px] text-ink-mute">{{ t('Hidden') }}</span>
          </div>
          <p v-if="tp.description && tp.description !== tp.template" class="mt-1 text-[13px] text-ink-mute">{{ tp.description }}</p>
          <ul class="mt-3 flex-1 space-y-1.5">
            <li v-for="i in tp.items" :key="i.medicine" class="flex items-baseline justify-between gap-3 text-[13px]">
              <span class="truncate text-ink-soft">{{ i.medicine_name }}</span>
              <span class="shrink-0 font-semibold text-ink tabular">× {{ num(i.qty) }} <span class="font-normal text-ink-mute">{{ t(i.unit) }}</span></span>
            </li>
            <li v-if="!tp.items.length" class="text-[13px] text-ink-mute">{{ t('Uses no medicine') }}</li>
          </ul>
          <div class="mt-4 flex items-center justify-between gap-2 border-t border-line/70 pt-3.5">
            <span class="text-[12px] text-ink-mute">{{ t('Done {0} time(s)', tp.used) }}</span>
            <div class="flex gap-1.5">
              <Btn size="sm" variant="ghost" icon="lucide-pencil" :label="t('Edit')" @click="openTemplate(tp.name)" />
              <Btn v-if="!tp.disabled" size="sm" icon="lucide-plus" :label="t('Use')" @click="openProcedure(null, tp.name)" />
            </div>
          </div>
        </article>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'frappe-ui'
import Btn from '@/components/Btn.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import ProcedureCard from '@/components/ProcedureCard.vue'
import Pager from '@/components/Pager.vue'
import { usePaged } from '@/paging'
import { get } from '@/api'
import { t } from '@/i18n'
import { num } from '@/format'
import { ui, H, openProcedure, openTemplate } from '@/ui'

const route = useRoute()
const router = useRouter()
const tabs = [
  { value: 'records', label: 'Recorded', icon: 'lucide-stethoscope' },
  { value: 'types', label: 'Procedure types', icon: 'lucide-list-checks' },
]
const states = [
  { value: 'all', label: 'All' },
  { value: 'planned', label: 'Planned' },
  { value: 'done', label: 'Done' },
]
const tab = ref(route.query.tab === 'types' ? 'types' : 'records')
const state = ref('all')
const rows = ref(null)
const templates = ref(null)

const shown = computed(() => (rows.value || []).filter((r) => state.value === 'all' || r.state === state.value))
const paged = usePaged(shown, 10)
const count = (s) => (rows.value || []).filter((r) => s === 'all' || r.state === s).length

async function load() {
  try {
    if (tab.value === 'records') rows.value = await get(H('procedures'), { limit: 300 })
    else templates.value = await get(H('procedure_templates'), { include_disabled: 1 })
  } catch (e) {
    toast.error(e.message)
  }
}
watch(tab, () => router.replace({ query: tab.value === 'types' ? { tab: 'types' } : {} }))
watch([tab, () => ui.version], load, { immediate: true })
</script>
