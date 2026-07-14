/**
 * Axios 全局封装（对齐关键决策 1：Cookie + CSRF）
 * - withCredentials：让浏览器自动携带 HttpOnly cookie（access/refresh）
 * - 不手动加 Authorization header
 * - 写方法（POST/PUT/DELETE/PATCH）从 csrf_token cookie 读值写入 X-CSRF-Token
 * - 响应统一解包 { code, data, message }；401 尝试 refresh 后重放
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const CSRF_COOKIE = 'csrf_token'
const CSRF_HEADER = 'X-CSRF-Token'
const WRITE_METHODS = ['post', 'put', 'delete', 'patch']

function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  withCredentials: true,
  timeout: 15000,
})

// 请求拦截：写方法回填 CSRF token
service.interceptors.request.use((config) => {
  if (WRITE_METHODS.includes((config.method || '').toLowerCase())) {
    const token = getCookie(CSRF_COOKIE)
    if (token) config.headers[CSRF_HEADER] = token
  }
  return config
})

let refreshing = null

// 响应拦截：解包统一响应体 + 401 刷新重放
service.interceptors.response.use(
  (response) => {
    const body = response.data
    // 统一响应体 { code, data, message }
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 200) return body.data
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  async (error) => {
    const { response, config } = error
    if (!response) {
      ElMessage.error('网络异常，请检查后端服务')
      return Promise.reject(error)
    }

    // 401：尝试刷新 access 后重放一次（登录/刷新接口本身不重试）
    const isAuthPath = /\/auth\/(login|register|refresh)$/.test(config?.url || '')
    if (response.status === 401 && !config._retried && !isAuthPath) {
      config._retried = true
      try {
        if (!refreshing) {
          refreshing = service.post('/auth/refresh').finally(() => {
            refreshing = null
          })
        }
        await refreshing
        return service(config)
      } catch (e) {
        redirectToLogin()
        return Promise.reject(e)
      }
    }

    if (response.status === 401) redirectToLogin()

    const msg = response.data?.message || `请求错误 ${response.status}`
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

function redirectToLogin() {
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export default service
