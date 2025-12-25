import { createRouter, createWebHistory } from 'vue-router'
// Import views
import CardFlashcardView from '../views/CardFlashcardView.vue'
import DashboardView from '../views/DashboardView.vue'
import CardListView from '../views/CardListView.vue'
import CardEditorView from '../views/CardEditorView.vue'
import ImportCardsView from '../views/ImportCardsView.vue'
import CalendarView from '../views/CalendarView.vue'
import LoginView from '../views/LoginView.vue'
import SupabaseService from '../services/SupabaseService'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'CardReview',
    component: CardFlashcardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/cards',
    name: 'Cards',
    component: CardListView,
    meta: { requiresAuth: true }
  },
  {
    path: '/cards/create',
    name: 'CardCreate',
    component: CardEditorView,
    meta: { requiresAuth: true }
  },
  {
    path: '/cards/:id/edit',
    name: 'CardEditor',
    component: CardEditorView,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/cards/import',
    name: 'ImportCards',
    component: ImportCardsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: CalendarView,
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Navigation guard to protect routes
router.beforeEach(async (to, from, next) => {
  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    // Allow access in Cypress test mode (check both window and global)
    const isCypressTest = typeof window !== 'undefined' && 
                         (window.__CYPRESS_TEST_MODE__ || window.Cypress);
    
    if (isCypressTest) {
      console.log('[Router] Cypress test mode detected, bypassing auth check');
      next()
      return
    }
    
    try {
      // Check if user is logged in
      const session = await SupabaseService.getSession()
      if (session && session.user) {
        // User is authenticated, allow access
        next()
      } else {
        // User is not authenticated, redirect to login
        next({ name: 'Login', query: { redirect: to.fullPath } })
      }
    } catch (error) {
      // Error checking session, redirect to login
      console.error('Auth check error:', error)
      next({ name: 'Login', query: { redirect: to.fullPath } })
    }
  } else {
    // Route doesn't require auth, allow access
    next()
  }
})

export default router
