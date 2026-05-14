<template>
  <div class="agent">
    <div class="wrapper">
      <!-- Sidebar -->
      <div class="sidebar">
        <div class="sidebar-header">
          <span class="sidebar-title">任务</span>
          <button class="new-chat-btn" @click="resetTask">
            <span>+</span>
            <span>新建</span>
          </button>
        </div>

        <div class="history-list">
          <div v-if="tasks.length === 0" class="empty-hint">
            暂无处理记录
          </div>
          <div
            v-for="task in tasks"
            :key="task.id"
            class="history-item"
            :class="{ active: currentTaskId === task.id }"
            @click="selectTask(task)"
          >
            <span class="history-icon">◎</span>
            <span class="history-title">{{ task.filename }}</span>
            <button class="task-delete-btn" @click.stop="deleteTask(task.id)">×</button>
          </div>
        </div>

        <!-- Flow Graph Section -->
        <div class="graph-section">
          <div class="graph-header" @click="toggleGraph">
            <span class="sidebar-title">处理流程</span>
            <span class="graph-toggle">{{ showGraph ? '▼' : '▶' }}</span>
          </div>
          <div v-if="showGraph && graphData" class="graph-content">
            <div class="flow-chart">
              <div v-for="node in graphData.nodes" :key="node.id" class="flow-node-wrapper">
                <div class="flow-node" :class="node.type">{{ node.label }}</div>
                <!-- Show main path arrow -->
                <div v-if="getMainNextNodeId(node.id)" class="flow-arrow">↓</div>
                <!-- Show branches if any -->
                <div v-if="getBranches(node.id).length > 0" class="flow-branches">
                  <div v-for="(branch, idx) in getBranches(node.id)" :key="idx" class="branch-item">
                    <span class="branch-label">{{ branch.label }}</span>
                    <span class="branch-arrow">→</span>
                    <span class="branch-node" :class="branch.type">{{ branch.toLabel }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="graph-legend">
              <div class="legend-item"><span class="legend-dot process"></span>处理节点</div>
              <div class="legend-item"><span class="legend-dot decision"></span>决策节点</div>
              <div class="legend-item"><span class="legend-dot tool"></span>工具节点</div>
              <div class="legend-item"><span class="legend-dot end"></span>结束节点</div>
            </div>
          </div>
          <div v-else-if="showGraph && !graphData" class="graph-loading">
            加载中...
          </div>
        </div>
      </div>

      <!-- Main chat area -->
      <div class="main">
        <!-- File upload section -->
        <div class="upload-section">
          <label class="upload-btn" :class="{ disabled: isProcessing }">
            <input
              type="file"
              accept=".docx,.doc,.xlsx,.xls"
              style="display: none"
              @change="handleFileUpload"
              :disabled="isProcessing"
            />
            {{ uploadedFile ? '📄 已选择' : '↑ 上传文件' }}
          </label>
          <span class="file-hint">支持 .docx, .doc, .xlsx, .xls</span>
          <div v-if="uploadedFile" class="file-info">
            {{ uploadedFile.name }}
            <button class="clear-file-btn" @click="clearFile">×</button>
          </div>
        </div>

        <!-- Messages -->
        <div class="messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <span class="empty-icon">◈</span>
            <span>上传文件并输入需求开始处理</span>
          </div>

          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="message-wrap"
            :class="msg.role === 'user' ? 'user' : 'assistant'"
          >
            <div class="message-avatar">
              {{ msg.role === 'user' ? '◉' : '◎' }}
            </div>
            <div class="message-content" :class="msg.role">
              <div v-if="msg.role === 'user'">{{ msg.content }}</div>
              <div v-else class="result-content" v-html="renderContent(msg.content)"></div>
            </div>
          </div>

          <div v-if="isProcessing" class="message-wrap assistant">
            <div class="message-avatar">◎</div>
            <div class="message-content assistant">
              <div class="processing-indicator">
                <span class="spinner">◌</span>
                <span>正在处理文档，请稍候...</span>
              </div>
            </div>
          </div>
          <div ref="messagesEnd" />
        </div>

        <!-- Input -->
        <div class="input-area">
          <textarea
            ref="inputRef"
            v-model="inputText"
            class="input"
            placeholder="描述您的需求，例如：统计每列求和、分析文档内容..."
            rows="2"
            :disabled="isProcessing"
            @keydown.enter.exact="handleEnter"
          />
          <button
            class="send-btn"
            :disabled="isProcessing || !inputText.trim() || !uploadedFile"
            @click="sendRequirements"
          >
            →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, inject } from 'vue'
import { marked } from 'marked'
import { useApi } from '../composables/useApi.js'

const { agent } = useApi()
const toast = inject('toast')

marked.setOptions({
  breaks: true,
  gfm: true,
})

const messages = ref([])
const inputText = ref('')
const isProcessing = ref(false)
const uploadedFile = ref(null)
const currentTaskId = ref(null)
const tasks = ref([])
const lastResult = ref(null)
const messagesEnd = ref(null)
const showGraph = ref(true)
const graphData = ref(null)

const toggleGraph = () => {
  showGraph.value = !showGraph.value
}

const loadGraph = async () => {
  try {
    const data = await agent.getGraph()
    graphData.value = data
  } catch (e) {
    console.warn('Failed to load graph:', e)
  }
}

const getNextNode = (nodeId) => {
  if (!graphData.value) return null
  const edge = graphData.value.edges.find(e => e.from === nodeId && !e.label)
  return edge ? graphData.value.nodes.find(n => n.id === edge.to) : null
}

const getMainNextNodeId = (nodeId) => {
  if (!graphData.value) return null
  const edge = graphData.value.edges.find(e => e.from === nodeId && e.label === null)
  return edge ? edge.to : null
}

const getBranches = (nodeId) => {
  if (!graphData.value) return []
  const branches = graphData.value.edges
    .filter(e => e.from === nodeId && e.label)
    .map(e => {
      const toNode = graphData.value.nodes.find(n => n.id === e.to)
      return {
        label: e.label,
        toId: e.to,
        toLabel: toNode ? toNode.label : e.to,
        type: toNode ? toNode.type : 'process'
      }
    })
  return branches
}

const renderContent = (content) => {
  if (!content) return ''
  try {
    let processed = content

    // Handle chart markdown image syntax: ![alt](/api/agent/chart/{image_id})
    // Replace entire markdown image with img tag
    processed = processed.replace(/!\[([^\]]*)\]\(\/api\/agent\/chart\/([^)]+)\)/g, (match, alt, imageId) => {
      return `<img src="/api/agent/chart/${imageId}" class="chart-image" alt="${alt}" />`
    })

    // Also handle base64 images if any remain (for backward compatibility)
    const base64Pattern = /data:image\/png;base64,([A-Za-z0-9+/=]+)/g
    processed = processed.replace(base64Pattern, (match) => {
      return `<img src="${match}" class="chart-image" alt="Chart" />`
    })

    // Parse markdown
    let html = marked.parse(processed)

    // Process any remaining base64 images in HTML
    const imgPattern = /<img src="data:image\/png;base64,([^"]+)"/g
    html = html.replace(imgPattern, (match, data) => {
      return `<img src="data:image/png;base64,${data}" class="chart-image" alt="Chart" />`
    })

    return html
  } catch (e) {
    return content
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

const handleFileUpload = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  const ext = '.' + file.name.split('.').pop().toLowerCase()
  const allowedTypes = ['.docx', '.doc', '.xlsx', '.xls']
  if (!allowedTypes.includes(ext)) {
    toast.show('目前只支持 .docx, .doc, .xlsx, .xls 文件', 'warning')
    return
  }

  uploadedFile.value = {
    name: file.name,
    size: file.size,
    file: file
  }
}

const clearFile = () => {
  uploadedFile.value = null
  const input = document.querySelector('input[type="file"]')
  if (input) input.value = ''
}

const resetTask = () => {
  messages.value = []
  inputText.value = ''
  uploadedFile.value = null
  currentTaskId.value = null
  const input = document.querySelector('input[type="file"]')
  if (input) input.value = ''
}

const selectTask = (task) => {
  currentTaskId.value = task.id
  if (task.messages) {
    messages.value = task.messages
  }
  if (task.uploadedFile) {
    uploadedFile.value = task.uploadedFile
  }
  scrollToBottom()
}

const deleteTask = async (taskId) => {
  try {
    await agent.deleteFile(taskId)
    tasks.value = tasks.value.filter(t => t.id !== taskId)
    localStorage.setItem('doc_tasks', JSON.stringify(tasks.value))
    if (currentTaskId.value === taskId) {
      currentTaskId.value = null
      messages.value = []
      uploadedFile.value = null
    }
    toast.show('任务已删除', 'success')
  } catch (e) {
    console.error('Delete task error:', e)
    toast.show('删除失败: ' + e.message, 'error')
  }
}

const handleEnter = (e) => {
  if (!e.shiftKey) {
    e.preventDefault()
    sendRequirements()
  }
}

const sendRequirements = async () => {
  if (!inputText.value.trim() || !uploadedFile.value || isProcessing.value) return

  const userMsg = { role: 'user', content: inputText.value.trim() }
  messages.value.push(userMsg)
  const requirementsText = inputText.value.trim()
  inputText.value = ''
  isProcessing.value = true
  scrollToBottom()

  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value.file)
    formData.append('requirements', requirementsText)

    const uploadResult = await agent.uploadFile(formData)
    currentTaskId.value = uploadResult.file_id

    const processResult = await agent.processDocument(uploadResult.file_id, requirementsText)

    if (processResult.status === 'needs_confirmation') {
      // Show confirmation message to user
      const confirmMsg = {
        role: 'assistant',
        content: processResult.message + '\n\n请选择：\n1. 继续尝试另一种分析方式\n2. 结束并查看当前结果'
      }
      messages.value.push(confirmMsg)
      // Store partial result for potential continuation
      lastResult.value = {
        fileId: uploadResult.file_id,
        dataContent: processResult.data_content
      }
    } else {
      const aiMsg = {
        role: 'assistant',
        content: processResult.data_content || processResult.message || '分析完成'
      }
      messages.value.push(aiMsg)

      tasks.value.unshift({
        id: uploadResult.file_id,
        filename: uploadedFile.value.name,
        messages: [...messages.value],
        uploadedFile: uploadedFile.value
      })
      localStorage.setItem('doc_tasks', JSON.stringify(tasks.value))
    }
  } catch (e) {
    console.error('Process error:', e)
    const errorMsg = {
      role: 'assistant',
      content: `处理失败: ${e.message}`
    }
    messages.value.push(errorMsg)
    toast.show('处理失败: ' + e.message, 'error')
  } finally {
    isProcessing.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  loadGraph()
  // Load tasks from localStorage
  const saved = localStorage.getItem('doc_tasks')
  if (saved) {
    try {
      tasks.value = JSON.parse(saved)
    } catch (e) {
      console.warn('Failed to load tasks:', e)
    }
  }
})
</script>

<style scoped>
.agent {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 24px 16px 80px;
  min-height: 0;
  overflow: hidden;
}

.wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  gap: 20px;
  height: 100%;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: oklch(70% 0.02 250);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: oklch(35% 0.05 175 / 0.3);
  border: 1px solid oklch(55% 0.1 175 / 0.4);
  border-radius: 10px;
  color: oklch(90% 0.01 250);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
}

.new-chat-btn:hover {
  background: oklch(45% 0.08 175 / 0.4);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
}

.empty-hint {
  color: oklch(50% 0.02 250);
  font-size: 13px;
  text-align: center;
  padding: 20px 0;
}

.history-item {
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 150ms ease;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid transparent;
  position: relative;
}

.history-item:hover {
  background: oklch(30% 0.02 280);
}

.history-item:hover .task-delete-btn {
  opacity: 1;
}

.history-item.active {
  background: oklch(35% 0.03 175 / 0.2);
  border-color: oklch(50% 0.08 175 / 0.3);
}

.task-delete-btn {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: oklch(50% 0.1 0 / 0.3);
  border: none;
  color: oklch(90% 0.01 250);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 150ms ease;
  flex-shrink: 0;
}

.task-delete-btn:hover {
  background: oklch(50% 0.15 0 / 0.5);
}

.history-icon {
  font-size: 14px;
}

.history-title {
  flex: 1;
  font-size: 13px;
  color: oklch(85% 0.01 250);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.graph-section {
  border-top: 1px solid oklch(30% 0.02 280);
  padding-top: 12px;
}

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 0 4px;
  margin-bottom: 8px;
}

.graph-toggle {
  font-size: 10px;
  color: oklch(55% 0.02 250);
  transition: transform 200ms ease;
}

.graph-content {
  padding: 8px;
  background: oklch(20% 0.015 280);
  border-radius: 10px;
}

.flow-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.flow-node-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flow-node {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 11px;
  text-align: center;
  min-width: 80px;
}

.flow-node.start {
  background: oklch(40% 0.05 145 / 0.3);
  border: 1px solid oklch(50% 0.08 145 / 0.4);
  color: oklch(90% 0.01 250);
}

.flow-node.process {
  background: oklch(35% 0.05 175 / 0.3);
  border: 1px solid oklch(50% 0.08 175 / 0.4);
  color: oklch(90% 0.01 250);
}

.flow-node.decision {
  background: oklch(40% 0.05 280 / 0.3);
  border: 1px solid oklch(50% 0.08 280 / 0.4);
  color: oklch(90% 0.01 250);
}

.flow-node.tool {
  background: oklch(35% 0.05 200 / 0.3);
  border: 1px solid oklch(50% 0.08 200 / 0.4);
  color: oklch(90% 0.01 250);
}

.flow-node.tool {
  background: oklch(35% 0.05 200 / 0.3);
  border: 1px solid oklch(50% 0.08 200 / 0.4);
  color: oklch(90% 0.01 250);
}

.flow-node.end {
  background: oklch(50% 0.08 90 / 0.3);
  border: 1px solid oklch(60% 0.1 90 / 0.4);
  color: oklch(90% 0.01 250);
}

.flow-arrow {
  font-size: 10px;
  color: oklch(55% 0.02 250);
  line-height: 1;
}

.graph-loading {
  padding: 12px;
  text-align: center;
  font-size: 11px;
  color: oklch(50% 0.02 250);
}

.flow-branches {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
  padding: 6px 8px;
  background: oklch(25% 0.02 280);
  border-radius: 6px;
  border: 1px solid oklch(35% 0.02 280);
}

.branch-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
}

.branch-label {
  color: oklch(65% 0.03 250);
  font-style: italic;
}

.branch-arrow {
  color: oklch(50% 0.02 250);
}

.branch-node {
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 10px;
}

.branch-node.process {
  background: oklch(35% 0.05 175 / 0.3);
  color: oklch(85% 0.01 250);
}

.branch-node.decision {
  background: oklch(40% 0.05 280 / 0.3);
  color: oklch(85% 0.01 250);
}

.branch-node.end {
  background: oklch(50% 0.08 90 / 0.3);
  color: oklch(85% 0.01 250);
}

.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid oklch(30% 0.02 280);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: oklch(60% 0.02 250);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 4px;
}

.legend-dot.process {
  background: oklch(50% 0.08 175);
}

.legend-dot.decision {
  background: oklch(50% 0.08 280);
}

.legend-dot.tool {
  background: oklch(50% 0.08 200);
}

.legend-dot.end {
  background: oklch(50% 0.08 90);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: oklch(20% 0.02 280 / 0.5);
  border-radius: 20px;
  border: 1px solid oklch(30% 0.02 280);
  overflow: hidden;
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: oklch(22% 0.015 280);
  border-bottom: 1px solid oklch(30% 0.02 280);
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: oklch(30% 0.02 280);
  border: 1px solid oklch(40% 0.02 280);
  border-radius: 8px;
  color: oklch(85% 0.01 250);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms ease;
}

.upload-btn:hover:not(.disabled) {
  background: oklch(40% 0.05 175 / 0.4);
}

.upload-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-hint {
  font-size: 11px;
  color: oklch(50% 0.02 250);
}

.file-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: oklch(75% 0.01 250);
  overflow: hidden;
}

.file-info .clear-file-btn {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: oklch(50% 0.1 0 / 0.3);
  border: none;
  color: oklch(90% 0.01 250);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-info .clear-file-btn:hover {
  background: oklch(50% 0.15 0 / 0.5);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: oklch(55% 0.03 250);
  gap: 12px;
}

.empty-icon {
  font-size: 36px;
}

.message-wrap {
  display: flex;
  gap: 12px;
  animation: slideUp 300ms ease-out;
}

.message-wrap.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.message-wrap.user .message-avatar {
  background: oklch(55% 0.12 175);
}

.message-wrap.assistant .message-avatar {
  background: oklch(35% 0.03 280);
}

.message-content {
  flex: 1;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  text-wrap: pretty;
  max-width: 85%;
  overflow-x: auto;
}

.message-content.user {
  background: oklch(50% 0.1 175 / 0.25);
  color: oklch(95% 0.01 250);
  border-radius: 16px 16px 4px 16px;
}

.message-content.assistant {
  background: oklch(30% 0.02 280);
  color: oklch(85% 0.01 250);
  border-radius: 16px 16px 16px 4px;
}

.result-content {
  overflow-x: auto;
}

.result-content :deep(.chart-image) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 12px 0;
  display: block;
  box-shadow: 0 2px 8px oklch(0% 0 0 / 0.2);
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  font-size: 16px;
  animation: spin 1s linear infinite;
  display: inline-block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Markdown and table styles */
.result-content :deep(pre) {
  background: oklch(25% 0.02 280);
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.result-content :deep(code) {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
}

.result-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.result-content :deep(p:not(:last-child)) {
  margin-bottom: 8px;
}

.result-content :deep(ul),
.result-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.result-content :deep(li) {
  margin: 4px 0;
}

.result-content :deep(blockquote) {
  border-left: 3px solid oklch(55% 0.1 175);
  margin: 8px 0;
  padding-left: 12px;
  color: oklch(65% 0.02 250);
}

.result-content :deep(a) {
  color: oklch(70% 0.15 175);
}

.result-content :deep(strong) {
  color: oklch(90% 0.01 250);
}

/* Table styles - for pandas markdown tables */
.result-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 13px;
  overflow-x: auto;
  display: block;
}

.result-content :deep(th),
.result-content :deep(td) {
  border: 1px solid oklch(40% 0.02 280);
  padding: 8px 12px;
  text-align: left;
}

.result-content :deep(th) {
  background: oklch(35% 0.03 280);
  font-weight: 600;
  color: oklch(90% 0.01 250);
}

.result-content :deep(tr:nth-child(even)) {
  background: oklch(25% 0.02 280 / 0.5);
}

.result-content :deep(tr:hover) {
  background: oklch(35% 0.03 280 / 0.5);
}

.input-area {
  padding: 16px 20px;
  border-top: 1px solid oklch(30% 0.02 280);
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input {
  flex: 1;
  padding: 12px 16px;
  background: oklch(25% 0.02 280);
  border: 1px solid oklch(35% 0.02 280);
  border-radius: 14px;
  color: oklch(95% 0.01 250);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  resize: none;
  line-height: 1.5;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: oklch(50% 0.08 175 / 0.5);
}

.input:disabled {
  opacity: 0.6;
}

.input::placeholder {
  color: oklch(50% 0.02 250);
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: oklch(55% 0.12 175);
  border: none;
  color: oklch(100% 0 0);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 200ms ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: oklch(65% 0.15 175);
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>