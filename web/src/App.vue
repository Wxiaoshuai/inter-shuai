<template>
  <div class="app">
    <div class="background" />
    <div class="content">
      <component :is="currentPageComponent" :key="currentPage" />
    </div>
    <Dock />
    <Toast ref="toastRef" />
    <ConfirmDialog ref="confirmRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import Dock from './components/Dock.vue'
import HomePage from './components/HomePage.vue'
import RagPage from './components/RagPage.vue'
import AgentPage from './components/AgentPage.vue'
import AboutPage from './components/AboutPage.vue'
import Toast from './components/Toast.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'

const pageMap = {
  'home': HomePage,
  'rag': RagPage,
  'agent': AgentPage,
  'about': AboutPage
}

const currentPage = ref('home')
const toastRef = ref(null)
const confirmRef = ref(null)

const currentPageComponent = computed(() => {
  return pageMap[currentPage.value] || HomePage
})

const updatePage = () => {
  const hash = window.location.hash.slice(1) || 'home'
  currentPage.value = hash
}

const showToast = (message, type = 'info', duration = 3000) => {
  toastRef.value?.show(message, type, duration)
}

const showConfirm = (options) => {
  return confirmRef.value?.show(options)
}

provide('toast', { show: showToast })
provide('confirm', { show: showConfirm })

onMounted(() => {
  updatePage()
  window.addEventListener('hashchange', updatePage)
})

onUnmounted(() => {
  window.removeEventListener('hashchange', updatePage)
})
</script>

<style>
@import './styles/global.css';

.app {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.background {
  position: fixed;
  inset: 0;
  background: linear-gradient(145deg, oklch(12% 0.02 265) 0%, oklch(18% 0.015 280) 100%);
  z-index: -1;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding-bottom: 80px;
}
</style>