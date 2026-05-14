<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="cancel">
        <div class="modal">
          <div class="modal-header">
            <span class="modal-title">{{ title }}</span>
          </div>
          <div class="modal-body">
            <span class="modal-message">{{ message }}</span>
          </div>
          <div class="modal-footer">
            <button class="modal-btn cancel" @click="cancel">{{ cancelText }}</button>
            <button class="modal-btn confirm" :class="confirmType" @click="confirm">{{ confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const visible = ref(false)
const title = ref('确认操作')
const message = ref('确定要执行此操作吗？')
const confirmText = ref('确认')
const cancelText = ref('取消')
const confirmType = ref('danger')

let resolvePromise = null

const show = (options = {}) => {
  return new Promise((resolve) => {
    title.value = options.title || '确认操作'
    message.value = options.message || '确定要执行此操作吗？'
    confirmText.value = options.confirmText || '确认'
    cancelText.value = options.cancelText || '取消'
    confirmType.value = options.confirmType || 'danger'
    resolvePromise = resolve
    visible.value = true
  })
}

const cancel = () => {
  visible.value = false
  resolvePromise?.(false)
  resolvePromise = null
}

const confirm = () => {
  visible.value = false
  resolvePromise?.(true)
  resolvePromise = null
}

defineExpose({ show })
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: oklch(0% 0 0 / 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal {
  background: oklch(20% 0.02 280);
  border: 1px solid oklch(40% 0.02 280);
  border-radius: 16px;
  padding: 24px;
  min-width: 320px;
  max-width: 420px;
  box-shadow: 0 24px 64px oklch(0% 0 0 / 0.4);
}

.modal-header {
  margin-bottom: 16px;
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: oklch(95% 0.01 250);
}

.modal-body {
  margin-bottom: 24px;
}

.modal-message {
  font-size: 14px;
  color: oklch(75% 0.01 250);
  line-height: 1.5;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms ease;
  border: 1px solid transparent;
}

.modal-btn.cancel {
  background: oklch(30% 0.02 280);
  border-color: oklch(40% 0.02 280);
  color: oklch(85% 0.01 250);
}

.modal-btn.cancel:hover {
  background: oklch(40% 0.02 280);
}

.modal-btn.confirm {
  background: oklch(50% 0.15 0 / 0.4);
  border-color: oklch(60% 0.15 0 / 0.5);
  color: oklch(95% 0.01 250);
}

.modal-btn.confirm:hover {
  background: oklch(50% 0.15 0 / 0.6);
}

.modal-btn.confirm.danger {
  background: oklch(50% 0.15 25 / 0.4);
  border-color: oklch(60% 0.15 25 / 0.5);
}

.modal-btn.confirm.danger:hover {
  background: oklch(50% 0.15 25 / 0.6);
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 200ms ease;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 200ms cubic-bezier(0.4, 0, 0.2, 1), opacity 200ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.95);
  opacity: 0;
}
</style>