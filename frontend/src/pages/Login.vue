<template>
  <div class="flex min-h-screen bg-surface-base">
    <!-- brand side -->
    <div class="brand-gradient relative hidden w-[46%] flex-col justify-between overflow-hidden p-12 text-white lg:flex">
      <div class="absolute -right-24 -top-24 size-96 rounded-full bg-white/10" />
      <div class="absolute -bottom-32 -left-20 size-[28rem] rounded-full bg-white/5" />
      <Logo inverted mark-class="size-11 rounded-6 ring-2 ring-white/30" />
      <div class="relative max-w-md">
        <h1 class="text-4xl font-semibold leading-tight tracking-tight">{{ t('Your pharmacy stock, simple and always up to date.') }}</h1>
        <ul class="mt-8 space-y-4 text-lg text-teal-50">
          <li v-for="f in features" :key="f.icon" class="flex items-center gap-3">
            <span class="flex size-9 items-center justify-center rounded-4 bg-white/15"><span :class="f.icon" class="size-[18px]" /></span>
            {{ t(f.text) }}
          </li>
        </ul>
      </div>
      <p class="relative text-sm text-teal-50/70">{{ t('Made for health centers in Cameroon') }}</p>
    </div>

    <!-- form side -->
    <div class="flex flex-1 flex-col">
      <div class="flex justify-end p-5">
        <button class="rounded-3 px-2.5 py-1 text-sm font-semibold text-ink-gray-6 hover:bg-surface-gray-2" @click="toggleLang">
          {{ lang === 'fr' ? 'English' : 'Français' }}
        </button>
      </div>
      <div class="flex flex-1 items-center justify-center px-6 pb-16">
        <form class="w-full max-w-sm" @submit.prevent="submit">
          <Logo class="mb-10 lg:hidden" mark-class="size-11" />
          <h2 class="text-3xl font-semibold tracking-tight text-ink-gray-9">{{ t('Welcome back') }}</h2>
          <p class="mt-2 text-base text-ink-gray-5">{{ t('Log in to manage your medicine stock.') }}</p>
          <div class="mt-8 space-y-4">
            <FormControl v-model="email" type="email" :label="t('Email')" size="lg" autocomplete="username" required
              :placeholder="t('you@clinic.cm')" />
            <FormControl v-model="password" type="password" :label="t('Password')" size="lg" autocomplete="current-password" required />
            <ErrorMessage :message="error" />
            <Button type="submit" variant="solid" size="lg" class="w-full !bg-[#0f766e] hover:!bg-[#115e59]" :loading="loading"
              :label="t('Log in')" />
          </div>
          <p class="mt-6 text-center text-sm text-ink-gray-5">{{ t('Forgot your password? Ask your pharmacy administrator.') }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Button, ErrorMessage, FormControl } from 'frappe-ui'
import Logo from '@/components/Logo.vue'
import { lang, setLanguage, t } from '@/i18n'
import { login } from '@/session'

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const features = [
  { icon: 'lucide-package-check', text: 'Know what is on the shelf at any time' },
  { icon: 'lucide-calendar-clock', text: 'See expiring medicines before it is too late' },
  { icon: 'lucide-bell-ring', text: 'Get alerted when stock runs low' },
  { icon: 'lucide-wifi-off', text: 'Keeps working when the internet is down' },
]

const toggleLang = () => setLanguage(lang.value === 'fr' ? 'en' : 'fr')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await login(email.value.trim(), password.value)
  } catch (e) {
    error.value = t(e.message)
    loading.value = false
  }
}
</script>
