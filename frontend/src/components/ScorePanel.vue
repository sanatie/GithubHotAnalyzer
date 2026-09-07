<template>
  <div class="score-panel">
    <div class="panel-header">
      <h4>综合评分</h4>
      <span class="overall-score">{{ scores.overall || 0 }}</span>
    </div>

    <div class="score-bars">
      <div class="score-item" v-for="(value, key) in breakdown" :key="key">
        <div class="score-label">
          <span>{{ getLabel(key) }}</span>
          <span class="score-value">{{ value }}</span>
        </div>
        <el-progress
          :percentage="value"
          :stroke-width="8"
          :show-text="false"
          :color="getProgressColor(value)"
        />
      </div>
    </div>

    <div class="score-tips" v-if="suitableFor">
      <h5>适合人群</h5>
      <p>{{ suitableFor }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  scores: {
    type: Object,
    default: () => ({ overall: 0 })
  },
  breakdown: {
    type: Object,
    default: () => ({})
  },
  suitableFor: {
    type: String,
    default: ''
  }
});

const labelMap = {
  code_quality: '代码质量',
  community: '社区活跃度',
  documentation: '文档完善度',
  learning_curve: '学习曲线',
  popularity: '流行程度',
  maintenance: '维护状态'
};

function getLabel(key) {
  return labelMap[key] || key;
}

function getProgressColor(value) {
  if (value >= 80) return '#67c23a';
  if (value >= 60) return '#e6a23c';
  if (value >= 40) return '#f56c6c';
  return '#909399';
}
</script>

<style scoped>
.score-panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-header h4 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.overall-score {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
}

.score-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.score-label {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #606266;
}

.score-value {
  font-weight: 600;
}

.score-tips {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.score-tips h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.score-tips p {
  margin: 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}
</style>
