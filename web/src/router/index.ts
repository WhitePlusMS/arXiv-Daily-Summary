import { createRouter, createWebHistory } from 'vue-router'
import MainDashboard from '../views/MainDashboard.vue'
import CategoryBrowser from '../views/CategoryBrowser.vue'
import CategoryMatcher from '../views/CategoryMatcher.vue'
import EnvironmentConfig from '../views/EnvironmentConfig.vue'

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
    {
      path: '/matcher',
      name: 'matcher',
      component: CategoryMatcher,
    },
    {
      path: '/env-config',
      name: 'env-config',
      component: EnvironmentConfig,
    },
  ],
})

export default router
