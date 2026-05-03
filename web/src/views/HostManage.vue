<template>
  <div class="host-manage">
    <div class="page-header">
      <div class="header-left">
        <span class="icon">💻</span>
        <div class="header-text">
          <h2>主机管理</h2>
          <p>Host Management</p>
        </div>
      </div>
      <el-button type="primary" class="add-btn" @click="openAddDialog">
        <span class="btn-icon">+</span>
        添加主机
      </el-button>
    </div>
    
    <el-card class="main-card">
      <el-table 
        :data="hosts" 
        class="tech-table"
        :max-height="400"
      >
        <el-table-column prop="id" label="ID" width="60">
          <template #default="{ row }">
            <span class="id-text">#{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="主机名" width="120">
          <template #default="{ row }">
            <div class="name-cell">
              <span class="name-icon">🖥️</span>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="host" label="IP地址" width="140">
          <template #default="{ row }">
            <span class="ip-text">{{ row.host }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="port" label="端口" width="70">
          <template #default="{ row }">
            <span class="port-tag">{{ row.port }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="90">
          <template #default="{ row }">
            <span class="user-text">{{ row.username }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="auth_type" label="认证方式" width="90">
          <template #default="{ row }">
            <el-tag :type="row.auth_type === 'password' ? 'info' : 'success'" size="small">
              {{ row.auth_type === "password" ? "密码" : "密钥" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <div class="status-cell">
              <span class="status-dot" :class="row.status === 'online' ? 'online' : 'offline'"></span>
              <span>{{ row.status === "online" ? "在线" : "离线" }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="success" @click="openSsh(row)">
                <span>🔗</span>
                SSH
              </el-button>
              <el-button size="small" type="primary" @click="openEditDialog(row)">
                <span>✏️</span>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row.id)">
                <span>🗑️</span>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <SshTerminal
      v-if="sshHost"
      :visible="sshVisible"
      :host="sshHost"
      @close="sshVisible = false"
    />

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑主机' : '添加主机'"
      width="500px"
      class="tech-dialog"
    >
      <el-form
        :model="hostForm"
        :rules="rules"
        ref="formRef"
        label-width="100px"
        class="tech-form"
      >
        <el-form-item label="主机名" prop="name">
          <el-input v-model="hostForm.name" placeholder="请输入主机名" class="custom-input" />
        </el-form-item>
        <el-form-item label="IP地址" prop="host">
          <el-input v-model="hostForm.host" placeholder="请输入IP地址" class="custom-input" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="hostForm.port" :min="1" :max="65535" class="custom-input" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="hostForm.username" placeholder="请输入用户名" class="custom-input" />
        </el-form-item>
        <el-form-item label="认证方式" prop="auth_type">
          <el-radio-group v-model="hostForm.auth_type" class="custom-radio">
            <el-radio label="password">密码</el-radio>
            <el-radio label="key">密钥</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="密码/密钥" prop="credential">
          <el-input
            v-model="hostForm.credential"
            type="password"
            placeholder="请输入密码或密钥"
            class="custom-input"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" class="cancel-btn">取消</el-button>
        <el-button type="primary" @click="handleSubmit" class="confirm-btn">
          <span class="btn-icon">✅</span>
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { getHosts, addHost, updateHost, deleteHost } from "../api";
import SshTerminal from "../components/SshTerminal.vue";

const hosts = ref([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref();
const sshVisible = ref(false);
const sshHost = ref(null);

const hostForm = reactive({
  id: null,
  name: "",
  host: "",
  port: 22,
  username: "",
  auth_type: "password",
  credential: "",
});

const rules = {
  name: [{ required: true, message: "请输入主机名", trigger: "blur" }],
  host: [{ required: true, message: "请输入IP地址", trigger: "blur" }],
  port: [{ required: true, message: "请输入端口", trigger: "blur" }],
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  auth_type: [{ required: true, message: "请选择认证方式", trigger: "change" }],
  credential: [
    { required: true, message: "请输入密码或密钥", trigger: "blur" },
  ],
};

const loadHosts = async () => {
  try {
    const res = await getHosts();
    hosts.value = res.data || [];
  } catch (err) {
    ElMessage.error("获取主机列表失败");
  }
};

const openAddDialog = () => {
  isEdit.value = false;
  Object.assign(hostForm, {
    id: null,
    name: "",
    host: "",
    port: 22,
    username: "",
    auth_type: "password",
    credential: "",
  });
  dialogVisible.value = true;
};

const openEditDialog = (row) => {
  isEdit.value = true;
  Object.assign(hostForm, { ...row, credential: "" });
  dialogVisible.value = true;
};

const openSsh = (row) => {
  sshHost.value = row;
  sshVisible.value = true;
};

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  try {
    const data = { ...hostForm };
    delete data.id;
    if (isEdit.value) {
      await updateHost(hostForm.id, data);
      ElMessage.success("更新成功");
    } else {
      await addHost(data);
      ElMessage.success("添加成功");
    }
    dialogVisible.value = false;
    loadHosts();
  } catch (err) {
    ElMessage.error(err.message || "操作失败");
  }
};

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm("确定要删除该主机吗？", "提示", {
      type: "warning",
    });
    await deleteHost(id);
    ElMessage.success("删除成功");
    loadHosts();
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

onMounted(() => {
  loadHosts();
});
</script>

<style scoped>
.host-manage {
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

.header-text {
  display: flex;
  flex-direction: column;
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

.add-btn {
  background: linear-gradient(135deg, #00f3ff 0%, #00ff88 100%);
  border: none;
  color: #0a0e27;
  font-weight: 600;
  padding: 10px 22px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 243, 255, 0.3);
  transition: all 0.3s ease;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 243, 255, 0.5);
}

.btn-icon {
  margin-right: 6px;
}

.main-card {
  background: rgba(10, 14, 39, 0.7);
  border: 1px solid rgba(0, 243, 255, 0.15);
  border-radius: 16px;
  box-shadow: 
    0 0 30px rgba(0, 243, 255, 0.1),
    0 10px 40px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.main-card :deep(.el-card__body) {
  padding: 0;
}

.tech-table {
  width: 100%;
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

.id-text {
  color: #00f3ff;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-icon {
  font-size: 16px;
}

.ip-text {
  color: #8a2be2;
  font-family: 'Courier New', monospace;
}

.port-tag {
  background: rgba(0, 255, 136, 0.15);
  color: #00ff88;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.user-text {
  color: #6b809a;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: #00ff88;
  box-shadow: 0 0 8px #00ff88;
}

.status-dot.offline {
  background: #6b809a;
}

.action-buttons {
  display: flex;
  gap: 6px;
}

.action-buttons .el-button {
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
}

.action-buttons span {
  margin-right: 3px;
}

.tech-dialog :deep(.el-dialog) {
  background: rgba(10, 14, 39, 0.95);
  border: 1px solid rgba(0, 243, 255, 0.2);
  border-radius: 16px;
}

.tech-dialog :deep(.el-dialog__title) {
  color: #00f3ff;
  font-size: 16px;
}

.tech-form :deep(.el-form-item__label) {
  color: #8b9eb7;
  font-size: 13px;
}

.tech-form :deep(.el-input__wrapper) {
  background: rgba(26, 31, 58, 0.8);
  border: 1px solid rgba(0, 243, 255, 0.2);
  border-radius: 8px;
}

.tech-form :deep(.el-input__wrapper.is-focus) {
  border-color: #00f3ff;
}

.cancel-btn {
  background: rgba(107, 128, 154, 0.2);
  border: 1px solid rgba(107, 128, 154, 0.3);
  color: #8b9eb7;
  border-radius: 8px;
}

.confirm-btn {
  background: linear-gradient(135deg, #00f3ff 0%, #00ff88 100%);
  border: none;
  color: #0a0e27;
  font-weight: 600;
  border-radius: 8px;
}
</style>