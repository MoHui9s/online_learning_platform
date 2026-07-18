<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'

const route = useRoute()
const showLayout = computed(() => !route.meta.public)
</script>

<template>
  <AppLayout v-if="showLayout">
    <RouterView />
  </AppLayout>
  <template v-else>
    <RouterView />
  </template>
</template>

<style>
html,
body,
#app {
  margin: 0;
  height: 100%;
}
</style>
