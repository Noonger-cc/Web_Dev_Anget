<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>LangGraph 智能运维 Agent</h2>
      </template>
      <el-form
        :model="loginForm"
        :rules="rules"
        ref="formRef"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            style="width: 100%"
            @click="handleLogin"
            :loading="loading"
            >登录</el-button
          >
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { login } from "../api";

const router = useRouter();
const formRef = ref();
const loading = ref(false);

const loginForm = reactive({
  username: "admin",
  password: "admin123",
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    const res = await login(loginForm);
    localStorage.setItem("token", res.token);
    ElMessage.success("登录成功");
    router.push("/main");
  } catch (err) {
    ElMessage.error(err.message || "登录失败");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
}

.login-card h2 {
  text-align: center;
  color: #333;
  margin: 0;
}
</style>
