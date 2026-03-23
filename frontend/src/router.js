import { createRouter, createWebHistory } from 'vue-router'
import Overview from './views/Overview.vue'
import Anaerobic from './views/Anaerobic.vue'
import Intake from './views/Intake.vue'
import Weight from './views/Weight.vue'
import Login from './views/Login.vue'

const routes = [
  { path: '/', redirect: '/overview' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/overview', name: 'Overview', component: Overview },
  { path: '/anaerobic', name: 'Anaerobic', component: Anaerobic },
  { path: '/intake', name: 'Intake', component: Intake },
  { path: '/weight', name: 'Weight', component: Weight },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// === 全局路由守卫 ===
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
