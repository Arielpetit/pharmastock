<template>
  <div class="max-w-2xl">
    <PageHeader :title="t('My account')" />

    <div class="card mb-5 flex items-center gap-4 p-5">
      <Avatar :label="session.user.full_name" :image="session.user.image" size="3xl" />
      <div class="min-w-0">
        <div class="text-lg font-semibold text-ink-gray-9">{{ session.user.full_name }}</div>
        <div class="text-sm text-ink-gray-5">{{ session.user.email }}</div>
        <Badge class="mt-2" :theme="session.isAdmin ? 'violet' : 'blue'" :label="session.isAdmin ? t('Pharmacy administrator') : t('Pharmacy staff')" />
      </div>
    </div>

    <Panel class="mb-5" :title="t('Language')" icon="lucide-languages" padded>
      <div class="grid grid-cols-2 gap-2">
        <button v-for="l in [{ v: 'en', n: 'English' }, { v: 'fr', n: 'Français' }]" :key="l.v" class="rounded-4 border p-3 text-left text-sm font-medium transition"
          :class="lang === l.v ? 'border-teal-600 bg-teal-50 text-teal-900 ring-1 ring-teal-600' : 'border-outline-gray-2 text-ink-gray-7 hover:border-outline-gray-3'"
          @click="setLanguage(l.v)">{{ l.n }}</button>
      </div>
    </Panel>

    <Panel class="mb-5" :title="t('Change password')" icon="lucide-key-round" padded>
      <form class="space-y-4" @submit.prevent="changePassword">
        <FormControl v-model="pw.old" type="password" :label="t('Current password')" size="md" autocomplete="current-password" />
        <FormControl v-model="pw.new" type="password" :label="t('New password')" size="md" autocomplete="new-password"
          :description="t('At least 8 characters, with letters and numbers.')" />
        <ErrorMessage :message="pwError" />
        <Button type="submit" variant="solid" size="md" :loading="pwSaving" :label="t('Update password')" />
      </form>
    </Panel>

    <Panel class="mb-5" :title="t('Install the app')" icon="lucide-smartphone" padded>
      <p class="text-sm text-ink-gray-6">{{ t('On Android, open the browser menu and tap "Install app" or "Add to Home screen". On iPhone, tap Share, then "Add to Home Screen". The app then opens like any other app and keeps working offline.') }}</p>
      <Button v-if="installEvent" class="mt-3" size="md" icon-left="lucide-download" :label="t('Install now')" @click="install" />
    </Panel>

    <Panel :title="t('This device')" icon="lucide-refresh-cw" padded>
      <div class="flex items-center justify-between gap-3 text-sm">
        <span class="text-ink-gray-6">{{ net.outbox.length ? t('{0} change(s) waiting to be sent', net.outbox.length) : t('Everything is sent.') }}</span>
        <Button size="sm" :label="t('Details')" @click="ui.sync.open = true" />
      </div>
      <div class="mt-4 border-t border-outline-gray-1 pt-4">
        <Button theme="red" variant="subtle" size="md" icon-left="lucide-log-out" :label="t('Log out')" @click="logout" />
      </div>
    </Panel>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { Avatar, Badge, Button, ErrorMessage, FormControl, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import Panel from '@/components/Panel.vue'
import { net, post } from '@/api'
import { lang, setLanguage, t } from '@/i18n'
import { session, logout } from '@/session'
import { ui } from '@/ui'

const pw = reactive({ old: '', new: '' })
const pwError = ref('')
const pwSaving = ref(false)
const installEvent = ref(window.__pwaInstall || null)
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  installEvent.value = e
})

async function install() {
  installEvent.value?.prompt()
  installEvent.value = null
}

async function changePassword() {
  pwError.value = ''
  if (!pw.old || !pw.new) return (pwError.value = t('Please fill in both passwords.'))
  pwSaving.value = true
  try {
    await post('frappe.core.doctype.user.user.update_password', { old_password: pw.old, new_password: pw.new, logout_all_sessions: 0 })
    toast.success(t('Password updated'))
    pw.old = pw.new = ''
  } catch (e) {
    pwError.value = e.message
  } finally {
    pwSaving.value = false
  }
}
</script>
