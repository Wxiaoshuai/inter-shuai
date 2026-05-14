<template>
  <div class="dock">
    <div
      v-for="item in items"
      :key="item.id"
      class="dock-item"
      :data-dock-item="item.id"
      @mouseenter="hoveredItem = item.id"
      @mouseleave="hoveredItem = null"
      @click="navigate(item.id)"
    >
      <div
        class="dock-icon"
        :class="{ active: activeItem === item.id }"
      >
        {{ item.icon }}
      </div>
      <span class="dock-label" :class="{ visible: hoveredItem === item.id }">
        {{ item.label }}
      </span>
      <div v-if="activeItem === item.id" class="dock-indicator" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const items = [
  { id: 'home', label: '首页', icon: '⌂' },
  { id: 'rag', label: 'RAG 展示', icon: '◎' },
  { id: 'agent', label: 'Agent 展示', icon: '◈' },
  { id: 'about', label: '关于我', icon: '⍉' }
]

const activeItem = ref('home')
const hoveredItem = ref(null)

const handleHashChange = () => {
  const hash = window.location.hash.slice(1) || 'home'
  activeItem.value = hash
}

const navigate = (id) => {
  window.location.hash = id
}

onMounted(() => {
  handleHashChange()
  window.addEventListener('hashchange', handleHashChange)
})

onUnmounted(() => {
  window.removeEventListener('hashchange', handleHashChange)
})
</script>

<style scoped>
.dock {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-end;
  gap: 14px;
  padding: 10px 16px;
  background: oklch(25% 0.02 280 / 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid oklch(40% 0.02 280 / 0.3);
  box-shadow: 0 8px 32px oklch(0% 0 0 / 0.4), inset 0 1px 0 oklch(100% 0 0 / 0.05);
  z-index: 1000;
}

.dock-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.dock-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: oklch(30% 0.02 280);
  border: 1px solid oklch(40% 0.02 280 / 0.5);
  transition: transform 250ms cubic-bezier(0.34, 1.56, 0.64, 1),
              background 200ms ease,
              box-shadow 200ms ease;
  font-size: 24px;
  transform-origin: center bottom;
  transform: scale(1);
}

.dock-icon.active {
  background: oklch(35% 0.05 175 / 0.4);
  border-color: oklch(60% 0.1 175 / 0.5);
  box-shadow: 0 0 16px oklch(68% 0.14 175 / 0.3);
}

.dock-item:hover .dock-icon {
  background: oklch(35% 0.02 280);
  transform: scale(1.15);
}

.dock-item:hover .dock-icon.active {
  transform: scale(1.15);
}

.dock-label {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(8px);
  margin-bottom: 8px;
  padding: 4px 10px;
  background: oklch(20% 0.02 280);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: oklch(95% 0.01 250);
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms ease, transform 200ms ease;
  border: 1px solid oklch(35% 0.02 280);
}

.dock-label.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.dock-indicator {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: oklch(68% 0.14 175);
  position: absolute;
  bottom: -6px;
  box-shadow: 0 0 8px oklch(68% 0.14 175);
}
</style>