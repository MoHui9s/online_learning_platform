/** 用户状态 store（Pinia）。 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import * as authApi from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)

  async function login(payload) {
    user.value = await authApi.login(payload)
    return user.value
  }

  async function register(payload) {
    user.value = await authApi.register(payload)
    return user.value
  }

  async function fetchMe() {
    user.value = await authApi.getMe()
    return user.value
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      user.value = null
    }
  }

  return { user, login, register, fetchMe, logout }
})
