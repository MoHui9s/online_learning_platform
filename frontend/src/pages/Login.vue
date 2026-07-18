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
  <div class="auth-page">
    <!-- 左侧品牌区 -->
    <div class="auth-banner">
      <div class="banner-overlay" />
      <div class="banner-content">
        <div class="banner-logo">
          <svg
            viewBox="0 0 48 48"
            fill="none"
            class="logo-icon"
          >
            <rect
              width="48"
              height="48"
              rx="12"
              fill="currentColor"
              fill-opacity="0.15"
            />
            <path
              d="M14 32V18l10-6 10 6v14l-10 6-10-6z"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linejoin="round"
            />
            <path
              d="M24 18v22M14 22l10 6 10-6"
              stroke="currentColor"
              stroke-width="2"
              stroke-linejoin="round"
              opacity="0.6"
            />
          </svg>
        </div>
        <h1 class="banner-title">
          在线教育学习平台
        </h1>
        <p class="banner-desc">
          汇聚优质课程资源，AI 赋能个性化学习路径
        </p>
        <div class="banner-features">
          <div class="feature-item">
            <span class="feature-dot" /> <span>500+ 精品课程</span>
          </div>
          <div class="feature-item">
            <span class="feature-dot" /> <span>AI 智能答疑辅导</span>
          </div>
          <div class="feature-item">
            <span class="feature-dot" /> <span>随时随地在线学习</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="auth-main">
      <div class="auth-card">
        <div class="card-header">
          <h2>欢迎回来</h2>
          <p>登录你的账号，继续学习之旅</p>
        </div>

        <el-form
          label-position="top"
          class="auth-form"
          @submit.prevent="onSubmit"
        >
          <el-form-item label="账号">
            <el-input
              v-model="form.account"
              placeholder="用户名或邮箱"
              size="large"
            >
              <template #prefix>
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  style="color:#94a3b8"
                >
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle
                    cx="12"
                    cy="7"
                    r="4"
                  />
                </svg>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="输入密码"
              size="large"
            >
              <template #prefix>
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  style="color:#94a3b8"
                >
                  <rect
                    x="3"
                    y="11"
                    width="18"
                    height="11"
                    rx="2"
                    ry="2"
                  />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </template>
            </el-input>
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="submit-btn"
            @click="onSubmit"
          >
            登 录
          </el-button>
        </el-form>

        <div class="card-footer">
          <span class="footer-text">还没有账号？</span>
          <router-link
            to="/register"
            class="footer-link"
          >
            立即注册
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page { display: flex; min-height: 100vh; }

/* 左侧品牌区 */
.auth-banner {
  flex: 1; position: relative;
  background: linear-gradient(135deg, #1a3a5c 0%, #2563eb 40%, #4f46e5 100%);
  display: flex; align-items: center; justify-content: center; overflow: hidden;
}
.banner-overlay {
  position: absolute; inset: 0;
  background: radial-gradient(circle at 20% 30%, rgba(255,255,255,0.08) 0%, transparent 50%),
              radial-gradient(circle at 80% 70%, rgba(255,255,255,0.06) 0%, transparent 50%);
}
.banner-content { position: relative; z-index: 1; text-align: center; padding: 60px 48px; max-width: 440px; }
.logo-icon { width: 80px; height: 80px; color: #fff; margin-bottom: 32px; }
.banner-title { font-size: 32px; font-weight: 700; color: #fff; margin: 0 0 12px; letter-spacing: 1px; }
.banner-desc { font-size: 16px; color: rgba(255,255,255,0.75); line-height: 1.7; margin: 0 0 40px; }
.banner-features { display: inline-flex; flex-direction: column; gap: 16px; align-items: flex-start; }
.feature-item { display: flex; align-items: center; gap: 12px; color: rgba(255,255,255,0.85); font-size: 15px; }
.feature-dot { width: 8px; height: 8px; border-radius: 50%; background: #60a5fa; box-shadow: 0 0 8px rgba(96,165,250,0.6); flex-shrink: 0; }

/* 右侧表单区 */
.auth-main { flex: 0 0 520px; display: flex; align-items: center; justify-content: center; background: #fff; padding: 60px 48px; }
.auth-card { width: 100%; max-width: 400px; }
.card-header { margin-bottom: 40px; }
.card-header h2 { font-size: 28px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.card-header p { font-size: 15px; color: #64748b; margin: 0; }

.auth-form :deep(.el-form-item__label) { font-weight: 600; color: #334155; padding-bottom: 6px; }
.auth-form :deep(.el-input__wrapper) { border-radius: 10px; box-shadow: 0 0 0 1px #e2e8f0; transition: box-shadow 0.2s; }
.auth-form :deep(.el-input__wrapper:hover) { box-shadow: 0 0 0 1px #93c5fd; }
.auth-form :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 2px rgba(37,99,235,0.25); }

.submit-btn { width: 100%; margin-top: 8px; font-size: 16px; font-weight: 600; letter-spacing: 2px; height: 46px; border-radius: 10px; background: linear-gradient(135deg, #2563eb, #4f46e5); border: none; }
.submit-btn:hover { background: linear-gradient(135deg, #1d4ed8, #4338ca); }

.card-footer { margin-top: 32px; text-align: center; font-size: 14px; }
.footer-text { color: #64748b; }
.footer-link { color: #2563eb; font-weight: 600; text-decoration: none; margin-left: 4px; }
.footer-link:hover { color: #1d4ed8; }

@media (max-width: 800px) { .auth-banner { display: none; } .auth-main { flex: 1; padding: 40px 24px; } }
</style>
