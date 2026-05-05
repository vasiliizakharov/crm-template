import axios from 'axios'
import { useAuth } from '../store/auth'

const baseURL = (import.meta.env.VITE_API_URL as string | undefined) || '/api'

const api = axios.create({ baseURL, timeout: 30_000 })

api.interceptors.request.use((cfg) => {
  const token = useAuth.getState().token
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      useAuth.getState().logout()
      if (location.pathname !== '/login') location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export default api
