/** 认证相关 API（对齐后端 /api/v1/auth）。 */
import request from '@/utils/request'

export function register(data) {
  return request.post('/auth/register', data)
}

export function login(data) {
  return request.post('/auth/login', data)
}

export function logout() {
  return request.post('/auth/logout')
}

export function refresh() {
  return request.post('/auth/refresh')
}

export function getMe() {
  return request.get('/auth/me')
}

export function updateProfile(data) {
  return request.put('/users/me', data)
}
