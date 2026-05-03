<template>
  <div class="host-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>主机管理</span>
          <el-button type="primary" @click="openAddDialog">添加主机</el-button>
        </div>
      </template>
      <el-table :data="hosts" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="主机名" />
        <el-table-column prop="host" label="IP地址" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="auth_type" label="认证方式" width="100">
          <template #default="{ row }">
            {{ row.auth_type === "password" ? "密码" : "密钥" }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'info'">
              {{ row.status === "online" ? "在线" : "离线" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEditDialog(row)"
              >编辑</el-button
            >
            <el-button size="small" type="danger" @click="handleDelete(row.id)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑主机' : '添加主机'"
      width="500px"
    >
      <el-form
        :model="hostForm"
        :rules="rules"
        ref="formRef"
        label-width="100px"
      >
        <el-form-item label="主机名" prop="name">
          <el-input v-model="hostForm.name" placeholder="请输入主机名" />
        </el-form-item>
        <el-form-item label="IP地址" prop="host">
          <el-input v-model="hostForm.host" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="hostForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="hostForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="认证方式" prop="auth_type">
          <el-radio-group v-model="hostForm.auth_type">
            <el-radio label="password">密码</el-radio>
            <el-radio label="key">密钥</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="密码/密钥" prop="credential">
          <el-input
            v-model="hostForm.credential"
            type="password"
            placeholder="请输入密码或密钥"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { getHosts, addHost, updateHost, deleteHost } from "../api";

const hosts = ref([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref();

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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
