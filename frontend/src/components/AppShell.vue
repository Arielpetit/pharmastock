<template>
  <div class="min-h-screen md:flex">
    <!-- desktop sidebar -->
    <aside class="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-outline-gray-1 bg-surface-base md:flex">
      <div class="px-5 pb-4 pt-5">
        <Logo :subtitle="session.siteName" />
      </div>
      <nav class="flex-1 space-y-0.5 overflow-y-auto px-3">
        <RouterLink v-for="item in nav" :key="item.to" :to="item.to" custom v-slot="{ navigate, isActive, isExactActive }">
          <a :href="'/pharmacy' + item.to" class="group flex items-center gap-3 rounded-4 px-3 py-2 text-base font-medium transition"
            :class="(item.exact ? isExactActive : isActive) ? 'bg-teal-50 text-teal-800' : 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9'"
            @click="navigate">
            <span :class="[item.icon, (item.exact ? isExactActive : isActive) ? 'text-teal-700' : 'text-ink-gray-5 group-hover:text-ink-gray-7']" class="size-[18px]" />
            <span class="flex-1">{{ t(item.label) }}</span>
            <span v-if="item.badge" class="rounded-full bg-teal-600 px-1.5 py-px text-xs font-semibold text-white tabular">{{ item.badge }}</span>
          </a>
        </RouterLink>
      </nav>
      <div class="space-y-3 border-t border-outline-gray-1 p-3">
        <button class="flex w-full items-center justify-center gap-2 rounded-4 bg-[#0f766e] px-3 py-2.5 text-base font-semibold text-white shadow-sm transition hover:bg-[#115e59]"
          @click="openAddStock()">
          <span class="lucide-plus size-4" /> {{ t('Add stock') }}
        </button>
        <Dropdown :options="userMenu" side="top" align="start" match-trigger-width>
          <template #default>
            <button class="flex w-full items-center gap-3 rounded-4 p-2 text-left transition hover:bg-surface-gray-2">
              <Avatar :label="session.user.full_name" :image="session.user.image" size="lg" />
              <div class="min-w-0 flex-1">
                <div class="truncate text-base font-medium text-ink-gray-9">{{ session.user.full_name }}</div>
                <div class="truncate text-xs text-ink-gray-5">{{ session.isAdmin ? t('Pharmacy administrator') : t('Pharmacy staff') }}</div>
              </div>
              <span class="lucide-chevrons-up-down size-4 text-ink-gray-4" />
            </button>
          </template>
        </Dropdown>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <!-- top bar -->
      <header class="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-outline-gray-1 bg-surface-base/90 px-4 backdrop-blur md:px-8">
        <RouterLink to="/" class="md:hidden"><Logo mark-only mark-class="size-8" /></RouterLink>
        <div class="min-w-0 flex-1 truncate text-base font-semibold text-ink-gray-9 md:hidden">{{ t(currentTitle) }}</div>
        <div class="hidden flex-1 md:block" />
        <button v-if="net.outbox.length" class="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
          :class="failed ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'" @click="ui.sync.open = true">
          <span :class="net.syncing ? 'lucide-loader-circle animate-spin' : failed ? 'lucide-triangle-alert' : 'lucide-cloud-upload'" class="size-3.5" />
          {{ failed ? t('{0} not sent', failed) : t('{0} to send', net.outbox.length) }}
        </button>
        <button class="hidden rounded-3 px-2 py-1 text-sm font-semibold text-ink-gray-6 hover:bg-surface-gray-2 sm:block"
          :title="t('Language')" @click="toggleLang">{{ lang === 'fr' ? 'FR' : 'EN' }}</button>
        <Popover side="bottom" align="end">
          <template #trigger="{ open }">
            <button class="relative flex size-9 items-center justify-center rounded-4 text-ink-gray-6 hover:bg-surface-gray-2"
              :aria-label="t('Alerts')" @click="loadAlerts">
              <span class="lucide-bell size-[18px]" />
              <span v-if="alertCount" class="absolute right-1.5 top-1.5 flex size-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">{{ alertCount > 9 ? '9+' : alertCount }}</span>
            </button>
          </template>
          <template #default="{ close }">
            <div class="w-80 p-2">
              <div class="px-2 pb-2 pt-1 text-sm font-semibold text-ink-gray-9">{{ t('Alerts') }}</div>
              <div v-if="!alerts.length" class="px-2 py-6 text-center text-sm text-ink-gray-5">{{ t('No alerts. Everything looks good.') }}</div>
              <RouterLink v-for="a in alerts" :key="a.key" :to="a.to" class="flex items-start gap-3 rounded-4 p-2 hover:bg-surface-gray-2" @click="close">
                <span class="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-4" :class="a.bg"><span :class="a.icon" class="size-4" /></span>
                <span>
                  <span class="block text-sm font-medium text-ink-gray-9">{{ a.title }}</span>
                  <span class="block text-xs text-ink-gray-5">{{ a.text }}</span>
                </span>
              </RouterLink>
            </div>
          </template>
        </Popover>
        <Dropdown :options="userMenu" align="end" class="md:hidden">
          <template #default>
            <button><Avatar :label="session.user.full_name" :image="session.user.image" size="md" /></button>
          </template>
        </Dropdown>
      </header>

      <div v-if="!net.online" class="flex items-center gap-2 bg-amber-50 px-4 py-2 text-sm text-amber-800 md:px-8">
        <span class="lucide-wifi-off size-4 shrink-0" />
        {{ t('You are offline. You see the last saved data, and new stock movements are kept and sent later.') }}
      </div>

      <main class="mx-auto w-full max-w-6xl flex-1 px-4 pb-28 pt-5 md:px-8 md:pb-10 md:pt-7">
        <slot />
      </main>
    </div>

    <!-- mobile tab bar -->
    <nav class="pb-safe fixed inset-x-0 bottom-0 z-30 border-t border-outline-gray-1 bg-surface-base/95 backdrop-blur md:hidden">
      <div class="grid grid-cols-5 items-end px-1">
        <RouterLink v-for="item in mobileNav" :key="item.to" :to="item.to" custom v-slot="{ navigate, isActive, isExactActive }">
          <a v-if="item.primary" :href="'/pharmacy' + item.to" class="-mt-5 flex flex-col items-center gap-1 pb-2" @click="navigate">
            <span class="brand-gradient flex size-12 items-center justify-center rounded-7 text-white shadow-lg ring-4 ring-surface-base">
              <span :class="item.icon" class="size-5" />
            </span>
            <span class="text-[11px] font-medium text-teal-800">{{ t(item.short) }}</span>
          </a>
          <a v-else :href="'/pharmacy' + item.to" class="relative flex flex-col items-center gap-1 py-2.5"
            :class="(item.exact ? isExactActive : isActive) ? 'text-teal-700' : 'text-ink-gray-5'" @click="navigate">
            <span :class="item.icon" class="size-5" />
            <span class="text-[11px] font-medium">{{ t(item.short) }}</span>
            <span v-if="item.badge" class="absolute right-1/4 top-1.5 size-2 rounded-full bg-red-500" />
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
import { useRoute } from 'vue-router'
import { Avatar, Dropdown, Popover, dialog } from 'frappe-ui'
import Logo from './Logo.vue'
import MedicineDialog from './MedicineDialog.vue'
import AddStockDialog from './AddStockDialog.vue'
import RequestDialog from './RequestDialog.vue'
import SyncDialog from './SyncDialog.vue'
import { get, net } from '@/api'
import { lang, setLanguage, t } from '@/i18n'
import { session, logout } from '@/session'
import { ui, openAddStock } from '@/ui'

const route = useRoute()
const counts = ref({})
const alerts = ref([])

const nav = computed(() => [
  { to: '/', label: 'Dashboard', icon: 'lucide-layout-dashboard', exact: true },
  { to: '/medicines', label: 'Medicines', icon: 'lucide-pill' },
  { to: '/give-out', label: 'Give out stock', icon: 'lucide-hand-heart' },
  { to: '/requests', label: 'Stock requests', icon: 'lucide-clipboard-list', badge: counts.value.pending || null },
  { to: '/reports', label: 'Reports', icon: 'lucide-chart-column' },
  ...(session.isAdmin ? [{ to: '/staff', label: 'Staff', icon: 'lucide-users' }] : []),
])

const mobileNav = computed(() => [
  { to: '/', short: 'Home', icon: 'lucide-layout-dashboard', exact: true },
  { to: '/medicines', short: 'Medicines', icon: 'lucide-pill' },
  { to: '/give-out', short: 'Give out', icon: 'lucide-hand-heart', primary: true },
  { to: '/requests', short: 'Requests', icon: 'lucide-clipboard-list', badge: counts.value.pending },
  { to: '/reports', short: 'Reports', icon: 'lucide-chart-column' },
])

const titles = { dashboard: 'Dashboard', medicines: 'Medicines', medicine: 'Medicine', 'give-out': 'Give out stock',
  requests: 'Stock requests', reports: 'Reports', staff: 'Staff', account: 'My account' }
const currentTitle = computed(() => titles[route.name] || 'PharmaStock')
const failed = computed(() => net.outbox.filter((i) => i.status === 'failed').length)
const alertCount = computed(() => (counts.value.low || 0) + (counts.value.expiring || 0) + (counts.value.expired || 0) +
  (session.isAdmin ? counts.value.pending || 0 : 0))

const userMenu = computed(() => [
  { label: t('My account'), icon: 'lucide-user-round', route: { name: 'account' } },
  ...(session.isAdmin ? [{ label: t('Staff'), icon: 'lucide-users', route: { name: 'staff' } }] : []),
  { label: lang.value === 'fr' ? 'English' : 'Français', icon: 'lucide-languages', onClick: toggleLang },
  { label: t('Log out'), icon: 'lucide-log-out', theme: 'red', onClick: confirmLogout },
])

function toggleLang() {
  setLanguage(lang.value === 'fr' ? 'en' : 'fr')
}

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
      c.expired && { key: 'expired', to: '/medicines?status=expired', icon: 'lucide-octagon-alert text-red-600', bg: 'bg-red-50',
        title: t('{0} medicine(s) with expired stock', c.expired), text: t('Remove them from the shelf and record them as expired.') },
      c.low && { key: 'low', to: '/medicines?status=low', icon: 'lucide-trending-down text-amber-600', bg: 'bg-amber-50',
        title: t('{0} medicine(s) low or out of stock', c.low), text: t('Request more before they run out.') },
      c.expiring && { key: 'expiring', to: '/medicines?status=expiring', icon: 'lucide-calendar-clock text-amber-600', bg: 'bg-amber-50',
        title: t('{0} medicine(s) expiring within 90 days', c.expiring), text: t('Give these out first.') },
      session.isAdmin && c.pending && { key: 'pending', to: '/requests?status=pending', icon: 'lucide-clipboard-list text-blue-600', bg: 'bg-blue-50',
        title: t('{0} request(s) waiting for your approval', c.pending), text: t('Approve or reject them.') },
    ].filter(Boolean)
  } catch {}
}

onMounted(loadAlerts)
watch(() => ui.version, loadAlerts)
</script>
