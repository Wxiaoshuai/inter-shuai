<template>
  <div class="about">
    <div class="glow" />
    <div class="card">
      <div class="avatar">王</div>
      <h2 class="name">王帅</h2>
      <p class="title">AI RAG & Agent Developer</p>

      <div class="info-list">
        <div class="info-item">
          <span class="info-icon">📱</span>
          <a href="tel:17610776119" class="info-value">17610776119</a>
        </div>
        <div class="info-item">
          <span class="info-icon">✉️</span>
          <a href="mailto:wangsh8102@163.com" class="info-value">wangsh8102@163.com</a>
        </div>
        <div class="info-item">
          <span class="info-icon">💻</span>
          <a href="https://github.com/Wxiaoshuai" target="_blank" rel="noopener" class="info-value github">
            github.com/Wxiaoshuai
          </a>
        </div>
      </div>

      <div class="divider" />

      <p class="bio">
        专注于 AI 智能体与 RAG 技术开发，构建智能文档处理与检索增强生成系统。
      </p>

      <div class="skills">
        <span class="skill-tag">FastAPI</span>
        <span class="skill-tag">LangChain</span>
        <span class="skill-tag">Vue 3</span>
        <span class="skill-tag">Milvus</span>
        <span class="skill-tag">MySQL</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  min-height: 0;
  position: relative;
}

.glow {
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, oklch(65% 0.1 175 / 0.15) 0%, transparent 70%);
  filter: blur(60px);
  pointer-events: none;
  top: 25%;
  left: 30%;
}

.card {
  background: oklch(25% 0.02 250 / 0.4);
  border: 1px solid oklch(40% 0.02 250 / 0.3);
  border-radius: 20px;
  padding: 48px;
  text-align: center;
  max-width: 420px;
  animation: fadeIn 600ms ease-out;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, oklch(70% 0.15 175), oklch(60% 0.2 250));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 600;
  color: oklch(98% 0.01 250);
  margin: 0 auto 20px;
  box-shadow: 0 4px 20px oklch(0% 0 0 / 0.3);
}

.name {
  font-size: 1.8rem;
  font-weight: 600;
  color: oklch(95% 0.01 250);
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}

.title {
  font-size: 0.95rem;
  color: oklch(70% 0.03 250);
  margin-bottom: 28px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 28px;
}

.info-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.info-icon {
  font-size: 1.1rem;
}

.info-value {
  font-size: 0.95rem;
  color: oklch(85% 0.02 250);
  text-decoration: none;
  transition: color 200ms;
}

.info-value:hover {
  color: oklch(95% 0.01 250);
}

.github {
  color: oklch(75% 0.12 175);
}

.github:hover {
  color: oklch(85% 0.15 175);
}

.divider {
  height: 1px;
  background: oklch(40% 0.02 250 / 0.3);
  margin: 24px 0;
}

.bio {
  font-size: 0.9rem;
  color: oklch(65% 0.02 250);
  line-height: 1.6;
  margin-bottom: 24px;
}

.skills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.skill-tag {
  font-size: 0.8rem;
  padding: 4px 12px;
  border-radius: 12px;
  background: oklch(35% 0.02 250 / 0.4);
  color: oklch(75% 0.02 250);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>