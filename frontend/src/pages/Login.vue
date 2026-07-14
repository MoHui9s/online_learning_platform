<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = reactive({ account: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  if (!form.account || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login({ account: form.account, password: form.password })
    ElMessage.success('登录成功')
    router.replace(route.query.redirect || '/')
  } catch {
    // 错误已由 request 拦截器提示
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <el-card class="auth-card">
      <h2 class="title">在线教育学习平台 · 登录</h2>
      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="账号（用户名或邮箱）">
          <el-input v-model="form.account" placeholder="用户名 / 邮箱" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" />
        </el-form-item>
        <el-button type="primary" :loading="loading" style="width: 100%" @click="onSubmit">
          登录
        </el-button>
      </el-form>
      <div class="foot">
        还没有账号？<router-link to="/register">去注册</router-link>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.auth-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f0f2f5;
}
.auth-card {
  width: 380px;
}
.title {
  text-align: center;
  margin: 0 0 16px;
  font-size: 18px;
}
.foot {
  margin-top: 12px;
  text-align: center;
  font-size: 13px;
}
</style>
