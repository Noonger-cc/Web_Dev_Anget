<template>
  <div class="task-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <el-button type="primary" @click="loadTasks">刷新</el-button>
        </div>
      </template>
      <el-table :data="tasks" border stripe v-loading="loading">
        <el-empty v-if="tasks.length === 0 && !loading" description="暂无任务" />
        <el-table-column v-else prop="id" label="ID" width="80" />
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
  router.push({ path: "/main/task-log", query: { taskId: row.id } });
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
