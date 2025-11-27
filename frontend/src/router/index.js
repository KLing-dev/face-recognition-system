import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../pages/Home.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../pages/Register.vue')
  },
  {
    path: '/recognition',
    name: 'Recognition',
    component: () => import('../pages/Recognition.vue')
  },
  {
    path: '/camera-test',
    name: 'CameraTest',
    component: () => import('../pages/CameraTest.vue')
  },
  {
    path: '/data-manage',
    name: 'DataManage',
    component: () => import('../pages/DataManage.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router