<template>
  <div>
    <PageHeader :title="t('Staff')" :subtitle="t('People who can use the pharmacy app.')">
      <template #actions>
        <Button size="md" variant="solid" icon-left="lucide-user-plus" :label="t('Add a person')" class="!bg-[#0f766e] hover:!bg-[#115e59]" @click="edit()" />
      </template>
    </PageHeader>

    <div class="card overflow-hidden">
      <div v-if="!rows" class="p-10 text-center"><LoadingIndicator class="mx-auto size-5 text-ink-gray-5" /></div>
      <EmptyState v-else-if="!rows.length" icon="lucide-users" :title="t('No staff yet')" />
      <ul v-else class="divide-y divide-outline-gray-1">
        <li v-for="u in rows" :key="u.name" class="flex flex-wrap items-center gap-3 px-4 py-3" :class="!u.enabled && 'opacity-60'">
          <Avatar :label="u.full_name" size="xl" />
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 text-base font-medium text-ink-gray-9">
              {{ u.full_name }} <span v-if="u.name === session.user.name" class="text-xs font-normal text-ink-gray-5">({{ t('you') }})</span>
            </div>
            <div class="truncate text-sm text-ink-gray-5">{{ u.email }} · {{ u.last_login ? t('last seen {0}', date(u.last_login)) : t('never logged in') }}</div>
          </div>
          <Badge :theme="u.role === 'Pharmacy Admin' ? 'violet' : 'blue'" :label="u.role === 'Pharmacy Admin' ? t('Administrator') : t('Staff')" />
          <Badge v-if="!u.enabled" theme="gray" :label="t('Disabled')" />
          <Button size="sm" icon-left="lucide-pencil" :label="t('Edit')" @click="edit(u)" />
        </li>
      </ul>
    </div>

    <Dialog v-model:open="open" :title="form.existing ? t('Edit {0}', form.full_name) : t('Add a person')" icon="lucide-user-round" size="lg">
      <form class="space-y-4" @submit.prevent="save">
        <FormControl v-model="form.full_name" :label="t('Full name')" required size="md" />
        <FormControl v-model="form.email" type="email" :label="t('Email (used to log in)')" required size="md" :disabled="form.existing" />
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ t('Role') }}</div>
          <div class="grid gap-2 sm:grid-cols-2">
            <button v-for="r in roles" :key="r.value" type="button" class="rounded-4 border p-3 text-left transition"
              :class="form.role === r.value ? 'border-teal-600 bg-teal-50 ring-1 ring-teal-600' : 'border-outline-gray-2 hover:border-outline-gray-3'"
              @click="form.role = r.value">
              <div class="text-sm font-semibold text-ink-gray-9">{{ t(r.label) }}</div>
              <div class="mt-0.5 text-xs text-ink-gray-5">{{ t(r.text) }}</div>
            </button>
          </div>
        </div>
        <FormControl v-model="form.password" type="password" size="md" :required="!form.existing"
          :label="form.existing ? t('New password (leave empty to keep)') : t('Password')"
          :description="t('At least 8 characters, with letters and numbers. Share it with the person privately.')" />
        <FormControl v-if="form.existing" v-model="form.enabled" type="checkbox" :label="t('Can log in')" />
        <ErrorMessage :message="error" />
      </form>
      <template #actions>
        <div class="flex w-full justify-end gap-2">
          <Button :label="t('Cancel')" size="md" @click="open = false" />
          <Button :label="t('Save')" variant="solid" size="md" :loading="saving" @click="save" />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Avatar, Badge, Button, Dialog, ErrorMessage, FormControl, LoadingIndicator, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { get, post } from '@/api'
import { t } from '@/i18n'
import { date } from '@/format'
import { session } from '@/session'

const rows = ref(null)
const open = ref(false)
const saving = ref(false)
const error = ref('')
const form = reactive({})
const roles = [
  { value: 'Pharmacy Staff', label: 'Staff', text: 'Adds and gives out stock, sends requests.' },
  { value: 'Pharmacy Admin', label: 'Administrator', text: 'Also approves requests and manages staff.' },
]

function edit(u) {
  Object.assign(form, u
    ? { existing: true, full_name: u.full_name, email: u.email, role: u.role, password: '', enabled: !!u.enabled }
    : { existing: false, full_name: '', email: '', role: 'Pharmacy Staff', password: '', enabled: true })
  error.value = ''
  open.value = true
}

async function save() {
  error.value = ''
  if (!form.full_name?.trim() || !form.email?.trim()) return (error.value = t('Please enter the name and email.'))
  if (!form.existing && !form.password) return (error.value = t('Please set a password.'))
  saving.value = true
  try {
    await post('save_staff', { email: form.email, full_name: form.full_name, role: form.role, password: form.password || undefined,
      enabled: form.enabled ? 1 : 0 })
    open.value = false
    toast.success(form.existing ? t('Saved') : t('{0} can now log in', form.full_name))
    load()
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function load() {
  try {
    rows.value = await get('staff')
  } catch (e) {
    toast.error(e.message)
    rows.value = []
  }
}
onMounted(load)
</script>
