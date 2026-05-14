<template>
  <div class="about">
    <div class="glow" />
    <div class="placeholder">
      <div class="placeholder-icon">⍉</div>
      <h2 class="title">关于我</h2>
      <p class="subtitle">个人信息开发中...</p>
    </div>
  </div>
</template>

<style scoped>
.about {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  min-height: 0;
  position: relative;
}

.placeholder {
  text-align: center;
  animation: fadeIn 800ms ease-out;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.title {
  font-size: clamp(1.5rem, 4vw, 2.5rem);
  font-weight: 600;
  color: oklch(95% 0.01 250);
  letter-spacing: -0.02em;
  margin-bottom: 12px;
}

.subtitle {
  font-size: 1rem;
  color: oklch(55% 0.03 250);
}

.glow {
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, oklch(65% 0.1 175 / 0.1) 0%, transparent 70%);
  filter: blur(50px);
  pointer-events: none;
  top: 30%;
  left: 25%;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>