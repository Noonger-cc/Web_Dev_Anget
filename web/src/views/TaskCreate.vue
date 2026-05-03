<template>
  <div class="task-create">
    <el-card>
      <template #header>
        <span>创建运维任务</span>
      </template>
      <el-form
        :model="taskForm"
        :rules="rules"
        ref="formRef"
        label-width="120px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="执行方式" prop="exec_type">
          <el-radio-group v-model="taskForm.exec_type">
            <el-radio label="ssh">SSH直连</el-radio>
            <el-radio label="client">客户端</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          label="选择主机"
          prop="host_ids"
          v-if="taskForm.exec_type === 'ssh'"
        >
          <el-select
            v-model="taskForm.host_ids"
            multiple
            placeholder="请选择主机"
            style="width: 100%"
          >
            <el-option
              v-for="host in hosts"
              :key="host.id"
              :label="host.name"
              :value="host.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          label="选择客户端"
          prop="client_ids"
          v-if="taskForm.exec_type === 'client'"
        >
          <el-select
            v-model="taskForm.client_ids"
            multiple
            placeholder="请选择客户端"
            style="width: 100%"
          >
            <el-option
              v-for="client in clients"
              :key="client.id"
              :label="client.name"
              :value="client.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行命令" prop="command">
          <el-input
            v-model="taskForm.command"
            type="textarea"
            :rows="4"
            placeholder="请输入要执行的命令"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleCreate" :loading="loading"
            >创建任务</el-button
          >
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getHosts, getClients, createTask } from "../api";

const router = useRouter();
const formRef = ref();
const loading = ref(false);
const hosts = ref([]);
const clients = ref([]);

const taskForm = reactive({
  name: "",
  exec_type: "ssh",
  host_ids: [],
  client_ids: [],
  command: "",
});

const rules = {
  name: [{ required: true, message: "请输入任务名称", trigger: "blur" }],
  exec_type: [{ required: true, message: "请选择执行方式", trigger: "change" }],
  host_ids: [
    {
      type: "array",
      required: true,
      message: "请选择至少一台主机",
      trigger: "change",
      validator: (rule, value, callback) => {
        if (taskForm.exec_type === "ssh" && (!value || value.length === 0)) {
          callback(new Error("请选择至少一台主机"));
        } else {
          callback();
        }
      },
    },
  ],
  client_ids: [
    {
      type: "array",
      required: true,
      message: "请选择至少一个客户端",
      trigger: "change",
      validator: (rule, value, callback) => {
        if (taskForm.exec_type === "client" && (!value || value.length === 0)) {
          callback(new Error("请选择至少一个客户端"));
        } else {
          callback();
        }
      },
    },
  ],
  command: [{ required: true, message: "请输入执行命令", trigger: "change" }],
};

const loadData = async () => {
  try {
    const [hostRes, clientRes] = await Promise.all([getHosts(), getClients()]);
    hosts.value = hostRes.data || [];
    clients.value = clientRes.data || [];
  } catch (err) {
    ElMessage.error("获取数据失败");
  }
};

const handleCreate = async () => {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    const data = {
      name: taskForm.name,
      exec_type: taskForm.exec_type,
      command: taskForm.command,
    };
    if (taskForm.exec_type === "ssh") {
      data.host_ids = taskForm.host_ids;
    } else {
      data.client_ids = taskForm.client_ids;
    }
    await createTask(data);
    ElMessage.success("任务创建成功");
    router.push("/main/tasks");
  } catch (err) {
    ElMessage.error(err.message || "创建失败");
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  formRef.value.resetFields();
  taskForm.host_ids = [];
  taskForm.client_ids = [];
};

onMounted(() => {
  loadData();
});

// 切换执行方式时清空已选
watch(
  () => taskForm.exec_type,
  (newType) => {
    if (newType === "ssh") {
      taskForm.client_ids = [];
    } else {
      taskForm.host_ids = [];
    }
  },
);
</script>
