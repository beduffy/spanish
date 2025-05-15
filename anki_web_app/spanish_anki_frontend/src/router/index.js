import { createRouter, createWebHistory } from 'vue-router'
// Import the new views
import FlashcardView from '../views/FlashcardView.vue'
import DashboardView from '../views/DashboardView.vue'
import SentenceListView from '../views/SentenceListView.vue'
import SentenceDetailView from '../views/SentenceDetailView.vue'

const routes = [
  {
    path: '/',
    name: 'Flashcard',
    component: FlashcardView
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
