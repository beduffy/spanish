import { createRouter, createWebHistory } from 'vue-router'
// Import the new views
import FlashcardView from '../views/FlashcardView.vue'
import CardFlashcardView from '../views/CardFlashcardView.vue'
import DashboardView from '../views/DashboardView.vue'
import SentenceListView from '../views/SentenceListView.vue'
import SentenceDetailView from '../views/SentenceDetailView.vue'
import CardListView from '../views/CardListView.vue'
import CardEditorView from '../views/CardEditorView.vue'
import ImportCardsView from '../views/ImportCardsView.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/',
    name: 'Flashcard',
    component: FlashcardView
  },
  {
    path: '/cards/review',
    name: 'CardFlashcard',
    component: CardFlashcardView
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView
  },
  {
    path: '/sentences',
    name: 'Sentences',
    component: SentenceListView
  },
  {
    path: '/sentences/:id', // Route parameter for sentence ID
    name: 'SentenceDetailView',
    component: SentenceDetailView,
    props: true // Pass route params as props to the component
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
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  // We can remove or comment out the default About route if not needed
  // {
  //   path: '/about',
  //   name: 'about',
  //   // route level code-splitting
  //   // this generates a separate chunk (about.[hash].js) for this route
  //   // which is lazy-loaded when the route is visited.
  //   component: () => import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
  // }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
