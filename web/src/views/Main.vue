<template>
  <div class="main-layout">
    <div class="bg-animation"></div>
    <div class="bg-grid"></div>
    <el-container>
      <el-aside width="240px">
        <div class="logo">
          <div class="logo-icon">🚀</div>
          <h3>智能运维</h3>
          <p>LangGraph Agent</p>
        </div>
        <el-menu 
          :default-active="activeMenu" 
          router 
          class="sidebar-menu"
          active-text-color="#00f3ff"
          background-color="transparent"
          text-color="#8b9eb7"
        >
          <el-menu-item index="/main/hosts">
            <span class="menu-icon">💻</span>
            <span>主机管理</span>
          </el-menu-item>
          <el-menu-item index="/main/clients">
            <span class="menu-icon">🔗</span>
            <span>客户端管理</span>
          </el-menu-item>
          <el-menu-item index="/main/task/create">
            <span class="menu-icon">⚡</span>
            <span>创建任务</span>
          </el-menu-item>
          <el-menu-item index="/main/tasks">
            <span class="menu-icon">📋</span>
            <span>任务列表</span>
          </el-menu-item>
          <el-menu-item index="/main/task-log">
            <span class="menu-icon">📊</span>
            <span>实时日志</span>
          </el-menu-item>
        </el-menu>
        <div class="logout-section">
          <div class="user-card">
            <div class="avatar">👤</div>
            <div class="user-name">{{ username }}</div>
            <div class="user-status">在线</div>
          </div>
          <el-button type="danger" size="small" class="logout-btn" @click="handleLogout">
            <span>退出登录</span>
          </el-button>
        </div>
      </el-aside>
      <el-container>
        <el-header>
          <div class="header-left">
            <div class="status-dot"></div>
            <h2>LangGraph 智能运维 Agent</h2>
          </div>
          <div class="header-right">
            <div class="time-display">{{ currentTime }}</div>
            <div class="connection-status">
              <span class="status-dot green"></span>
              <span>系统正常</span>
            </div>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();
const username = ref(localStorage.getItem("username") || "admin");
const currentTime = ref("");
let timer = null;

const activeMenu = computed(() => route.path);

const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString("zh-CN", { 
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
};

const handleLogout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  router.push("/login");
};

onMounted(() => {
  updateTime();
  timer = setInterval(updateTime, 1000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1729 100%);
}

.bg-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(0, 243, 255, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(138, 43, 226, 0.06) 0%, transparent 50%),
    radial-gradient(circle at 40% 20%, rgba(0, 255, 136, 0.05) 0%, transparent 40%);
  pointer-events: none;
  z-index: 0;
  animation: bgPulse 8s ease-in-out infinite;
}

@keyframes bgPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
  z-index: 0;
}

.el-aside {
  background: linear-gradient(180deg, 
    rgba(10, 14, 39, 0.95) 0%, 
    rgba(26, 31, 58, 0.98) 100%);
  color: #fff;
  position: relative;
  z-index: 1;
  border-right: 1px solid rgba(0, 243, 255, 0.1);
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
}

.logo {
  padding: 30px 20px;
  text-align: center;
  border-bottom: 1px solid rgba(0, 243, 255, 0.15);
  background: linear-gradient(180deg, rgba(0, 243, 255, 0.08) 0%, transparent 100%);
}

.logo-icon {
  font-size: 48px;
  margin-bottom: 10px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.logo h3 {
  color: #00f3ff;
  margin: 0 0 5px 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
}

.logo p {
  margin: 0;
  color: #6b809a;
  font-size: 12px;
  letter-spacing: 3px;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
  padding: 10px 0;
}

.sidebar-menu .el-menu-item {
  margin: 5px 12px;
  border-radius: 10px;
  transition: all 0.3s ease;
  position: relative;
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(0, 243, 255, 0.1) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(90deg, 
    rgba(0, 243, 255, 0.2) 0%, 
    rgba(0, 243, 255, 0.05) 100%);
  border-left: 3px solid #00f3ff;
  box-shadow: 0 0 20px rgba(0, 243, 255, 0.15);
}

.sidebar-menu .el-menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 10px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.sidebar-menu .el-menu-item:hover::before {
  border-color: rgba(0, 243, 255, 0.3);
}

.menu-icon {
  margin-right: 12px;
  font-size: 18px;
}

.el-header {
  background: linear-gradient(90deg, 
    rgba(10, 14, 39, 0.95) 0%, 
    rgba(26, 31, 58, 0.98) 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  border-bottom: 1px solid rgba(0, 243, 255, 0.15);
  position: relative;
  z-index: 1;
}

.el-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(0, 243, 255, 0.5) 20%,
    rgba(0, 243, 255, 0.8) 50%,
    rgba(0, 243, 255, 0.5) 80%,
    transparent 100%);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #00f3ff;
  box-shadow: 0 0 10px #00f3ff, 0 0 20px rgba(0, 243, 255, 0.5);
  animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
  0%, 100% { box-shadow: 0 0 10px #00f3ff, 0 0 20px rgba(0, 243, 255, 0.5); }
  50% { box-shadow: 0 0 20px #00f3ff, 0 0 40px rgba(0, 243, 255, 0.7); }
}

.el-header h2 {
  margin: 0;
  font-size: 20px;
  color: #00f3ff;
  font-weight: 600;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 30px;
}

.time-display {
  color: #00f3ff;
  font-family: 'Courier New', monospace;
  font-size: 18px;
  text-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
  letter-spacing: 2px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8b9eb7;
}

.status-dot.green {
  width: 8px;
  height: 8px;
  background: #00ff88;
  box-shadow: 0 0 8px #00ff88;
  animation: none;
}

.el-main {
  padding: 25px;
  background: transparent;
  position: relative;
  z-index: 1;
}

.logout-section {
  padding: 20px;
  position: absolute;
  bottom: 0;
  width: 100%;
  border-top: 1px solid rgba(0, 243, 255, 0.1);
}

.user-card {
  text-align: center;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(0, 243, 255, 0.1) 0%, rgba(138, 43, 226, 0.05) 100%);
  border: 1px solid rgba(0, 243, 255, 0.2);
}

.avatar {
  font-size: 32px;
  margin-bottom: 8px;
}

.user-name {
  color: #fff;
  font-size: 14px;
  margin-bottom: 3px;
}

.user-status {
  color: #00ff88;
  font-size: 12px;
}

.logout-btn {
  width: 100%;
  background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(255, 71, 87, 0.4);
  transition: all 0.3s ease;
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 71, 87, 0.6);
}
</style>