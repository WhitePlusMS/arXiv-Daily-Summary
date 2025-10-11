import { createRouter, createWebHistory } from 'vue-router'
import MainDashboard from '../views/MainDashboard.vue'
import CategoryBrowser from '../views/CategoryBrowser.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: MainDashboard,
    },
    {
      path: '/categories',
      name: 'categories',
      component: CategoryBrowser,
    },
  ],
})

export default router
