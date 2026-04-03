<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>自定义报表系统</h1>
      </el-header>
      <el-container>
        <el-aside width="200px">
          <el-menu :default-active="activeMenu" router>
            <el-menu-item index="/reports">
              <el-icon><Document /></el-icon>
              <span>报表管理</span>
            </el-menu-item>
            <el-menu-item index="/datasources">
              <el-icon><DataBoard /></el-icon>
              <span>数据源</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Document, DataBoard } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  height: 100vh;
}

.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
}

.el-aside {
  background-color: #f5f7fa;
  border-right: 1px solid #e6e6e6;
}

.el-main {
  padding: 20px;
  background-color: #fff;
}
</style>
