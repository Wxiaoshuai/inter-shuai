<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >
        <span class="toast-icon">{{ toastIcons[toast.type] }}</span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
const toastIcons = {
  success: '✓',
  error: '✕',
  info: '◎',
  warning: '⚠',
}

let toastId = 0

const show = (message, type = 'info', duration = 3000) => {
  const id = ++toastId
  toasts.value.push({ id, message, type })

  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, duration)
}

defineExpose({ show })
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  background: oklch(25% 0.02 280);
  border: 1px solid oklch(40% 0.02 280);
  border-radius: 12px;
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px oklch(0% 0 0 / 0.3);
  font-size: 14px;
  color: oklch(90% 0.01 250);
  max-width: 360px;
}

.toast.success {
  border-color: oklch(60% 0.15 145 / 0.5);
  background: oklch(30% 0.02 145 / 0.3);
}

.toast.error {
  border-color: oklch(50% 0.15 25 / 0.5);
  background: oklch(30% 0.02 25 / 0.3);
}

.toast.warning {
  border-color: oklch(65% 0.12 85 / 0.5);
  background: oklch(30% 0.02 85 / 0.3);
}

.toast.info {
  border-color: oklch(50% 0.08 175 / 0.5);
  background: oklch(30% 0.02 175 / 0.3);
}

.toast-icon {
  font-size: 16px;
}

.toast-message {
  flex: 1;
  line-height: 1.4;
}

/* Transitions */
.toast-enter-active {
  animation: toastIn 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-leave-active {
  animation: toastOut 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes toastIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes toastOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}
</style>