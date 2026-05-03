import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Main from './views/Main.vue'
import HostManage from './views/HostManage.vue'
import TaskCreate from './views/TaskCreate.vue'
import TaskList from './views/TaskList.vue'
import LogViewer from './views/LogViewer.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/main',
    name: 'Main',
    component: Main,
    children: [
      {
        path: '',
        redirect: '/main/hosts'
      },
      {
        path: 'hosts',
        name: 'HostManage',
        component: HostManage
      },
      {
        path: 'task/create',
        name: 'TaskCreate',
        component: TaskCreate
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: TaskList
      },
      {
        path: 'task-log',
        name: 'LogViewer',
        component: LogViewer
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/main')
  } else {
    next()
  }
})

export default router
