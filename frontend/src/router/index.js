/** 路由配置 + 登录守卫。 */
import { createRouter, createWebHistory } from 'vue-router'

import { useUserStore } from '@/store/user'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/pages/Login.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('@/pages/Register.vue'), meta: { public: true } },
  { path: '/', name: 'home', component: () => import('@/pages/Home.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 登录守卫：非 public 路由需已登录（无用户信息时尝试拉 /me）
router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const userStore = useUserStore()
  if (userStore.user) return true
  try {
    await userStore.fetchMe()
    return true
  } catch {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router
