<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)

async function onLogout() {
  await userStore.logout()
  ElMessage.success('已登出')
  router.replace('/login')
}
</script>

<template>
  <el-container class="home">
    <el-header class="header">
      <span class="brand">在线教育学习平台</span>
      <div class="right">
        <span v-if="user" class="hello">
          你好，{{ user.nickname || user.username }}（{{ user.role }}）
        </span>
        <el-button size="small" @click="onLogout">登出</el-button>
      </div>
    </el-header>
    <el-main>
      <el-result icon="success" title="Day1 骨架就绪" sub-title="认证闭环已打通，可在此基础上并行开发各业务模块。">
        <template #extra>
          <p style="color: #909399; font-size: 13px">
            当前登录用户 ID：{{ user?.id }} · 邮箱：{{ user?.email }}
          </p>
        </template>
      </el-result>
    </el-main>
  </el-container>
</template>

<style scoped>
.home {
  height: 100%;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}
.brand {
  font-weight: 600;
}
.right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.hello {
  font-size: 13px;
  color: #606266;
}
</style>
