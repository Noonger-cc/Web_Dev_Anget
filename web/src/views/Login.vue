<template>
  <div class="login-container">
    <div class="bg-particles">
      <div class="particle" v-for="i in 50" :key="i" :style="getParticleStyle(i)"></div>
    </div>
    <div class="bg-grid"></div>
    <div class="bg-glow"></div>
    
    <el-card class="login-card">
      <div class="login-header">
        <div class="logo-icon">🚀</div>
        <h2>LangGraph 智能运维 Agent</h2>
        <p>Intelligent Operations & Maintenance</p>
      </div>
      
      <el-form
        :model="loginForm"
        :rules="rules"
        ref="formRef"
        class="login-form"
      >
        <el-form-item prop="username">
          <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <el-input 
              v-model="loginForm.username" 
              placeholder="请输入用户名"
              class="custom-input"
            />
          </div>
        </el-form-item>
        <el-form-item prop="password">
          <div class="input-wrapper">
            <span class="input-icon">🔐</span>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              @keyup.enter="handleLogin"
              class="custom-input"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            @click="handleLogin"
            :loading="loading"
          >
            <span class="btn-text">登录</span>
            <span class="btn-glow"></span>
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>默认账号: admin / admin123</p>
      </div>
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

const getParticleStyle = (i) => {
  const size = Math.random() * 4 + 2;
  const left = Math.random() * 100;
  const duration = Math.random() * 20 + 10;
  const delay = Math.random() * 10;
  const color = i % 3 === 0 ? '0, 243, 255' : (i % 3 === 1 ? '138, 43, 226' : '0, 255, 136');
  
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animation: `float-particle ${duration}s linear infinite ${delay}s`,
    background: `rgba(${color}, 0.8)`,
    boxShadow: `0 0 ${size * 2}px rgba(${color}, 0.5)`
  };
};

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    const res = await login(loginForm);
    localStorage.setItem("token", res.token);
    localStorage.setItem("username", loginForm.username);
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
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1729 100%);
}

.bg-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.particle {
  position: absolute;
  top: 100%;
  border-radius: 50%;
  opacity: 0.8;
}

@keyframes float-particle {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 0.8;
  }
  90% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-100vh) rotate(720deg);
    opacity: 0;
  }
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 243, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 243, 255, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
  z-index: 0;
}

.bg-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(0, 243, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(138, 43, 226, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 50% 80%, rgba(0, 255, 136, 0.06) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
  animation: glowPulse 6s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.login-card {
  width: 420px;
  position: relative;
  z-index: 1;
  background: rgba(10, 14, 39, 0.85);
  border-radius: 24px;
  border: 1px solid rgba(0, 243, 255, 0.2);
  backdrop-filter: blur(20px);
  box-shadow: 
    0 0 40px rgba(0, 243, 255, 0.15),
    0 20px 60px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  padding: 20px;
}

.login-card :deep(.el-card__header) {
  border-bottom: none;
  padding: 0;
}

.login-header {
  text-align: center;
  padding: 20px 0 30px 0;
}

.logo-icon {
  font-size: 64px;
  margin-bottom: 15px;
  animation: logoFloat 3s ease-in-out infinite;
  display: inline-block;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-10px) scale(1.05); }
}

.login-header h2 {
  margin: 0 0 10px 0;
  color: #00f3ff;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
}

.login-header p {
  margin: 0;
  color: #6b809a;
  font-size: 13px;
  letter-spacing: 3px;
  text-transform: uppercase;
}

.login-form {
  padding: 0 10px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 15px;
  font-size: 18px;
  z-index: 1;
}

.custom-input {
  flex: 1;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(26, 31, 58, 0.8);
  border: 1px solid rgba(0, 243, 255, 0.2);
  border-radius: 12px;
  padding: 8px 15px 8px 45px;
  box-shadow: none;
  transition: all 0.3s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 243, 255, 0.4);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #00f3ff;
  box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
}

.login-form :deep(.el-input__inner) {
  color: #e0e6ed;
  font-size: 15px;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #6b809a;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #00f3ff 0%, #8a2be2 50%, #00ff88 100%);
  background-size: 200% 200%;
  animation: btnGradient 4s ease infinite;
  border: none;
  color: #0a0e27;
  box-shadow: 
    0 4px 20px rgba(0, 243, 255, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

@keyframes btnGradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 30px rgba(0, 243, 255, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

.btn-text {
  position: relative;
  z-index: 1;
}

.btn-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: btnGlow 3s ease-in-out infinite;
}

@keyframes btnGlow {
  0% { left: -100%; }
  100% { left: 100%; }
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 243, 255, 0.1);
}

.login-footer p {
  margin: 0;
  color: #6b809a;
  font-size: 12px;
  letter-spacing: 1px;
}
</style>