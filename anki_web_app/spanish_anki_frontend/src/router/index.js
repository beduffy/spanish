import { createRouter, createWebHistory } from 'vue-router'
// Import views
import CardFlashcardView from '../views/CardFlashcardView.vue'
import DashboardView from '../views/DashboardView.vue'
import CardListView from '../views/CardListView.vue'
import CardEditorView from '../views/CardEditorView.vue'
import ImportCardsView from '../views/ImportCardsView.vue'
import CalendarView from '../views/CalendarView.vue'

const routes = [
  {
    path: '/',
    name: 'CardReview',
    component: CardFlashcardView
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView
  },
  {
    path: '/cards',
    name: 'Cards',
    component: CardListView
  },
  {
    path: '/cards/create',
    name: 'CardCreate',
    component: CardEditorView
  },
  {
    path: '/cards/:id/edit',
    name: 'CardEditor',
    component: CardEditorView,
    props: true
  },
  {
    path: '/cards/import',
    name: 'ImportCards',
    component: ImportCardsView
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: CalendarView
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
