<template>
  <div class="home">
    <div class="glow glow-1" />
    <div class="glow glow-2" />
    <div class="hero">
      <h1 class="title">AI Assistant</h1>
      <p class="subtitle">智能 RAG 检索与 Agent 对话系统，探索知识与智能的边界</p>
    </div>
  </div>
</template>

<style scoped>
.home {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  min-height: 0;
}

.hero {
  text-align: center;
  animation: fadeIn 800ms ease-out;
}

.title {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 600;
  color: oklch(95% 0.01 250);
  letter-spacing: -0.02em;
  margin-bottom: 16px;
  text-wrap: pretty;
}

.subtitle {
  font-size: clamp(1rem, 2vw, 1.25rem);
  color: oklch(65% 0.03 250);
  max-width: 500px;
  line-height: 1.6;
  text-wrap: pretty;
}

.glow {
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, oklch(68% 0.14 175 / 0.15) 0%, transparent 70%);
  filter: blur(60px);
  pointer-events: none;
}

.glow-1 {
  top: 20%;
  left: 10%;
}

.glow-2 {
  top: 60%;
  right: 15%;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>