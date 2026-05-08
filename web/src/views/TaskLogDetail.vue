<template>
  <div class="task-log-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务日志详情</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <div v-if="task" class="task-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ task.id }}</el-descriptions-item>
          <el-descriptions-item label="任务名称">{{ task.name }}</el-descriptions-item>
          <el-descriptions-item label="执行方式">{{ task.exec_type === 'ssh' ? 'SSH' : '客户端' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ task.created_at }}</el-descriptions-item>
          <el-descriptions-item label="结果">{{ task.result || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="logs-section">
        <h3>执行日志</h3>
        <el-card class="log-card">
          <pre class="log-content">{{ task ? task.logs : '加载中...' }}</pre>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTasks } from '@/api/index.js'

export default {
  name: 'TaskLogDetail',
  setup() {
    const route = useRoute()
    const task = ref(null)

    const getStatusType = (status) => {
      const map = {
        pending: 'info',
        running: 'primary',
        success: 'success',
        failed: 'danger'
      }
      return map[status] || 'info'
    }

    const getStatusText = (status) => {
      const map = {
        pending: '待执行',
        running: '执行中',
        success: '成功',
        failed: '失败'
      }
      return map[status] || status
    }

    const loadTaskDetail = async () => {
      try {
        const res = await getTasks()
        const tasks = res.data || []
        const taskId = parseInt(route.params.id)
        task.value = tasks.find(t => t.id === taskId)
        if (!task.value) {
          ElMessage.error('任务不存在')
        }
      } catch (error) {
        ElMessage.error('加载任务详情失败')
      }
    }

    onMounted(() => {
      loadTaskDetail()
    })

    return {
      task,
      getStatusType,
      getStatusText
    }
  }
}
</script>

<style scoped>
.task-log-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-info {
  margin-bottom: 20px;
}

.logs-section h3 {
  margin-bottom: 10px;
  color: #409eff;
}

.log-card {
  max-height: 600px;
  overflow-y: auto;
}

.log-content {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}
</style>