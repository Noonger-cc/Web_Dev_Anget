<template>
  <div class="client-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>客户端管理</span>
          <el-button type="primary" @click="showAddDialog">添加客户端</el-button>
        </div>
      </template>

      <el-table :data="clients" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="name" label="名称"></el-table-column>
        <el-table-column prop="host" label="主机"></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'online' ? 'success' : 'danger'">
              {{ scope.row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_heart" label="最后心跳" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.last_heart) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="showEditDialog(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteClient(scope.row.id)">删除</el-button>
            <el-button size="small" type="warning" @click="sendCommand(scope.row.id)">发送命令</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="clientForm" :rules="rules" ref="formRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="clientForm.name" placeholder="请输入客户端名称"></el-input>
        </el-form-item>
        <el-form-item label="主机" prop="host">
          <el-input v-model="clientForm.host" placeholder="请输入主机地址"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 发送命令对话框 -->
    <el-dialog v-model="cmdDialogVisible" title="发送命令" width="500px">
      <el-form :model="cmdForm" :rules="cmdRules" ref="cmdFormRef">
        <el-form-item label="命令" prop="command">
          <el-input v-model="cmdForm.command" placeholder="请输入要执行的命令"></el-input>
        </el-form-item>
        <el-form-item label="任务ID" prop="taskId">
          <el-input-number v-model="cmdForm.taskId" :min="1" placeholder="关联的任务ID"></el-input-number>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cmdDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCommand">发送</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getClients, addClient, updateClient, deleteClient, sendClientCmd } from '@/api'

export default {
  name: 'ClientManage',
  setup() {
    const clients = ref([])
    const dialogVisible = ref(false)
    const dialogTitle = ref('添加客户端')
    const clientForm = ref({
      name: '',
      host: ''
    })
    const rules = {
      name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
      host: [{ required: true, message: '请输入主机', trigger: 'blur' }]
    }
    const formRef = ref(null)
    const editingId = ref(null)

    const cmdDialogVisible = ref(false)
    const cmdForm = ref({
      command: '',
      taskId: null
    })
    const cmdRules = {
      command: [{ required: true, message: '请输入命令', trigger: 'blur' }],
      taskId: [{ required: true, message: '请输入任务ID', trigger: 'blur' }]
    }
    const cmdFormRef = ref(null)
    const currentClientId = ref(null)

    const loadClients = async () => {
      try {
        const res = await getClients()
        clients.value = res.data
      } catch (error) {
        ElMessage.error('加载客户端列表失败')
      }
    }

    const showAddDialog = () => {
      dialogTitle.value = '添加客户端'
      clientForm.value = { name: '', host: '' }
      editingId.value = null
      dialogVisible.value = true
    }

    const showEditDialog = (client) => {
      dialogTitle.value = '编辑客户端'
      clientForm.value = { name: client.name, host: client.host }
      editingId.value = client.id
      dialogVisible.value = true
    }

    const submitForm = async () => {
      try {
        await formRef.value.validate()
        if (editingId.value) {
          await updateClient(editingId.value, clientForm.value)
          ElMessage.success('更新成功')
        } else {
          await addClient(clientForm.value)
          ElMessage.success('添加成功')
        }
        dialogVisible.value = false
        loadClients()
      } catch (error) {
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

    const sendCommand = (clientId) => {
      currentClientId.value = clientId
      cmdForm.value = { command: '', taskId: null }
      cmdDialogVisible.value = true
    }

    const submitCommand = async () => {
      try {
        await cmdFormRef.value.validate()
        await sendClientCmd(currentClientId.value, cmdForm.value.command, cmdForm.value.taskId)
        ElMessage.success('命令发送成功')
        cmdDialogVisible.value = false
      } catch (error) {
        ElMessage.error('发送失败')
      }
    }

    const formatTime = (timeStr) => {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString()
    }

    onMounted(() => {
      loadClients()
    })

    return {
      clients,
      dialogVisible,
      dialogTitle,
      clientForm,
      rules,
      formRef,
      cmdDialogVisible,
      cmdForm,
      cmdRules,
      cmdFormRef,
      showAddDialog,
      showEditDialog,
      submitForm,
      deleteClient: deleteClientHandler,
      sendCommand,
      submitCommand,
      formatTime
    }
  }
}
</script>

<style scoped>
.client-manage {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>