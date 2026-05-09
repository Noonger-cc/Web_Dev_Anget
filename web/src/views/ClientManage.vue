<template>
  <div class="client-manage">
    <div class="page-header">
      <div class="header-left">
        <span class="icon">🔗</span>
        <div class="header-text">
          <h2>客户端管理</h2>
          <p>Client Management</p>
        </div>
      </div>
      <el-button type="primary" class="add-btn" @click="showAddDialog">
        <span>+ 添加客户端</span>
      </el-button>
    </div>

    <el-card class="main-card">
      <el-table :data="clients" class="tech-table">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="host" label="主机" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_heart" label="最后心跳" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_heart) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteClientHandler(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" class="tech-dialog">
      <el-form :model="clientForm" :rules="rules" ref="formRef" class="tech-form">
        <el-form-item label="名称" prop="name">
          <el-input v-model="clientForm.name" placeholder="请输入客户端名称" />
        </el-form-item>
        <el-form-item label="主机" prop="host">
          <el-input v-model="clientForm.host" placeholder="请输入主机地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button class="cancel-btn" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" class="confirm-btn" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getClients, addClient, updateClient, deleteClient } from '../api'

const clients = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('添加客户端')
const formRef = ref()
const editingId = ref(null)

const clientForm = reactive({
  name: '',
  host: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机', trigger: 'blur' }]
}

const loadClients = async () => {
  try {
    const res = await getClients()
    clients.value = res.data
  } catch {
    ElMessage.error('加载客户端列表失败')
  }
}

const showAddDialog = () => {
  dialogTitle.value = '添加客户端'
  clientForm.name = ''
  clientForm.host = ''
  editingId.value = null
  dialogVisible.value = true
}

const showEditDialog = (client) => {
  dialogTitle.value = '编辑客户端'
  clientForm.name = client.name
  clientForm.host = client.host
  editingId.value = client.id
  dialogVisible.value = true
}

const submitForm = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    if (editingId.value) {
      await updateClient(editingId.value, { name: clientForm.name, host: clientForm.host })
      ElMessage.success('更新成功')
    } else {
      await addClient({ name: clientForm.name, host: clientForm.host })
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadClients()
  } catch {
    ElMessage.error('操作失败')
  }
}

const deleteClientHandler = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除此客户端吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteClient(id)
    ElMessage.success('删除成功')
    loadClients()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString()
}

onMounted(() => {
  loadClients()
})
</script>

<style scoped>
.client-manage {
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

.add-btn {
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

.tech-dialog :deep(.el-dialog) {
  background: rgba(10, 14, 39, 0.95);
  border: 1px solid rgba(0, 243, 255, 0.2);
  border-radius: 16px;
}

.tech-dialog :deep(.el-dialog__title) {
  color: #00f3ff;
}

.tech-form :deep(.el-form-item__label) {
  color: #8b9eb7;
}

.tech-form :deep(.el-input__wrapper) {
  background: rgba(26, 31, 58, 0.8);
  border: 1px solid rgba(0, 243, 255, 0.2);
  border-radius: 8px;
  box-shadow: none;
}

.tech-form :deep(.el-input__inner) {
  color: #e0e6ed;
}

.confirm-btn {
  background: linear-gradient(135deg, #00f3ff 0%, #00ff88 100%);
  border: none;
  color: #0a0e27;
  font-weight: 600;
  border-radius: 8px;
}

.cancel-btn {
  background: rgba(107, 128, 154, 0.2);
  border: 1px solid rgba(107, 128, 154, 0.3);
  color: #8b9eb7;
  border-radius: 8px;
}
</style>
