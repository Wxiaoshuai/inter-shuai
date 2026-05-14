// API Composable for RAG & Agent interfaces
const API_BASE = '/api'

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' }
  }
  if (body) options.body = JSON.stringify(body)

  const res = await fetch(`${API_BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export function useApi() {
  // RAG Session APIs
  const ragSession = {
    create: (title) =>
      request('POST', '/rag/sessions', { title }),

    list: (limit = 50, offset = 0) =>
      request('GET', `/rag/sessions?limit=${limit}&offset=${offset}`),

    get: (sessionId) =>
      request('GET', `/rag/sessions/${sessionId}`),

    delete: (sessionId) =>
      request('DELETE', `/rag/sessions/${sessionId}`),

    updateTitle: (sessionId, title) =>
      request('PATCH', `/rag/sessions/${sessionId}/title`, { title }),

    addMessage: (sessionId, role, content, metadata = null) =>
      request('POST', `/rag/sessions/${sessionId}/messages`, { role, content, metadata }),

    getMessages: (sessionId) =>
      request('GET', `/rag/sessions/${sessionId}/messages`)
  }

  // RAG APIs
  const rag = {
    createIndex: (documents, collection, chunk_size = 500, chunk_overlap = 50) =>
      request('POST', '/rag/index/create', { documents, collection, chunk_size, chunk_overlap }),

    addDocuments: (collection, documents, chunk_size = 500, chunk_overlap = 50) =>
      request('POST', `/rag/index/${collection}`, { documents, chunk_size, chunk_overlap }),

    deleteIndex: (collection) =>
      request('DELETE', `/rag/index/${collection}`),

    search: (query, collection, k = 3) =>
      request('POST', '/rag/search', { query, collection, k }),

    ask: (question, collection, k = 3) =>
      request('POST', '/rag/ask', { question, collection, k }),

    getCollections: () =>
      request('GET', '/rag/collections'),

    getDocuments: (collection) =>
      request('GET', `/rag/documents?collection=${collection}`),

    deleteDocument: (docId) =>
      request('DELETE', `/rag/documents/${docId}`),

    createIndexWithDocs: (collection, documents) =>
      request('POST', '/rag/documents/create-index', { collection, documents })
  }

  // Agent APIs
  const agent = {
    create: (name, description, tools = [], max_iterations = 10) =>
      request('POST', '/agent/create', { name, description, tools, max_iterations }),

    list: () => request('GET', '/agent/list'),

    delete: (agentId) => request('DELETE', `/agent/${agentId}`),

    chat: (agentId, message, collection = null) =>
      request('POST', `/agent/${agentId}/chat`, { message, collection }),

    getHistory: (agentId) => request('GET', `/agent/${agentId}/history`),

    getState: (agentId) => request('GET', `/agent/${agentId}/state`),

    humanFeedback: (agentId, feedback) =>
      request('POST', `/agent/${agentId}/human-feedback`, { feedback }),

    uploadFile: (formData) =>
      fetch(`${API_BASE}/agent/file-upload`, {
        method: 'POST',
        body: formData
      }).then(res => {
        if (!res.ok) throw new Error('Upload failed')
        return res.json()
      }),

    processDocument: (fileId, requirements) =>
      request('POST', '/agent/process', { file_id: fileId, requirements }),

    getDownloadUrl: (filename) => `${API_BASE}/agent/download/${filename}`,

    deleteFile: (fileId) => request('DELETE', `/agent/file/${fileId}`),

    getGraph: () => request('GET', '/agent/graph')
  }

  return { rag, ragSession, agent }
}