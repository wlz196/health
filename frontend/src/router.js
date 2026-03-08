import { createRouter, createWebHistory } from 'vue-router'
import Overview from './views/Overview.vue'
import Anaerobic from './views/Anaerobic.vue'
import Aerobic from './views/Aerobic.vue'
import Intake from './views/Intake.vue'

const routes = [
  { path: '/', redirect: '/overview' },
  { path: '/overview', name: 'Overview', component: Overview },
  { path: '/anaerobic', name: 'Anaerobic', component: Anaerobic },
  { path: '/aerobic', name: 'Aerobic', component: Aerobic },
  { path: '/intake', name: 'Intake', component: Intake },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
