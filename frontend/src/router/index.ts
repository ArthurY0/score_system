import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: () => import('@/views/dashboard/LayoutView.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
        },
        {
          path: 'statistics/class',
          name: 'class-statistics',
          component: () => import('@/views/statistics/ClassStatistics.vue'),
        },
        {
          path: 'statistics/grade',
          name: 'grade-statistics',
          component: () => import('@/views/statistics/GradeStatistics.vue'),
        },
        {
          path: 'statistics/student',
          name: 'student-statistics',
          component: () => import('@/views/statistics/StudentStatistics.vue'),
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/statistics/ReportsView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    return { name: 'login' }
  }
  if (to.name === 'login' && authStore.isLoggedIn) {
    return { name: 'dashboard' }
  }
})

export default router
