<template>
  <div class="rag">
    <div class="wrapper">
      <!-- Sidebar -->
      <div class="sidebar">
        <div class="sidebar-header">
          <span class="sidebar-title">对话</span>
          <button class="new-chat-btn" @click="createNewChat">
            <span>+</span>
            <span>新建</span>
          </button>
        </div>

        <div class="history-list">
          <div v-if="conversations.length === 0" class="empty-hint">
            暂无历史对话
          </div>
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="history-item"
            :class="{ active: currentConvId === conv.id }"
            @click="selectConversation(conv)"
          >
            <span class="history-icon">◎</span>
            <span class="history-title">{{ conv.title }}</span>
            <button class="conv-delete-btn" @click.stop="deleteConversation(conv.id)">×</button>
          </div>
        </div>

        <div class="doc-list-section">
          <div class="doc-list-header">
            <span class="sidebar-title">索引文档</span>
          </div>
          <div class="doc-list">
            <div v-if="sessionDocuments.length === 0" class="empty-hint">
              暂无文档
            </div>
            <div
              v-for="doc in sessionDocuments"
              :key="doc.id"
              class="doc-item"
            >
              <span class="doc-icon">📄</span>
              <span class="doc-name">{{ doc.name }}</span>
              <button class="doc-delete-btn" @click="deleteDocument(doc.id)">×</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Main chat area -->
      <div class="main">
        <!-- Document section -->
        <div class="doc-section">
          <label class="doc-btn">
            <input
              type="file"
              accept=".txt,.md"
              multiple
              style="display: none"
              @change="handleFileUpload"
            />
            ↑ 上传
          </label>
          <button
            class="doc-btn"
            :class="{ loading: isIndexing }"
            :disabled="isIndexing || uploadedFiles.length === 0"
            @click="createIndex"
          >
            {{ isIndexing ? '创建中...' : '◎ 创建索引' }}
          </button>
          <span class="index-status">
            {{ uploadedFiles.length > 0
              ? `已上传 ${uploadedFiles.length} 个文档`
              : collections.length > 0
                ? `索引: ${collections.length} 个集合`
                : '未创建索引' }}
          </span>
        </div>

        <!-- Messages -->
        <div class="messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <span class="empty-icon">◎</span>
            <span>开始新对话，或上传文档创建索引</span>
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
            <div class="message-content" :class="msg.role" v-html="renderMarkdown(msg.content)"></div>
          </div>

          <div v-if="isLoading" class="message-wrap assistant">
            <div class="message-avatar">◎</div>
            <div class="message-content">思考中...</div>
          </div>
          <div ref="messagesEnd" />
        </div>

        <!-- Input -->
        <div class="input-area">
          <textarea
            ref="inputRef"
            v-model="inputText"
            class="input"
            placeholder="输入消息..."
            rows="1"
            @keydown.enter.exact="handleEnter"
            @focus="inputFocused = true"
            @blur="inputFocused = false"
          />
          <button
            class="send-btn"
            :disabled="isLoading || !inputText.trim()"
            @click="sendMessage"
          >
            ↑
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

const { rag, ragSession } = useApi()
const toast = inject('toast')
const confirm = inject('confirm')

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

const conversations = ref([])
const currentConvId = ref(null)
const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const isIndexing = ref(false)
const collections = ref([])
const uploadedFiles = ref([])
const sessionDocuments = ref([])
const inputFocused = ref(false)
const messagesEnd = ref(null)
const messagesContainer = ref(null)

const loadConversations = async () => {
  try {
    const data = await ragSession.list(50, 0)
    conversations.value = data.sessions || []
  } catch (e) {
    console.warn('Failed to load sessions:', e)
  }
}

const loadCollections = async () => {
  try {
    const data = await rag.getCollections()
    collections.value = data.collections || []
  } catch (e) {
    console.warn('Failed to load collections:', e)
  }
}

const loadDocuments = async (collection = 'default') => {
  try {
    const data = await rag.getDocuments(collection)
    sessionDocuments.value = data.documents || []
  } catch (e) {
    console.warn('Failed to load documents:', e)
  }
}

const loadMessages = async (sessionId) => {
  try {
    const data = await ragSession.getMessages(sessionId)
    messages.value = data.messages || []
  } catch (e) {
    console.warn('Failed to load messages:', e)
  }
}

const createNewChat = async () => {
  try {
    const session = await ragSession.create()
    conversations.value.unshift(session)
    currentConvId.value = session.id
    messages.value = []
    inputRef.value?.focus()
    return session
  } catch (e) {
    console.error('Failed to create session:', e)
    throw e
  }
}

const selectConversation = async (conv) => {
  currentConvId.value = conv.id
  await loadMessages(conv.id)
}

const deleteConversation = async (convId) => {
  const ok = await confirm.show({
    title: '删除对话',
    message: '确定要删除此对话吗？删除后无法恢复。',
    confirmText: '删除',
    confirmType: 'danger',
  })
  if (!ok) return

  try {
    await ragSession.delete(convId)
    conversations.value = conversations.value.filter(c => c.id !== convId)
    toast.show('对话已删除', 'success')
    if (currentConvId.value === convId) {
      currentConvId.value = null
      messages.value = []
      if (conversations.value.length > 0) {
        await selectConversation(conversations.value[0])
      }
    }
  } catch (e) {
    toast.show('删除失败: ' + e.message, 'error')
  }
}

const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    return marked.parse(content)
  } catch (e) {
    return content
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

const sendMessage = async () => {
  console.log('sendMessage called', { inputText: inputText.value, isLoading: isLoading.value, currentConvId: currentConvId.value })
  if (!inputText.value.trim() || isLoading.value) {
    console.log('sendMessage early return')
    return
  }

  // Auto-create session if none exists
  if (!currentConvId.value) {
    console.log('Auto creating session')
    await createNewChat()
    if (!currentConvId.value) {
      toast.show('请先创建新对话', 'warning')
      return
    }
  }

  const userMsg = { role: 'user', content: inputText.value.trim() }
  messages.value.push(userMsg)
  inputText.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    console.log('Calling ragSession.addMessage', currentConvId.value)
    await ragSession.addMessage(currentConvId.value, 'user', userMsg.content)

    console.log('Calling rag.ask', userMsg.content)
    const response = await rag.ask(userMsg.content, 'default')
    console.log('rag.ask response:', response)
    const aiMsg = { role: 'assistant', content: response.answer }

    await ragSession.addMessage(currentConvId.value, 'assistant', aiMsg.content)

    messages.value.push(aiMsg)
  } catch (e) {
    console.error('Send message error:', e)
    const errorMsg = { role: 'assistant', content: `抱歉出现问题: ${e.message}` }
    messages.value.push(errorMsg)
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const handleEnter = (e) => {
  if (!e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const handleFileUpload = async (e) => {
  const files = Array.from(e.target.files || [])
  if (!files.length) return

  const textFiles = files.filter(f =>
    f.name.endsWith('.txt') || f.name.endsWith('.md')
  )

  if (textFiles.length === 0) {
    toast.show('目前只支持 .txt 和 .md 文件', 'warning')
    return
  }

  for (const file of textFiles) {
    const content = await file.text()
    uploadedFiles.value.push({ name: file.name, content })
  }
}

const createIndex = async () => {
  if (uploadedFiles.value.length === 0) {
    toast.show('请先上传文档', 'warning')
    return
  }

  isIndexing.value = true
  try {
    const documents = uploadedFiles.value.map(f => ({
      content: f.content,
      metadata: { source: f.name }
    }))

    await rag.createIndexWithDocs('default', documents)
    toast.show('索引创建成功！', 'success')
    loadCollections()
    loadDocuments()
    uploadedFiles.value = []
  } catch (e) {
    toast.show('索引创建失败: ' + e.message, 'error')
  } finally {
    isIndexing.value = false
  }
}

const deleteDocument = async (docId) => {
  const ok = await confirm.show({
    title: '删除文档',
    message: '确定要删除此文档吗？删除后关联索引也会被移除。',
    confirmText: '删除',
    confirmType: 'danger',
  })
  if (!ok) return

  try {
    await rag.deleteDocument(docId)
    toast.show('文档已删除', 'success')
    await loadDocuments()
    await loadCollections()
  } catch (e) {
    toast.show('删除失败: ' + e.message, 'error')
  }
}

onMounted(async () => {
  await loadConversations()
  await loadCollections()
  await loadDocuments()

  // Auto-load latest conversation if available
  if (conversations.value.length > 0) {
    await selectConversation(conversations.value[0])
  }
})
</script>

<style scoped>
.rag {
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

.history-item:hover .conv-delete-btn {
  opacity: 0.6;
}

.history-item.active {
  background: oklch(35% 0.03 175 / 0.2);
  border-color: oklch(50% 0.08 175 / 0.3);
}

.conv-delete-btn {
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

.conv-delete-btn:hover {
  opacity: 1 !important;
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

.doc-list-section {
  border-top: 1px solid oklch(30% 0.02 280);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
}

.doc-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.doc-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.doc-item {
  padding: 8px 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: oklch(25% 0.02 280);
  border: 1px solid oklch(35% 0.02 280);
}

.doc-icon {
  font-size: 14px;
}

.doc-name {
  flex: 1;
  font-size: 12px;
  color: oklch(75% 0.01 250);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-delete-btn {
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
  opacity: 0.6;
  transition: opacity 150ms ease;
}

.doc-delete-btn:hover {
  opacity: 1;
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

.doc-section {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: oklch(22% 0.015 280);
  border-bottom: 1px solid oklch(30% 0.02 280);
}

.doc-btn {
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

.doc-btn:hover:not(:disabled) {
  background: oklch(40% 0.05 175 / 0.4);
}

.doc-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.doc-btn.loading {
  background: oklch(35% 0.05 175 / 0.3);
  border-color: oklch(55% 0.1 175 / 0.4);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.doc-btn.loading::before {
  content: '◌';
  display: inline-block;
  animation: spin 1s linear infinite;
  margin-right: 4px;
}

.index-status {
  flex: 1;
  font-size: 12px;
  color: oklch(55% 0.02 250);
  text-align: right;
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

/* Markdown content styles */
.message-content :deep(pre) {
  background: oklch(25% 0.02 280);
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(code) {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
}

.message-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.message-content :deep(p:not(:last-child)) {
  margin-bottom: 8px;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(blockquote) {
  border-left: 3px solid oklch(55% 0.1 175);
  margin: 8px 0;
  padding-left: 12px;
  color: oklch(65% 0.02 250);
}

.message-content :deep(a) {
  color: oklch(70% 0.15 175);
}

.message-content :deep(strong) {
  color: oklch(90% 0.01 250);
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid oklch(40% 0.02 280);
  padding: 6px 10px;
  text-align: left;
}

.message-content :deep(th) {
  background: oklch(30% 0.02 280);
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