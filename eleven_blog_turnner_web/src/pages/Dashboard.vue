<template>
  <div class="dashboard">
    <t-card title="欢迎使用 Blog Tuner By ELEVEN" bordered>
      <template #avatar >
        <t-icon name="face-retouching" size="64px"/>
      </template>
      <p>AI 博客生成助手，帮助您根据个人笔记学习写作风格，生成具有个人文笔特色的博客文章。</p>
    </t-card>

    <t-row :gutter="16" class="stats-row">
      <t-col :span="3">
        <t-card class="stat-card">
          <div class="stat-icon">
            <t-icon name="pen-brush" size="32px" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.articles }}</div>
            <div class="stat-label">文章总数</div>
          </div>
        </t-card>
      </t-col>
      <t-col :span="3">
        <t-card class="stat-card">
          <div class="stat-icon">
            <t-icon name="palette" size="32px" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.styles }}</div>
            <div class="stat-label">风格数量</div>
          </div>
        </t-card>
      </t-col>
      <t-col :span="3">
        <t-card class="stat-card">
          <div class="stat-icon">
            <t-icon name="pen" size="32px" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.notes }}</div>
            <div class="stat-label">笔记数量</div>
          </div>
        </t-card>
      </t-col>
      <t-col :span="3">
        <t-card class="stat-card">
          <div class="stat-icon">
            <t-icon name="check-circle" size="32px" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.tasks }}</div>
            <div class="stat-label">完成任务</div>
          </div>
        </t-card>
      </t-col>
    </t-row>

    <t-row :gutter="16" class="content-row">
      <t-col :span="2">
        <t-card title="快捷操作" bordered class="action-card">
          <div class="action-buttons">
            <t-button theme="primary" block @click="$router.push('/generate')">
              <template #icon>
                <t-icon name="add-circle" />
              </template>
              生成新文章
            </t-button>
            <t-button theme="default" block @click="$router.push('/notes')">
              <template #icon>
                <t-icon name="upload" />
              </template>
              导入笔记
            </t-button>
            <t-button theme="default" block @click="$router.push('/styles')">
              <template #icon>
                <t-icon name="palette" />
              </template>
              管理风格
            </t-button>
          </div>
        </t-card>
      </t-col>
      <t-col :span="10">
        <t-card title="最近任务" bordered class="task-card">
          <div class="task-list-container">
            <t-list v-if="recentTasks.length > 0" :split="false" class="task-list">
              <t-list-item v-for="task in recentTasks" :key="task.task_id">
                <t-list-item-meta
                  :title="task.task_type"
                  :description="`状态: ${task.status}`"
                />
              </t-list-item>
            </t-list>
          </div>
        </t-card>
      </t-col>
    </t-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { taskApi, type Task } from '@/api/task'

const stats = ref({
  articles: 0,
  styles: 0,
  notes: 0,
  tasks: 0
})

const recentTasks = ref<Task[]>([])

onMounted(async () => {
  try {
    const response = await taskApi.getTaskList()
    if (response.data?.tasks) {
      recentTasks.value = response.data.tasks.slice(0, 5)
      stats.value.tasks = response.data.total
    }
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  margin-top: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  color: #0052d9;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.content-row {
  margin-top: 24px;
  display: flex;
  align-items: stretch;
}

.content-row :deep(.t-col) {
  display: flex;
}

/* 快捷操作卡片和最近任务卡片统一样式 */
.action-card,
.task-card {
  flex: 1;
  width: 100%;
}

.action-card :deep(.t-card__body),
.task-card :deep(.t-card__body) {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

/* 快捷操作按钮容器 */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.action-buttons .t-button {
  width: 100%;
}

/* 最近任务列表容器 */
.task-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 任务列表填充剩余空间 */
.task-list {
  flex: 1;
  overflow-y: auto;
}

/* 空状态居中显示 */
.task-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
