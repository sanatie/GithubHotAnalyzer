<template>
  <div class="report-viewer">
    <el-tabs v-if="report" v-model="activeTab">
      <el-tab-pane label="概览" name="summary">
        <div class="section">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(report.stars) }}</div>
              <div class="stat-label">Star 数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(report.forks) }}</div>
              <div class="stat-label">Fork 数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(report.watchers) }}</div>
              <div class="stat-label">Watch 数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ formatNumber(report.open_issues) }}</div>
              <div class="stat-label">开放 Issue</div>
            </div>
          </div>
        </div>
        <div class="section">
          <div class="info-list">
            <div class="info-item" v-if="report.language">
              <span class="info-label">主要语言</span>
              <span class="info-value">{{ report.language }}</span>
            </div>
            <div class="info-item" v-if="report.license">
              <span class="info-label">开源协议</span>
              <span class="info-value">{{ report.license }}</span>
            </div>
            <div class="info-item" v-if="report.default_branch">
              <span class="info-label">默认分支</span>
              <span class="info-value">{{ report.default_branch }}</span>
            </div>
            <div class="info-item" v-if="report.created_at">
              <span class="info-label">创建时间</span>
              <span class="info-value">{{ formatDate(report.created_at) }}</span>
            </div>
            <div class="info-item" v-if="report.updated_at">
              <span class="info-label">更新时间</span>
              <span class="info-value">{{ formatDate(report.updated_at) }}</span>
            </div>
            <div class="info-item" v-if="report.homepage">
              <span class="info-label">项目主页</span>
              <span class="info-value link">{{ report.homepage }}</span>
            </div>
          </div>
        </div>
        <div class="section">
          <h4>项目简介</h4>
          <p class="summary-text">{{ report.summary || '暂无简介' }}</p>
        </div>
        <div class="section" v-if="report.tech_stack && report.tech_stack.length">
          <h4>技术栈</h4>
          <TechStackTags :tags="report.tech_stack.map(t => ({ name: t }))" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="优点" name="strengths">
        <div class="section">
          <div
            v-for="(item, index) in parseList(report.strengths)"
            :key="index"
            class="list-item positive"
          >
            <el-icon><CircleCheck /></el-icon>
            <span>{{ item }}</span>
          </div>
          <p v-if="!report.strengths" class="empty-text">暂无内容</p>
        </div>
      </el-tab-pane>

      <el-tab-pane label="缺点" name="weaknesses">
        <div class="section">
          <div
            v-for="(item, index) in parseList(report.weaknesses)"
            :key="index"
            class="list-item negative"
          >
            <el-icon><CircleClose /></el-icon>
            <span>{{ item }}</span>
          </div>
          <p v-if="!report.weaknesses" class="empty-text">暂无内容</p>
        </div>
      </el-tab-pane>

      <el-tab-pane label="建议" name="suggestions">
        <div class="section">
          <div
            v-for="(item, index) in parseList(report.suggestions)"
            :key="index"
            class="list-item"
          >
            <el-icon><InfoFilled /></el-icon>
            <span>{{ item }}</span>
          </div>
          <p v-if="!report.suggestions" class="empty-text">暂无内容</p>
        </div>
      </el-tab-pane>

      <el-tab-pane label="安全检测" name="security">
        <div class="section">
          <!-- 未检测时显示检测按钮 -->
          <div v-if="!security && !securityLoading" class="security-empty">
            <p class="empty-text">尚未进行安全风险检测</p>
            <el-button type="primary" @click="runSecurityCheck" :disabled="!reportId">
              开始安全检测
            </el-button>
          </div>

          <!-- 检测中 -->
          <div v-if="securityLoading" class="security-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在检测安全风险，请稍候...</span>
          </div>

          <!-- 检测结果 -->
          <div v-if="security && !securityLoading" class="security-result">
            <div class="security-header">
              <div class="risk-badge" :class="riskClass">{{ security.risk_level }}</div>
              <span class="risk-score">风险评分: {{ security.risk_score }}/100</span>
              <el-button size="small" @click="runSecurityCheck" :loading="securityLoading">
                重新检测
              </el-button>
            </div>

            <p class="security-summary">{{ security.summary }}</p>

            <!-- 漏洞列表 -->
            <div v-if="security.vulnerabilities && security.vulnerabilities.length" class="vuln-section">
              <h4>发现的风险项 ({{ security.vulnerabilities.length }})</h4>
              <div class="vuln-table">
                <div class="vuln-row vuln-header">
                  <span class="col-type">类型</span>
                  <span class="col-severity">严重程度</span>
                  <span class="col-file">文件</span>
                  <span class="col-desc">描述</span>
                  <span class="col-fix">建议</span>
                </div>
                <div
                  v-for="(vuln, index) in security.vulnerabilities"
                  :key="index"
                  class="vuln-row"
                >
                  <span class="col-type">{{ vuln.type }}</span>
                  <span class="col-severity">
                    <span class="severity-tag" :class="severityClass(vuln.severity)">{{ vuln.severity }}</span>
                  </span>
                  <span class="col-file">{{ vuln.file || '-' }}</span>
                  <span class="col-desc">{{ vuln.description }}</span>
                  <span class="col-fix">{{ vuln.recommendation || '-' }}</span>
                </div>
              </div>
            </div>

            <!-- 依赖风险 -->
            <div v-if="security.dependency_risks && security.dependency_risks.length" class="dep-section">
              <h4>依赖风险</h4>
              <div
                v-for="(risk, index) in security.dependency_risks"
                :key="index"
                class="list-item warning"
              >
                <el-icon><Warning /></el-icon>
                <span>{{ risk }}</span>
              </div>
            </div>

            <!-- 无风险 -->
            <div v-if="!security.vulnerabilities?.length && !security.dependency_risks?.length" class="safe-state">
              <el-icon><CircleCheck /></el-icon>
              <span>未发现明显安全风险</span>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div v-else class="empty-state">
      <el-empty description="暂无报告数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { CircleCheck, CircleClose, InfoFilled, Loading, Warning } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import api from '../api';
import TechStackTags from './TechStackTags.vue';

const props = defineProps({
  report: {
    type: Object,
    default: null
  },
  reportId: {
    type: Number,
    default: null
  },
  security: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['security-done']);

const activeTab = ref('summary');
const securityLoading = ref(false);

const riskClass = computed(() => {
  if (!props.security) return '';
  const level = props.security.risk_level || '';
  if (level.includes('严重')) return 'risk-critical';
  if (level.includes('高')) return 'risk-high';
  if (level.includes('中')) return 'risk-medium';
  return 'risk-low';
});

function severityClass(severity) {
  if (!severity) return '';
  if (severity.includes('严重')) return 'severity-critical';
  if (severity.includes('高')) return 'severity-high';
  if (severity.includes('中')) return 'severity-medium';
  return 'severity-low';
}

async function runSecurityCheck() {
  if (!props.reportId) {
    ElMessage.warning('缺少报告 ID，无法检测');
    return;
  }
  securityLoading.value = true;
  try {
    const res = await api.securityCheck(props.reportId);
    ElMessage.success('安全检测完成');
    emit('security-done');
  } catch (error) {
    const msg = error?.response?.data?.detail || '安全检测失败';
    ElMessage.error(msg);
  } finally {
    securityLoading.value = false;
  }
}

function parseList(text) {
  if (!text) return [];
  if (Array.isArray(text)) return text;
  return text.split('\n').filter(item => item.trim());
}

function formatNumber(num) {
  if (!num && num !== 0) return '-';
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num;
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  return date.toLocaleDateString('zh-CN');
}
</script>

<style scoped>
.report-viewer {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.report-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.report-header h2 {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: #303133;
}

.repo-meta {
  display: flex;
  gap: 16px;
  color: #909399;
  font-size: 14px;
}

.section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #303133;
}

.summary-text {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.info-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 24px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-label {
  font-size: 13px;
  color: #909399;
}

.info-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.info-value.link {
  color: #409eff;
  cursor: pointer;
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .info-list {
    grid-template-columns: 1fr;
  }
}

.list-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.list-item.positive {
  color: #67c23a;
}

.list-item.negative {
  color: #f56c6c;
}

.list-item.warning {
  color: #e6a23c;
}

.empty-text,
.empty-state {
  color: #909399;
  font-size: 14px;
}

/* 安全检测样式 */
.security-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 0;
}

.security-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

.security-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.security-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
}

.risk-badge.risk-low {
  background: #f0f9eb;
  color: #67c23a;
}

.risk-badge.risk-medium {
  background: #fdf6ec;
  color: #e6a23c;
}

.risk-badge.risk-high {
  background: #fef0f0;
  color: #f56c6c;
}

.risk-badge.risk-critical {
  background: #2a0000;
  color: #ff4d4f;
}

.risk-score {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.security-summary {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin: 0;
}

.vuln-section h4,
.dep-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #303133;
}

.vuln-table {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.vuln-row {
  display: flex;
  border-bottom: 1px solid #f0f0f0;
  min-height: 44px;
}

.vuln-row:last-child {
  border-bottom: none;
}

.vuln-header {
  background: #f5f7fa;
  font-weight: 600;
  font-size: 13px;
  color: #606266;
}

.vuln-row > span {
  padding: 8px 10px;
  display: flex;
  align-items: flex-start;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.col-type { flex: 0 0 100px; }
.col-severity { flex: 0 0 80px; }
.col-file { flex: 0 0 140px; word-break: break-all; }
.col-desc { flex: 1; }
.col-fix { flex: 0 0 180px; }

.severity-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.severity-tag.severity-critical {
  background: #2a0000;
  color: #ff4d4f;
}

.severity-tag.severity-high {
  background: #fef0f0;
  color: #f56c6c;
}

.severity-tag.severity-medium {
  background: #fdf6ec;
  color: #e6a23c;
}

.severity-tag.severity-low {
  background: #f0f9eb;
  color: #67c23a;
}

.safe-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 24px;
  justify-content: center;
  color: #67c23a;
  font-size: 15px;
}
</style>
