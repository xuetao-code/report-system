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
  height: 100vh;
}

.el-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
</style>
