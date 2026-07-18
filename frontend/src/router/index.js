/** 路由配置 + 登录守卫。 */
import { createRouter, createWebHistory } from 'vue-router'

import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/pages/Register.vue'),
    meta: { public: true },
  },
  { path: '/', name: 'home', component: () => import('@/pages/Home.vue') },
  { path: '/courses', name: 'courses', component: () => import('@/pages/Courses.vue') },
  {
    path: '/courses/:courseId',
    name: 'course-detail',
    component: () => import('@/pages/CourseDetail.vue'),
  },
  { path: '/learning', name: 'learning', component: () => import('@/pages/Learning.vue') },
  { path: '/qa', name: 'qa', component: () => import('@/pages/QA.vue') },
  { path: '/exam', name: 'exam', component: () => import('@/pages/Exam.vue') },
  { path: '/exam/:examId', name: 'exam-detail', component: () => import('@/pages/ExamDetail.vue') },
  { path: '/stats', name: 'stats', component: () => import('@/pages/Stats.vue') },
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
