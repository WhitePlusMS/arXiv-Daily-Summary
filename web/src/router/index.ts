import { createRouter, createWebHistory } from 'vue-router'
// 路由组件改为懒加载，减少首屏包体积
// 同时集成请求取消机制，在路由切换时取消未完成的请求
import { cancelAllRequests } from '@/services/api'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/MainDashboard.vue'),
    },
    {
      path: '/categories',
      name: 'categories',
      component: () => import('../views/CategoryBrowser.vue'),
    },
    {
      path: '/matcher',
      name: 'matcher',
      component: () => import('../views/CategoryMatcher.vue'),
    },
    {
      path: '/env-config',
      name: 'env-config',
      component: () => import('../views/EnvironmentConfig.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFound.vue'),
    },
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { left: 0, top: 0 }
  },
})

// 路由切换时取消所有未完成的 API 请求，避免竞态和资源浪费
router.beforeEach((to, from, next) => {
  try { cancelAllRequests() } catch {}
  next()
})

export default router
