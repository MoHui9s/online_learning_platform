<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  username: '',
  email: '',
  password: '',
  nickname: '',
  role: 'student',
})
const loading = ref(false)

async function onSubmit() {
  if (!form.username || !form.email || !form.password) {
    ElMessage.warning('用户名、邮箱、密码为必填')
    return
  }
  loading.value = true
  try {
    await userStore.register({ ...form })
    ElMessage.success('注册成功')
    router.replace('/')
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
          加入学习社区
        </h1>
        <p class="banner-desc">
          注册即享全部课程，开启你的 AI 智能学习之旅
        </p>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="auth-main">
      <div class="auth-card">
        <div class="card-header">
          <h2>创建账号</h2>
          <p>填写信息，免费注册</p>
        </div>

        <el-form
          label-position="top"
          class="auth-form"
          @submit.prevent="onSubmit"
        >
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="用户名">
                <el-input
                  v-model="form.username"
                  placeholder="至少 3 位"
                  size="large"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="昵称">
                <el-input
                  v-model="form.nickname"
                  placeholder="选填"
                  size="large"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="邮箱">
            <el-input
              v-model="form.email"
              placeholder="you@example.com"
              size="large"
            />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="至少 6 位"
              size="large"
            />
          </el-form-item>

          <el-form-item label="角色">
            <el-select
              v-model="form.role"
              style="width:100%"
              size="large"
            >
              <el-option
                label="🎓  学生 — 加入课程学习"
                value="student"
              />
              <el-option
                label="📖  教师 — 创建与管理课程"
                value="teacher"
              />
            </el-select>
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="submit-btn"
            @click="onSubmit"
          >
            注 册
          </el-button>
        </el-form>

        <div class="card-footer">
          <span class="footer-text">已有账号？</span>
          <router-link
            to="/login"
            class="footer-link"
          >
            立即登录
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page { display: flex; min-height: 100vh; }

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
.banner-desc { font-size: 16px; color: rgba(255,255,255,0.75); line-height: 1.7; margin: 0; }

.auth-main { flex: 0 0 560px; display: flex; align-items: center; justify-content: center; background: #fff; padding: 60px 48px; overflow-y: auto; }
.auth-card { width: 100%; max-width: 440px; }
.card-header { margin-bottom: 36px; }
.card-header h2 { font-size: 28px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.card-header p { font-size: 15px; color: #64748b; margin: 0; }

.auth-form :deep(.el-form-item__label) { font-weight: 600; color: #334155; padding-bottom: 6px; }
.auth-form :deep(.el-input__wrapper),
.auth-form :deep(.el-select .el-input__wrapper) { border-radius: 10px; box-shadow: 0 0 0 1px #e2e8f0; transition: box-shadow 0.2s; }
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
