<template>
  <div class="ai-assistant">
    <div class="chat-container">
      <div class="chat-header">
        <div class="agent-status">
          <span class="status-indicator" :class="{ online: !store.thinking, thinking: store.thinking }"></span>
          <span>LangGraph Agent {{ store.thinking ? '思考中...' : '就绪' }}</span>
        </div>
        <div class="header-actions">
          <el-button text @click="showSettings = true" class="settings-btn" title="LLM 设置">⚙️ 设置</el-button>
          <el-button text @click="store.clear()" class="clear-btn">清空对话</el-button>
        </div>
      </div>

      <div class="chat-messages" ref="msgContainer">
        <div v-if="store.messages.length === 0" class="welcome">
          <div class="welcome-icon">🤖</div>
          <h3>LangGraph 智能运维 Agent</h3>
          <p>我可以帮你管理服务器、诊断故障、监控系统状态</p>
          <div class="quick-prompts">
            <span class="prompt-tag" @click="sendQuick('检查所有主机状态')">检查所有主机状态</span>
            <span class="prompt-tag" @click="sendQuick('查看最近的告警信息')">查看最近的告警信息</span>
            <span class="prompt-tag" @click="sendQuick('服务器CPU高了怎么办')">服务器CPU高了怎么办</span>
            <span class="prompt-tag" @click="sendQuick('运行 yum update -y')">运行 yum update -y</span>
          </div>
        </div>

        <div v-for="msg in store.messages" :key="msg.id" class="msg-row" :class="msg.role">
          <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="msg-body">
            <div class="msg-meta">
              <span class="msg-role">{{ msg.role === 'user' ? '你' : 'Agent' }}</span>
              <span class="msg-time">{{ formatTime(msg.id) }}</span>
            </div>
            <div class="msg-content" v-html="renderContent(msg.content)"></div>
            <div v-if="msg.tool" class="msg-tool">
              <span class="tool-badge">🔧 {{ msg.tool }}</span>
              <pre v-if="msg.toolOutput" class="tool-output">{{ msg.toolOutput }}</pre>
            </div>
          </div>
        </div>

        <div v-if="store.thinking" class="msg-row agent">
          <div class="msg-avatar">🤖</div>
          <div class="msg-body">
            <div class="thinking-dots">
              <span></span><span></span><span></span>
            </div>
            <span v-if="store.currentTool" class="tool-active">调用工具: {{ store.currentTool }}</span>
          </div>
        </div>
      </div>

      <div class="chat-input-area">
        <el-input
          v-model="inputMsg"
          type="textarea"
          :rows="2"
          placeholder="输入运维指令，Agent 将自动规划并执行..."
          @keydown.enter.exact="send"
          :disabled="store.thinking"
          resize="none"
        />
        <el-button
          type="primary"
          @click="send"
          :loading="store.thinking"
          :disabled="!inputMsg.trim()"
          class="send-btn"
        >
          {{ store.thinking ? '处理中' : '发送' }}
        </el-button>
      </div>
    </div>
  </div>

    <!-- LLM Settings Dialog -->
    <el-dialog v-model="showSettings" title="LLM 模型设置" width="480px" class="dark-dialog">
      <el-form :model="llmSettings" label-width="100px">
        <el-alert
          title="如不填写则使用服务端默认配置"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        />
        <el-form-item label="API Key">
          <el-input v-model="llmSettings.api_key" type="password" show-password placeholder="sk-..." />
          <div class="form-hint">支持 OpenAI / DeepSeek 等兼容 API 的 Key</div>
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="llmSettings.base_url" placeholder="https://api.deepseek.com/v1" />
          <div class="form-hint">API 地址，留空则使用默认</div>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="llmSettings.model" placeholder="deepseek-chat" />
          <div class="form-hint">如 deepseek-chat / gpt-4o / qwen-plus 等</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { chatStore as store } from '../stores/chat.js'

const inputMsg = ref('')
const msgContainer = ref(null)
let reader = null
let abortCtrl = null

// LLM Settings
const showSettings = ref(false)
const llmSettings = ref({
  api_key: localStorage.getItem('llm_api_key') || '',
  base_url: localStorage.getItem('llm_base_url') || '',
  model: localStorage.getItem('llm_model') || '',
})

const saveSettings = () => {
  localStorage.setItem('llm_api_key', llmSettings.value.api_key)
  localStorage.setItem('llm_base_url', llmSettings.value.base_url)
  localStorage.setItem('llm_model', llmSettings.value.model)
  showSettings.value = false
  store.addMessage('system', 'LLM 设置已保存 ✅')
}

const formatTime = (ts) => {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const renderContent = (text) => {
  if (!text) return ''
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\n/g, '<br>')
}

const scrollBottom = async () => {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

const sendQuick = (text) => {
  inputMsg.value = text
  send()
}

const send = async () => {
  const text = inputMsg.value.trim()
  if (!text || store.thinking) return

  store.addMessage('user', text)
  inputMsg.value = ''
  store.setThinking(true)
  await scrollBottom()

  // Add a placeholder agent message for streaming
  store.addMessage('agent', '')
  const agentMsg = store.messages[store.messages.length - 1]

  abortCtrl = new AbortController()

  try {
    const resp = await fetch('/api/agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        thread_id: store.threadId,
        llm_config: llmSettings.value.api_key ? {
          api_key: llmSettings.value.api_key,
          base_url: llmSettings.value.base_url || undefined,
          model: llmSettings.value.model || undefined
        } : undefined
      }),
      signal: abortCtrl.signal
    })

    reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const eventType = line.startsWith('event: ') ? '' : ''
        let dataStr = line
        if (line.startsWith('data: ')) {
          dataStr = line.slice(6)
        }
        // Parse SSE: sometimes event and data come as separate lines
        // Handle simple case - data on same line
        try {
          const parsed = JSON.parse(dataStr)
          handleSSE(parsed, agentMsg, eventType)
        } catch {
          // might be event line, skip
        }
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      agentMsg.content = '请求失败: ' + err.message
    }
  } finally {
    store.setThinking(false)
    store.setCurrentTool('')
    reader = null
    abortCtrl = null
    await scrollBottom()
  }
}

// Track pending events across lines
let pendingEvent = ''

const handleSSE = (parsed, agentMsg) => {
  // If we have a pending event type from previous line
  const evType = pendingEvent || parsed.event || ''
  // data-only lines may have event already embedded
  pendingEvent = ''

  if (parsed.content !== undefined) {
    if (parsed.event === 'thinking' || evType === 'thinking') {
      // Just show thinking indicator, don't accumulate
    } else if (parsed.event === 'tool_start') {
      store.setCurrentTool(parsed.tool)
    } else if (parsed.event === 'tool_end') {
      agentMsg.tool = parsed.tool
      agentMsg.toolOutput = parsed.output?.substring(0, 500)
      store.setCurrentTool('')
    } else if (parsed.event === 'done') {
      agentMsg.content = parsed.report || parsed.content || ''
      store.threadId = parsed.thread_id || store.threadId
    } else if (parsed.event === 'message') {
      agentMsg.content += parsed.content || ''
    } else if (parsed.event === 'error') {
      agentMsg.content = '错误: ' + (parsed.message || '')
    } else {
      // generic content append
      agentMsg.content += parsed.content || ''
    }
  }

  if (parsed.report) {
    agentMsg.content = parsed.report
  }
  if (parsed.thread_id) {
    store.threadId = parsed.thread_id
  }

  scrollBottom()
}

onUnmounted(() => {
  if (abortCtrl) abortCtrl.abort()
})
</script>

<style scoped>
.ai-assistant {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(10, 14, 39, 0.6);
  border: 1px solid rgba(0, 243, 255, 0.12);
  border-radius: 12px;
  overflow: hidden;
  height: calc(100vh - 140px);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 243, 255, 0.1);
  background: rgba(0, 243, 255, 0.03);
  flex-shrink: 0;
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #c8d6e5;
  font-size: 14px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.online {
  background: #00ff88;
  box-shadow: 0 0 8px #00ff88;
}

.status-indicator.thinking {
  background: #ffa502;
  box-shadow: 0 0 8px #ffa502;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.header-actions {
  display: flex;
  gap: 8px;
}

.clear-btn, .settings-btn {
  color: #6b809a;
}

.settings-btn:hover {
  color: #00f3ff;
}

.clear-btn:hover {
  color: #ff4757;
}

.form-hint {
  font-size: 11px;
  color: #4a5a7a;
  margin-top: 4px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome h3 {
  color: #00f3ff;
  font-size: 22px;
  margin: 0 0 8px 0;
}

.welcome p {
  color: #6b809a;
  margin: 0 0 24px 0;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.prompt-tag {
  padding: 8px 16px;
  background: rgba(0, 243, 255, 0.08);
  border: 1px solid rgba(0, 243, 255, 0.2);
  border-radius: 20px;
  color: #00f3ff;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.prompt-tag:hover {
  background: rgba(0, 243, 255, 0.18);
  border-color: rgba(0, 243, 255, 0.4);
}

.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.msg-row.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 243, 255, 0.1);
  font-size: 18px;
  flex-shrink: 0;
}

.msg-row.user .msg-avatar {
  background: rgba(138, 43, 226, 0.15);
}

.msg-body {
  max-width: 75%;
}

.msg-row.user .msg-body {
  text-align: right;
}

.msg-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 4px;
  font-size: 12px;
}

.msg-row.user .msg-meta {
  justify-content: flex-end;
}

.msg-role {
  color: #00f3ff;
  font-weight: 600;
}

.msg-time {
  color: #4a5a7a;
}

.msg-content {
  color: #c8d6e5;
  line-height: 1.7;
  word-break: break-word;
}

.msg-row.user .msg-content {
  background: rgba(0, 243, 255, 0.1);
  border-radius: 12px 4px 12px 12px;
  padding: 12px 16px;
}

.msg-row.agent .msg-content {
  background: rgba(10, 14, 39, 0.6);
  border: 1px solid rgba(0, 243, 255, 0.1);
  border-radius: 4px 12px 12px 12px;
  padding: 12px 16px;
}

.msg-content :deep(.code-block) {
  background: #0a0e27;
  border: 1px solid rgba(0, 243, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #00ff88;
  margin: 8px 0;
}

.msg-content :deep(.inline-code) {
  background: rgba(0, 243, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #00f3ff;
}

.msg-tool {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(255, 165, 2, 0.08);
  border: 1px solid rgba(255, 165, 2, 0.2);
  border-radius: 8px;
}

.tool-badge {
  color: #ffa502;
  font-size: 13px;
}

.tool-output {
  margin: 6px 0 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  color: #8b9eb7;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.thinking-dots {
  display: inline-flex;
  gap: 4px;
  margin-right: 10px;
}

.thinking-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ffa502;
  animation: dotBounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }
.thinking-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.6); }
  40% { transform: scale(1); }
}

.tool-active {
  color: #ffa502;
  font-size: 13px;
}

.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 243, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.chat-input-area :deep(.el-textarea__inner) {
  background: rgba(10, 14, 39, 0.8);
  border-color: rgba(0, 243, 255, 0.2);
  color: #c8d6e5;
}

.chat-input-area :deep(.el-textarea__inner:focus) {
  border-color: rgba(0, 243, 255, 0.5);
}

.send-btn {
  align-self: flex-end;
  background: linear-gradient(135deg, #00f3ff 0%, #0088ff 100%);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  min-width: 80px;
}

.send-btn:hover {
  box-shadow: 0 0 20px rgba(0, 243, 255, 0.4);
}
</style>
