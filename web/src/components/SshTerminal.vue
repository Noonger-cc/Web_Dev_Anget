<template>
  <el-dialog
    :model-value="visible"
    :title="`SSH 连接 - ${host.name} (${host.host}:${host.port})`"
    width="900px"
    :close-on-click-modal="false"
    :close-on-press-escape="true"
    @update:model-value="$emit('close')"
    @opened="focusInput"
  >
    <div class="ssh-terminal">
      <div class="terminal-header">
        <span class="terminal-title">{{ host.name }}</span>
        <div class="terminal-controls">
          <el-button size="small" @click="sendCtrlC">Ctrl+C</el-button>
          <el-button size="small" @click="clearTerminal">清空</el-button>
          <el-button size="small" @click="disconnect">断开连接</el-button>
        </div>
      </div>
      <div ref="terminalOutput" class="terminal-output">
        <div v-for="(line, index) in outputLines" :key="index" :class="line.type">
          {{ line.text }}
        </div>
      </div>
      <div class="terminal-input">
        <span class="prompt">{{ host.username }}@{{ host.host }}:</span>
        <input
          ref="inputRef"
          v-model="command"
          @keydown.enter="sendCommand"
          @keydown.tab="handleTab"
          class="command-input"
          :disabled="!connected"
          placeholder="输入命令..."
          tabindex="0"
        />
      </div>
    </div>
    <template #footer>
      <el-button @click="disconnect">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  host: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["close"]);

const terminalOutput = ref(null);
const inputRef = ref(null);
const command = ref("");
const outputLines = ref([]);
const connected = ref(false);
const history = ref([]);
const historyIndex = ref(-1);

const focusInput = async () => {
  await nextTick();
  if (inputRef.value) {
    inputRef.value.focus();
  }
};

const appendOutput = (text, type = "output") => {
  outputLines.value.push({ text, type });
  nextTick(() => {
    if (terminalOutput.value) {
      terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight;
    }
  });
};

const connect = async () => {
  try {
    appendOutput(`正在连接 ${host.host}:${host.port}...`, "info");
    
    const response = await fetch("/api/ssh/connect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        host_id: props.host.id,
      }),
    });

    const result = await response.json();
    if (result.success) {
      connected.value = true;
      appendOutput(`连接成功！欢迎来到 ${props.host.name}`, "success");
      appendOutput(`${props.host.username}@${props.host.host}:~$`, "prompt");
      await focusInput();
    } else {
      appendOutput(`连接失败: ${result.message}`, "error");
    }
  } catch (err) {
    appendOutput(`连接错误: ${err.message}`, "error");
  }
};

const sendCommand = async () => {
  if (!command.value.trim() || !connected.value) return;

  appendOutput(`${props.host.username}@${props.host.host}:~$ ${command.value}`, "input");
  history.value.push(command.value);
  historyIndex.value = -1;

  try {
    const response = await fetch("/api/ssh/execute", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        host_id: props.host.id,
        command: command.value,
      }),
    });

    const result = await response.json();
    if (result.success) {
      appendOutput(result.output, "output");
    } else {
      appendOutput(result.message, "error");
    }
  } catch (err) {
    appendOutput(`执行错误: ${err.message}`, "error");
  }

  command.value = "";
  appendOutput(`${props.host.username}@${props.host.host}:~$`, "prompt");
  await focusInput();
};

const sendCtrlC = () => {
  appendOutput("^C", "error");
  appendOutput(`${props.host.username}@${props.host.host}:~$`, "prompt");
  focusInput();
};

const clearTerminal = () => {
  outputLines.value = [];
};

const disconnect = () => {
  connected.value = false;
  emit("close");
};

const handleTab = (e) => {
  e.preventDefault();
};

watch(() => props.visible, (newVal) => {
  if (newVal) {
    outputLines.value = [];
    connected.value = false;
    command.value = "";
    nextTick(() => {
      connect();
    });
  }
});
</script>

<style scoped>
.ssh-terminal {
  display: flex;
  flex-direction: column;
  height: 400px;
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
}

.terminal-title {
  color: #ccc;
  font-size: 14px;
}

.terminal-controls {
  display: flex;
  gap: 8px;
}

.terminal-output {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.terminal-output .prompt {
  color: #4ec9b0;
}

.terminal-output .input {
  color: #dcdcdc;
}

.terminal-output .output {
  color: #ccc;
}

.terminal-output .success {
  color: #6a9955;
}

.terminal-output .error {
  color: #f14c4c;
}

.terminal-output .info {
  color: #569cd6;
}

.terminal-input {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background: #2d2d2d;
  border-top: 1px solid #3d3d3d;
}

.prompt {
  color: #4ec9b0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  margin-right: 8px;
}

.command-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #dcdcdc;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  padding: 4px 0;
  caret-color: #fff;
}

.command-input::placeholder {
  color: #666;
}

.command-input:disabled {
  opacity: 0.5;
}
</style>