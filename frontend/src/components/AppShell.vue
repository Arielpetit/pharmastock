<template>
  <div class="min-h-screen md:flex">
    <!-- desktop sidebar -->
    <aside class="sticky top-0 hidden h-screen w-[248px] shrink-0 flex-col border-r border-line bg-white md:flex">
      <RouterLink to="/" class="px-6 pb-7 pt-7"><Logo :subtitle="session.siteName" /></RouterLink>

      <nav class="flex-1 overflow-y-auto px-3">
        <p class="eyebrow mb-2 px-3">{{ t('Pharmacy') }}</p>
        <RouterLink v-for="item in nav" :key="item.to" :to="item.to" custom v-slot="{ navigate, isActive, isExactActive }">
          <a :href="'/pharmacy' + item.to" class="group relative mb-0.5 flex items-center gap-3 rounded-[12px] px-3 py-2.5 text-[14px] transition"
            :class="(item.exact ? isExactActive : isActive) ? 'bg-paper-deep font-semibold text-ink' : 'font-medium text-ink-soft hover:bg-paper hover:text-ink'"
            @click="navigate">
            <span :class="[item.icon, (item.exact ? isExactActive : isActive) ? 'text-apo' : 'text-ink-mute group-hover:text-ink-soft']" class="size-[18px]" />
            <span class="flex-1">{{ t(item.label) }}</span>
            <span v-if="item.badge" class="font-label rounded-full bg-ink px-1.5 py-px text-[11px] font-medium text-white tabular">{{ item.badge }}</span>
          </a>
        </RouterLink>
      </nav>

      <div class="p-3">
        <div class="mb-3 rounded-[16px] bg-apo-mist p-4">
          <p class="font-display text-[17px] leading-snug text-apo-deep">{{ t('A delivery just arrived?') }}</p>
          <p class="mt-1 text-[12.5px] leading-snug text-apo/80">{{ t('Record it in a few seconds.') }}</p>
          <Btn class="mt-3" variant="brand" size="sm" icon="lucide-plus" :label="t('Add stock')" @click="openAddStock()" />
        </div>
        <Dropdown :options="userMenu" side="top" align="start" match-trigger-width>
          <template #default>
            <button class="flex w-full items-center gap-3 rounded-[12px] p-2 text-left transition hover:bg-paper">
              <Initials :name="session.user.full_name" />
              <div class="min-w-0 flex-1">
                <div class="truncate text-[13.5px] font-semibold text-ink">{{ session.user.full_name }}</div>
                <div class="truncate text-[12px] text-ink-mute">{{ session.isAdmin ? t('Pharmacy administrator') : t('Pharmacy staff') }}</div>
              </div>
              <span class="lucide-chevrons-up-down size-4 text-ink-faint" />
            </button>
          </template>
        </Dropdown>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <!-- top bar -->
      <header class="sticky top-0 z-20 flex h-16 items-center gap-2 bg-paper/85 px-4 backdrop-blur-md md:px-10">
        <RouterLink to="/" class="md:hidden"><Logo mark-class="size-9" /></RouterLink>
        <div class="flex-1" />

        <button v-if="net.outbox.length" class="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12.5px] font-medium"
          :class="failed ? 'bg-alert-soft text-alert' : 'bg-[#E8EEF7] text-[#2F4E7A]'" @click="ui.sync.open = true">
          <span :class="net.syncing ? 'lucide-loader-circle animate-spin' : failed ? 'lucide-triangle-alert' : 'lucide-cloud-upload'" class="size-3.5" />
          <span class="hidden sm:inline">{{ failed ? t('{0} not sent', failed) : t('{0} to send', net.outbox.length) }}</span>
          <span class="sm:hidden">{{ net.outbox.length }}</span>
        </button>

        <div class="hidden items-center rounded-full border border-line bg-white p-0.5 sm:flex" role="group" :aria-label="t('Language')">
          <button v-for="l in ['fr', 'en']" :key="l" class="rounded-full px-2.5 py-1 text-[11.5px] font-semibold uppercase tracking-wide transition"
            :class="lang === l ? 'bg-ink text-white' : 'text-ink-mute hover:text-ink'" @click="setLanguage(l)">{{ l }}</button>
        </div>

        <Popover side="bottom" align="end">
          <template #trigger>
            <button class="relative flex size-10 items-center justify-center rounded-full border border-line bg-white text-ink-soft shadow-card transition hover:text-ink"
              :aria-label="t('Alerts')" @click="loadAlerts">
              <span class="lucide-bell size-[17px]" />
              <span v-if="alertCount" class="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-alert px-1 text-[10px] font-bold text-white ring-2 ring-paper">{{ alertCount > 9 ? '9+' : alertCount }}</span>
            </button>
          </template>
          <template #default="{ close }">
            <div class="w-[340px] p-2">
              <div class="px-3 pb-2 pt-2">
                <p class="eyebrow">{{ t('Alerts') }}</p>
              </div>
              <div v-if="!alerts.length" class="px-3 pb-6 pt-2 text-center">
                <span class="lucide-circle-check mx-auto mb-2 block size-5 text-apo" />
                <p class="text-sm text-ink-mute">{{ t('No alerts. Everything looks good.') }}</p>
              </div>
              <RouterLink v-for="a in alerts" :key="a.key" :to="a.to" class="flex items-start gap-3 rounded-[12px] p-3 transition hover:bg-paper" @click="close">
                <span class="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full" :class="a.bg"><span :class="a.icon" class="size-4" /></span>
                <span>
                  <span class="block text-[13.5px] font-semibold text-ink">{{ a.title }}</span>
                  <span class="mt-0.5 block text-[12.5px] text-ink-mute">{{ a.text }}</span>
                </span>
              </RouterLink>
            </div>
          </template>
        </Popover>

        <Dropdown :options="userMenu" align="end" class="md:hidden">
          <template #default>
            <button class="rounded-full ring-1 ring-line"><Initials :name="session.user.full_name" /></button>
          </template>
        </Dropdown>
      </header>

      <div v-if="!net.online" class="mx-4 mb-1 flex items-center gap-2.5 rounded-[14px] border border-warn/15 bg-warn-soft px-4 py-2.5 text-[13px] text-warn md:mx-10">
        <span class="lucide-wifi-off size-4 shrink-0" />
        {{ t('You are offline. You see the last saved data, and new stock movements are kept and sent later.') }}
      </div>

      <main class="mx-auto w-full max-w-[1180px] flex-1 px-4 pb-32 pt-4 md:px-10 md:pb-14 md:pt-6">
        <slot />
      </main>
    </div>

    <!-- mobile tab bar -->
    <nav class="pb-safe fixed inset-x-3 bottom-3 z-30 md:hidden">
      <div class="grid grid-cols-5 items-center rounded-[26px] border border-line bg-white/95 px-1 py-1.5 shadow-lift backdrop-blur">
        <RouterLink v-for="item in mobileNav" :key="item.to" :to="item.to" custom v-slot="{ navigate, isActive, isExactActive }">
          <a v-if="item.primary" :href="'/pharmacy' + item.to" class="flex flex-col items-center" :aria-label="t(item.short)" @click="navigate">
            <span class="flex size-[52px] items-center justify-center rounded-full bg-ink text-white shadow-[0_8px_18px_-8px_rgba(22,24,29,.7)]">
              <span :class="item.icon" class="size-[21px]" />
            </span>
          </a>
          <a v-else :href="'/pharmacy' + item.to" class="relative flex flex-col items-center gap-1 py-1.5"
            :class="(item.exact ? isExactActive : isActive) ? 'text-ink' : 'text-ink-faint'" @click="navigate">
            <span :class="item.icon" class="size-[20px]" />
            <span class="text-[10.5px] font-semibold">{{ t(item.short) }}</span>
            <span v-if="(item.exact ? isExactActive : isActive)" class="absolute -bottom-0.5 h-[3px] w-4 rounded-full bg-apo" />
            <span v-if="item.badge" class="absolute right-[28%] top-1 size-2 rounded-full bg-alert ring-2 ring-white" />
          </a>
        </RouterLink>
      </div>
    </nav>

    <MedicineDialog />
    <AddStockDialog />
    <RequestDialog />
    <SyncDialog />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Dropdown, Popover, dialog } from 'frappe-ui'
import Initials from './Initials.vue'
import Logo from './Logo.vue'
import Btn from './Btn.vue'
import MedicineDialog from './MedicineDialog.vue'
import AddStockDialog from './AddStockDialog.vue'
import RequestDialog from './RequestDialog.vue'
import SyncDialog from './SyncDialog.vue'
import { get, net } from '@/api'
import { lang, setLanguage, t } from '@/i18n'
import { session, logout } from '@/session'
import { ui, openAddStock } from '@/ui'

const counts = ref({})
const alerts = ref([])

const nav = computed(() => [
  { to: '/', label: 'Dashboard', icon: 'lucide-layout-grid', exact: true },
  { to: '/medicines', label: 'Medicines', icon: 'lucide-pill' },
  { to: '/give-out', label: 'Give out stock', icon: 'lucide-hand-heart' },
  { to: '/requests', label: 'Stock requests', icon: 'lucide-clipboard-list', badge: counts.value.pending || null },
  { to: '/reports', label: 'Reports', icon: 'lucide-chart-no-axes-column' },
  ...(session.isAdmin ? [{ to: '/staff', label: 'Staff', icon: 'lucide-users-round' }] : []),
])

const mobileNav = computed(() => [
  { to: '/', short: 'Home', icon: 'lucide-layout-grid', exact: true },
  { to: '/medicines', short: 'Medicines', icon: 'lucide-pill' },
  { to: '/give-out', short: 'Give out', icon: 'lucide-hand-heart', primary: true },
  { to: '/requests', short: 'Requests', icon: 'lucide-clipboard-list', badge: counts.value.pending },
  { to: '/reports', short: 'Reports', icon: 'lucide-chart-no-axes-column' },
])

const failed = computed(() => net.outbox.filter((i) => i.status === 'failed').length)
const alertCount = computed(() => (counts.value.low || 0) + (counts.value.expiring || 0) + (counts.value.expired || 0) +
  (session.isAdmin ? counts.value.pending || 0 : 0))

const userMenu = computed(() => [
  { label: t('My account'), icon: 'lucide-user-round', route: { name: 'account' } },
  ...(session.isAdmin ? [{ label: t('Staff'), icon: 'lucide-users-round', route: { name: 'staff' } }] : []),
  { label: lang.value === 'fr' ? 'English' : 'Français', icon: 'lucide-languages', onClick: () => setLanguage(lang.value === 'fr' ? 'en' : 'fr') },
  { label: t('Log out'), icon: 'lucide-log-out', theme: 'red', onClick: confirmLogout },
])

function confirmLogout() {
  if (!net.outbox.length) return logout()
  dialog.danger({
    title: t('Log out?'),
    message: t('{0} change(s) on this device are not sent yet. If you log out now, they are lost.', net.outbox.length),
    confirmLabel: t('Log out'),
    onConfirm: () => {
      net.outbox = []
      localStorage.removeItem('pharmastock.outbox')
      logout()
    },
  })
}

async function loadAlerts() {
  try {
    const d = await get('dashboard')
    counts.value = d.counts
    const c = d.counts
    alerts.value = [
      c.expired && { key: 'expired', to: '/medicines?status=expired', icon: 'lucide-octagon-alert', bg: 'bg-alert-soft text-alert',
        title: t('{0} medicine(s) with expired stock', c.expired), text: t('Remove them from the shelf and record them as expired.') },
      c.low && { key: 'low', to: '/medicines?status=low', icon: 'lucide-trending-down', bg: 'bg-warn-soft text-warn',
        title: t('{0} medicine(s) low or out of stock', c.low), text: t('Request more before they run out.') },
      c.expiring && { key: 'expiring', to: '/medicines?status=expiring', icon: 'lucide-calendar-clock', bg: 'bg-warn-soft text-warn',
        title: t('{0} medicine(s) expiring within 90 days', c.expiring), text: t('Give these out first.') },
      session.isAdmin && c.pending && { key: 'pending', to: '/requests?status=pending', icon: 'lucide-clipboard-list', bg: 'bg-[#E8EEF7] text-[#2F4E7A]',
        title: t('{0} request(s) waiting for your approval', c.pending), text: t('Approve or reject them.') },
    ].filter(Boolean)
  } catch {}
}

onMounted(loadAlerts)
watch(() => ui.version, loadAlerts)
</script>
