import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      globalThis.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const login = (data) => api.post('/login', data)
export const getHosts = () => api.get('/host')
export const addHost = (data) => api.post('/host', data)
export const updateHost = (id, data) => api.put(`/host/${id}`, data)
export const deleteHost = (id) => api.delete(`/host/${id}`)
export const getTasks = () => api.get('/task/list')
export const createTask = (data) => api.post('/task/create', data)
export const getClients = () => api.get('/client/list')
export const addClient = (data) => api.post('/client', data)
export const updateClient = (id, data) => api.put(`/client/${id}`, data)
export const deleteClient = (id) => api.delete(`/client/${id}`)
export const sendClientCmd = (clientId, command, taskId) => api.post('/client/send', {
  client_id: clientId,
  command,
  task_id: taskId,
})

export default api
