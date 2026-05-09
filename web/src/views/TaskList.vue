<template>
  <div class="task-list">
    <div class="page-header">
      <div class="header-left">
        <span class="icon">📋</span>
        <div class="header-text">
          <h2>任务列表</h2>
          <p>Task List</p>
        </div>
      </div>
      <el-button type="primary" class="refresh-btn" @click="loadTasks">
        <span>🔄 刷新</span>
      </el-button>
    </div>

    <el-card class="main-card">
      <el-table :data="tasks" border stripe v-loading="loading" class="tech-table">
        <template #empty>
          <el-empty description="暂无任务" />
        </template>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="exec_type" label="执行方式" width="100">
          <template #default="{ row }">
            {{ row.exec_type === "ssh" ? "SSH" : "客户端" }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{
              getStatusText(row.status)
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="result" label="结果" show-overflow-tooltip />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewLog(row)"
              >查看日志</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getTasks } from "../api";

const router = useRouter();
const tasks = ref([]);
const loading = ref(false);
let refreshTimer = null;

const getStatusType = (status) => {
  const map = {
    pending: "info",
    running: "primary",
    success: "success",
    failed: "danger",
  };
  return map[status] || "info";
};

const getStatusText = (status) => {
  const map = {
    pending: "待执行",
    running: "执行中",
    success: "成功",
    failed: "失败",
  };
  return map[status] || status;
};

const loadTasks = async () => {
  loading.value = true;
  try {
    const res = await getTasks();
    tasks.value = res.data || [];
  } catch (err) {
    ElMessage.error("获取任务列表失败");
  } finally {
    loading.value = false;
  }
};

const viewLog = (row) => {
  router.push({ name: 'TaskLogDetail', params: { id: row.id } });
};

onMounted(() => {
  loadTasks();
  refreshTimer = setInterval(loadTasks, 30000);
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<style scoped>
.task-list {
  color: #e0e6ed;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 24px;
  background: rgba(10, 14, 39, 0.6);
  border-radius: 16px;
  border: 1px solid rgba(0, 243, 255, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-left .icon {
  font-size: 32px;
}

.header-text h2 {
  margin: 0;
  color: #00f3ff;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
}

.header-text p {
  margin: 0;
  color: #6b809a;
  font-size: 12px;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.refresh-btn {
  background: linear-gradient(135deg, #00f3ff 0%, #00ff88 100%);
  border: none;
  color: #0a0e27;
  font-weight: 600;
  padding: 10px 22px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 243, 255, 0.3);
}

.main-card {
  background: rgba(10, 14, 39, 0.7);
  border: 1px solid rgba(0, 243, 255, 0.15);
  border-radius: 16px;
  box-shadow: 0 0 30px rgba(0, 243, 255, 0.1), 0 10px 40px rgba(0, 0, 0, 0.4);
}

.main-card :deep(.el-card__body) {
  padding: 0;
}

.tech-table :deep(.el-table__header-wrapper) {
  background: rgba(26, 31, 58, 0.8);
}

.tech-table :deep(.el-table th) {
  color: #00f3ff;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid rgba(0, 243, 255, 0.2);
  background: transparent;
}

.tech-table :deep(.el-table td) {
  color: #e0e6ed;
  font-size: 13px;
  border-bottom: 1px solid rgba(0, 243, 255, 0.08);
  background: transparent;
}

.tech-table :deep(.el-table__body tr:hover > td) {
  background: rgba(0, 243, 255, 0.05);
}

.tech-table :deep(.el-table) {
  background: transparent;
}

.tech-table :deep(.el-table__empty-block) {
  background: transparent;
}
</style>
