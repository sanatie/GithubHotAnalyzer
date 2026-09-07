<template>
  <div class="repo-card" @click="$emit('click', repo)">
    <div class="card-header">
      <img v-if="repo.avatar_url" :src="repo.avatar_url" class="avatar" />
      <div class="repo-info">
        <h3 class="repo-name">{{ repo.name }}</h3>
        <p class="repo-owner" v-if="repo.owner">{{ repo.owner }}</p>
      </div>
      <el-button
        :type="isFavorited ? 'danger' : 'default'"
        :icon="isFavorited ? 'Star' : 'StarFilled'"
        circle
        @click.stop="$emit('favorite', repo)"
      />
    </div>

    <p class="description">{{ repo.description || '暂无描述' }}</p>

    <div class="meta">
      <TechStackTags v-if="repo.language" :tags="[{ name: repo.language }]" />
      <div class="stats">
        <span class="stat">
          <el-icon><Star /></el-icon>
          {{ formatNumber(repo.stars) }}
        </span>
        <span class="stat">
          <el-icon><ForkRight /></el-icon>
          {{ formatNumber(repo.forks) }}
        </span>
        <span class="stat" v-if="repo.license">
          <el-icon><Document /></el-icon>
          {{ repo.license }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Star, ForkRight, Document } from '@element-plus/icons-vue';
import TechStackTags from './TechStackTags.vue';

const props = defineProps({
  repo: {
    type: Object,
    required: true
  },
  isFavorited: {
    type: Boolean,
    default: false
  }
});

defineEmits(['click', 'favorite']);

function formatNumber(num) {
  if (!num) return '0';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num;
}
</script>

<style scoped>
.repo-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.repo-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}

.repo-info {
  flex: 1;
  min-width: 0;
}

.repo-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.repo-owner {
  font-size: 13px;
  color: #909399;
  margin: 4px 0 0 0;
}

.description {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}
</style>
