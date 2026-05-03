<template>
  <div class="main-layout">
    <el-container>
      <el-aside width="200px">
        <div class="logo">
          <h3>智能运维</h3>
        </div>
        <el-menu :default-active="activeMenu" router class="sidebar-menu">
          <el-menu-item index="/main/hosts">
            <span>主机管理</span>
          </el-menu-item>
          <el-menu-item index="/main/task/create">
            <span>创建任务</span>
          </el-menu-item>
          <el-menu-item index="/main/task/list">
            <span>任务列表</span>
          </el-menu-item>
          <el-menu-item index="/main/log">
            <span>实时日志</span>
          </el-menu-item>
        </el-menu>
        <div class="logout-section">
          <el-button type="danger" size="small" @click="handleLogout"
            >退出登录</el-button
          >
        </div>
      </el-aside>
      <el-container>
        <el-header>
          <h2>LangGraph 智能运维 Agent</h2>
          <span class="user-info">当前用户: {{ username }}</span>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();
const username = ref(localStorage.getItem("username") || "admin");

const activeMenu = computed(() => route.path);

const handleLogout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  router.push("/login");
};
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #4a5568;
}

.logo h3 {
  color: #fff;
  margin: 0;
}

.sidebar-menu {
  border-right: none;
  background-color: #304156;
}

.sidebar-menu span {
  color: #bfcbd9;
}

.el-header {
  background-color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.el-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.user-info {
  color: #666;
  font-size: 14px;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
}

.logout-section {
  padding: 20px;
  text-align: center;
  position: absolute;
  bottom: 0;
  width: 100%;
}
</style>
