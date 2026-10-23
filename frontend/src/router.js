import { createRouter, createWebHistory } from 'vue-router'
import { session, loadSession } from './session'

const routes = [
  { path: '/login', name: 'login', component: () => import('./pages/Login.vue'), meta: { public: true } },
  { path: '/', name: 'dashboard', component: () => import('./pages/Dashboard.vue') },
  { path: '/medicines', name: 'medicines', component: () => import('./pages/Medicines.vue') },
  { path: '/medicines/:code', name: 'medicine', component: () => import('./pages/Medicine.vue'), props: true },
  { path: '/give-out', name: 'give-out', component: () => import('./pages/GiveOut.vue') },
  { path: '/requests', name: 'requests', component: () => import('./pages/Requests.vue') },
  { path: '/reports', name: 'reports', component: () => import('./pages/Reports.vue') },
  { path: '/staff', name: 'staff', component: () => import('./pages/Staff.vue'), meta: { admin: true } },
  { path: '/account', name: 'account', component: () => import('./pages/Account.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory('/pharmacy/'),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  if (!session.ready) await loadSession()
  if (to.meta.public) return session.user ? { name: 'dashboard' } : true
  if (!session.user) return { name: 'login' }
  if (to.meta.admin && !session.isAdmin) return { name: 'dashboard' }
  return true
})

export default router
