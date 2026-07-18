<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goCourses() { router.push('/courses') }
function goLearning() { router.push('/learning') }
function goQA() { router.push('/qa') }
function goExam() { router.push('/exam') }
function goStats() { router.push('/stats') }
</script>

<template>
  <div class="page-container">
    <div class="home-hero">
      <div class="hero-icon">
        <svg
          viewBox="0 0 64 64"
          fill="none"
          width="64"
          height="64"
        >
          <rect
            width="64"
            height="64"
            rx="16"
            fill="#2563eb"
            fill-opacity="0.1"
          />
          <path
            d="M18 40V24l14-8 14 8v16l-14 8-14-8z"
            stroke="#2563eb"
            stroke-width="2.5"
            stroke-linejoin="round"
          />
          <path
            d="M32 24v28"
            stroke="#2563eb"
            stroke-width="2"
            stroke-linejoin="round"
            opacity="0.4"
          />
        </svg>
      </div>
      <h1 class="hero-title">
        欢迎回来，继续你的学习之旅
      </h1>
      <p class="hero-sub">
        选择下方模块开始今天的探索
      </p>
    </div>

    <div class="module-grid">
      <div
        class="module-card"
        @click="goCourses"
      >
        <div class="module-icon courses-icon">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" /></svg>
        </div>
        <div class="module-info">
          <h3>课程中心</h3>
          <p>浏览全部课程，开始系统学习</p>
        </div>
        <svg
          class="module-arrow"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><polyline points="9 18 15 12 9 6" /></svg>
      </div>

      <div
        class="module-card"
        @click="goLearning"
      >
        <div class="module-icon learning-icon">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c0 2 4 3 6 3s6-1 6-3v-5" /></svg>
        </div>
        <div class="module-info">
          <h3>我的学习</h3>
          <p>追踪学习进度与课程记录</p>
        </div>
        <svg
          class="module-arrow"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><polyline points="9 18 15 12 9 6" /></svg>
      </div>

      <div
        class="module-card"
        @click="goQA"
      >
        <div class="module-icon qa-icon">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
        </div>
        <div class="module-info">
          <h3>智能答疑</h3>
          <p>AI 驱动，即时解答学习疑问</p>
        </div>
        <svg
          class="module-arrow"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><polyline points="9 18 15 12 9 6" /></svg>
      </div>

      <div
        class="module-card"
        @click="goExam"
      >
        <div class="module-icon exam-icon">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><rect
            x="2"
            y="3"
            width="20"
            height="14"
            rx="2"
            ry="2"
          /><line
            x1="8"
            y1="21"
            x2="16"
            y2="21"
          /><line
            x1="12"
            y1="17"
            x2="12"
            y2="21"
          /></svg>
        </div>
        <div class="module-info">
          <h3>考试测评</h3>
          <p>在线考试，巩固学习成果</p>
        </div>
        <svg
          class="module-arrow"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><polyline points="9 18 15 12 9 6" /></svg>
      </div>

      <div
        class="module-card"
        @click="goStats"
      >
        <div class="module-icon stats-icon">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><line
            x1="18"
            y1="20"
            x2="18"
            y2="10"
          /><line
            x1="12"
            y1="20"
            x2="12"
            y2="4"
          /><line
            x1="6"
            y1="20"
            x2="6"
            y2="14"
          /></svg>
        </div>
        <div class="module-info">
          <h3>数据分析</h3>
          <p>可视化学习数据与趋势</p>
        </div>
        <svg
          class="module-arrow"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        ><polyline points="9 18 15 12 9 6" /></svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-hero { text-align: center; padding: 40px 0 48px; }
.hero-icon { margin-bottom: 20px; }
.hero-title { font-size: 28px; font-weight: 700; color: var(--color-text); margin: 0 0 8px; }
.hero-sub { font-size: 15px; color: var(--color-text-secondary); margin: 0; }

.module-grid { display: flex; flex-direction: column; gap: 8px; max-width: 680px; margin: 0 auto; }
.module-card { display: flex; align-items: center; gap: 16px; padding: 18px 24px; background: var(--color-surface); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); border: 1px solid var(--color-border); cursor: pointer; transition: all 0.2s; }
.module-card:hover { box-shadow: var(--shadow-md); border-color: var(--color-primary-light); transform: translateX(4px); }
.module-icon { width: 52px; height: 52px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.courses-icon { background: #eff6ff; color: #2563eb; }
.learning-icon { background: #f0fdf4; color: #16a34a; }
.qa-icon { background: #fefce8; color: #ca8a04; }
.exam-icon { background: #fef2f2; color: #dc2626; }
.stats-icon { background: #f5f3ff; color: #7c3aed; }
.module-info { flex: 1; min-width: 0; }
.module-info h3 { font-size: 16px; font-weight: 600; color: var(--color-text); margin: 0 0 4px; }
.module-info p { font-size: 13px; color: var(--color-text-secondary); margin: 0; }
.module-arrow { color: var(--color-text-muted); flex-shrink: 0; }
</style>
