<template>
  <div class="home">
    <div v-if="!report && !analyzing" class="empty-state">
      <div class="empty-inner">
        <h1 class="empty-title">仓库分析器</h1>
        <p class="empty-subtitle">输入 GitHub 仓库地址，生成 AI 智能分析报告</p>
        <div class="search-box">
          <input
            v-model="repoUrl"
            class="search-input"
            placeholder="https://github.com/owner/repo"
            @keyup.enter="handleAnalyze"
          />
          <button class="analyze-btn" @click="handleAnalyze" :disabled="analyzing">
            {{ analyzing ? '分析中...' : '开始分析' }}
          </button>
        </div>
        <div class="examples">
          <span class="examples-label">试试：</span>
          <button v-for="ex in examples" :key="ex" class="example-btn" @click="tryExample(ex)">
            {{ ex }}
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="analyzing" class="loading-state">
      <div class="loading-inner">
        <div class="spinner" />
        <p class="loading-text">正在分析仓库...</p>
        <p class="loading-subtext">可能需要几秒钟</p>
      </div>
    </div>

    <div v-else class="result-page">
      <div class="result-header">
        <div class="header-left">
          <div class="repo-name">{{ report.repo_full_name }}</div>
          <div class="repo-stats">
            <span class="stat-item">
              <span class="stat-label">评分</span>
              <span class="stat-value score">{{ report.overall_score }}</span>
            </span>
            <span class="stat-divider" />
            <span v-if="formattedReport.language" class="stat-item">
              <span class="stat-label">语言</span>
              <span class="stat-value">{{ formattedReport.language }}</span>
            </span>
            <span v-if="formattedReport.stars" class="stat-item">
              <span class="stat-label">Stars</span>
              <span class="stat-value">{{ formatNumber(formattedReport.stars) }}</span>
            </span>
          </div>
        </div>
        <div class="header-right">
          <button class="btn-secondary" @click="handleRefresh" :disabled="refreshing">
            {{ refreshing ? '刷新中...' : '重新分析' }}
          </button>
          <button :class="['btn-primary', { 'is-active': isFavorited }]" @click="handleFavorite">
            {{ isFavorited ? '已收藏' : '收藏' }}
          </button>
        </div>
      </div>

      <div class="result-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-btn', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="result-content">
        <div v-if="activeTab === 'overview'" class="tab-panel">
          <div class="section">
            <h3 class="section-title">项目摘要</h3>
            <p class="summary-text">{{ formattedReport.summary }}</p>
          </div>

          <div class="section">
            <h3 class="section-title">关键指标</h3>
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-value">{{ formatNumber(formattedReport.stars) }}</div>
                <div class="metric-label">Stars</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatNumber(formattedReport.forks) }}</div>
                <div class="metric-label">Forks</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatNumber(formattedReport.watchers) }}</div>
                <div class="metric-label">关注者</div>
              </div>
              <div class="metric-card">
                <div class="metric-value">{{ formatNumber(formattedReport.open_issues) }}</div>
                <div class="metric-label">未解决 Issues</div>
              </div>
            </div>
          </div>

          <div class="section">
            <h3 class="section-title">技术栈</h3>
            <div class="tech-list">
              <span v-for="tech in formattedReport.tech_stack" :key="tech" class="tech-tag">
                {{ tech }}
              </span>
            </div>
          </div>

          <div class="section">
            <h3 class="section-title">评分明细</h3>
            <div class="score-list">
              <div v-for="(value, key) in scoreBreakdown" :key="key" class="score-row">
                <span class="score-label">{{ getLabel(key) }}</span>
                <div class="score-bar-wrap">
                  <div class="score-bar" :style="{ width: value + '%' }" />
                </div>
                <span class="score-num">{{ value }}</span>
              </div>
            </div>
          </div>

          <div v-if="suitableForText" class="section">
            <h3 class="section-title">适用场景</h3>
            <p class="suitable-text">{{ suitableForText }}</p>
          </div>
        </div>

        <div v-if="activeTab === 'strengths'" class="tab-panel">
          <div class="section">
            <h3 class="section-title">项目优势</h3>
            <div class="point-list">
              <div v-for="(item, i) in parseList(formattedReport.strengths)" :key="i" class="point-item positive">
                <span class="point-marker">+</span>
                <span class="point-text">{{ item }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'weaknesses'" class="tab-panel">
          <div class="section">
            <h3 class="section-title">不足之处</h3>
            <div class="point-list">
              <div v-for="(item, i) in parseList(formattedReport.weaknesses)" :key="i" class="point-item negative">
                <span class="point-marker">−</span>
                <span class="point-text">{{ item }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'suggestions'" class="tab-panel">
          <div class="section">
            <h3 class="section-title">改进建议</h3>
            <div class="point-list">
              <div v-for="(item, i) in parseList(formattedReport.suggestions)" :key="i" class="point-item">
                <span class="point-marker">→</span>
                <span class="point-text">{{ item }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'security'" class="tab-panel">
          <div class="section">
            <!-- 未检测时显示检测按钮 -->
            <div v-if="!securityData && !securityLoading" class="security-empty">
              <p class="empty-text">尚未进行安全风险检测</p>
              <button class="btn-primary" @click="runSecurityCheck" :disabled="!report?.id">
                开始安全检测
              </button>
            </div>

            <!-- 检测中 -->
            <div v-if="securityLoading" class="security-loading">
              <div class="spinner" />
              <span>正在检测安全风险，请稍候...</span>
            </div>

            <!-- 检测结果 -->
            <div v-if="securityData && !securityLoading" class="security-result">
              <!-- 重新检测按钮 -->
              <div class="security-header">
                <span class="risk-badge" :class="riskClass">{{ securityData.risk_level }}</span>
                <span class="risk-score">风险评分: {{ securityData.risk_score }}/100</span>
                <button class="btn-secondary" @click="runSecurityCheck" :disabled="securityLoading">
                  重新检测
                </button>
              </div>

              <!-- 表格一：检测概览 -->
              <div class="sub-section">
                <h3 class="section-title">检测概览</h3>
                <el-table :data="overviewData" border :show-header="false" class="security-table">
                  <el-table-column prop="label" width="120" />
                  <el-table-column prop="value" />
                  <el-table-column prop="status" width="80">
                    <template #default="{ row }">
                      <span v-if="row.status" :class="['status-tag', row.status.toLowerCase().replace(' ', '-')]">{{ row.status }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 表格二：检测维度结果 -->
              <div class="sub-section">
                <h3 class="section-title">检测维度结果</h3>
                <el-table :data="securityData.detection_results" border class="security-table">
                  <el-table-column prop="dimension" label="检测维度" width="140" />
                  <el-table-column prop="issues_count" label="发现问题数" width="100" />
                  <el-table-column prop="status" label="状态" width="80">
                    <template #default="{ row }">
                      <span :class="['status-tag', row.status.toLowerCase().replace(' ', '-')]">{{ row.status }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="说明" />
                </el-table>
              </div>

              <!-- 表格三：漏洞详情 -->
              <div v-if="securityData.vulnerabilities && securityData.vulnerabilities.length" class="sub-section">
                <h3 class="section-title">漏洞详情 ({{ securityData.vulnerabilities.length }})</h3>
                <el-table :data="securityData.vulnerabilities" border class="security-table">
                  <el-table-column prop="type" label="类型" width="100" />
                  <el-table-column prop="severity" label="严重程度" width="80">
                    <template #default="{ row }">
                      <span :class="['severity-tag', severityClass(row.severity)]">{{ row.severity }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="file" label="文件" width="150" />
                  <el-table-column prop="description" label="描述" />
                  <el-table-column prop="recommendation" label="建议" />
                </el-table>
              </div>

              <!-- 表格四：依赖风险 -->
              <div v-if="securityData.dependency_risks && securityData.dependency_risks.length" class="sub-section">
                <h3 class="section-title">依赖风险 ({{ securityData.dependency_risks.length }})</h3>
                <el-table :data="securityData.dependency_risks" border class="security-table">
                  <el-table-column prop="package" label="依赖包" width="120" />
                  <el-table-column prop="version" label="当前版本" width="100" />
                  <el-table-column prop="description" label="风险描述" />
                  <el-table-column prop="suggested_version" label="建议版本" width="120" />
                </el-table>
              </div>

              <!-- 总结 -->
              <div class="sub-section">
                <h3 class="section-title">评估总结</h3>
                <p class="security-summary">{{ securityData.summary }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api';

const route = useRoute();

const repoUrl = ref('');
const analyzing = ref(false);
const refreshing = ref(false);
const report = ref(null);
const isFavorited = ref(false);
const activeTab = ref('overview');
const securityLoading = ref(false);

const tabs = [
  { key: 'overview', label: '概览' },
  { key: 'strengths', label: '优势' },
  { key: 'weaknesses', label: '不足' },
  { key: 'suggestions', label: '建议' },
  { key: 'security', label: '安全检测' },
];

const examples = [
  'tiangolo/fastapi',
  'vuejs/core',
  'facebook/react',
];

const labelMap = {
  code_quality: '代码质量',
  community: '社区活跃',
  documentation: '文档完善',
  learning_curve: '学习曲线',
  popularity: '流行程度',
  maintenance: '维护状态',
  activity: '活跃度',
};

const scoreBreakdown = computed(() => {
  if (!report.value) return {};
  if (report.value.score_breakdown) return report.value.score_breakdown;
  if (report.value.content?.score_breakdown) return report.value.content.score_breakdown;
  return {};
});

const suitableForText = computed(() => {
  if (!report.value) return '';
  let suitable = report.value.suitable_for;
  if (!suitable && report.value.content?.suitable_for) {
    suitable = report.value.content.suitable_for;
  }
  if (Array.isArray(suitable)) return suitable.join(', ');
  return suitable || '';
});

const securityData = computed(() => {
  if (!report.value) return null;
  const data = report.value.content?.security || report.value.security || null;
  if (!data) return null;
  
  const defaultDetectionResults = [
    { dimension: '恶意代码检测', issues_count: 0, status: '通过', description: '未检测' },
    { dimension: '网络请求安全', issues_count: 0, status: '通过', description: '未检测' },
    { dimension: '权限操作检测', issues_count: 0, status: '通过', description: '未检测' },
    { dimension: '依赖项风险', issues_count: 0, status: '通过', description: '未检测' },
    { dimension: '安装脚本检测', issues_count: 0, status: '通过', description: '未检测' },
    { dimension: '代码混淆检测', issues_count: 0, status: '通过', description: '未检测' },
  ];
  
  return {
    ...data,
    detection_results: data.detection_results || defaultDetectionResults,
    vulnerabilities: data.vulnerabilities || [],
    dependency_risks: data.dependency_risks || [],
  };
});

const riskClass = computed(() => {
  if (!securityData.value) return '';
  const level = securityData.value.risk_level || '';
  if (level.includes('严重')) return 'risk-critical';
  if (level.includes('高')) return 'risk-high';
  if (level.includes('中')) return 'risk-medium';
  return 'risk-low';
});

const overviewData = computed(() => {
  if (!securityData.value) return [];
  const totalIssues = securityData.value.vulnerabilities?.length || 0;
  const passedCount = securityData.value.detection_results?.filter(r => r.status === '通过').length || 0;
  const warningCount = securityData.value.detection_results?.filter(r => r.status === '警告').length || 0;
  const failedCount = securityData.value.detection_results?.filter(r => r.status === '失败').length || 0;
  
  return [
    { label: '风险等级', value: securityData.value.risk_level, status: riskClass.value ? (riskClass.value.includes('low') ? '通过' : riskClass.value.includes('medium') ? '警告' : '失败') : '' },
    { label: '风险评分', value: securityData.value.risk_score + '/100', status: securityData.value.risk_score <= 20 ? '通过' : securityData.value.risk_score <= 50 ? '警告' : '失败' },
    { label: '发现漏洞数', value: totalIssues + ' 个', status: totalIssues === 0 ? '通过' : totalIssues <= 3 ? '警告' : '失败' },
    { label: '检测维度', value: `通过 ${passedCount} / 警告 ${warningCount} / 失败 ${failedCount}`, status: failedCount === 0 && warningCount === 0 ? '通过' : failedCount > 0 ? '失败' : '警告' },
  ];
});

function severityClass(severity) {
  if (!severity) return '';
  if (severity.includes('严重')) return 'severity-critical';
  if (severity.includes('高')) return 'severity-high';
  if (severity.includes('中')) return 'severity-medium';
  return 'severity-low';
}

async function runSecurityCheck() {
  if (!report.value?.id) {
    ElMessage.warning('缺少报告 ID，无法检测');
    return;
  }
  securityLoading.value = true;
  try {
    await api.securityCheck(report.value.id);
    await fetchReportDetail(report.value.id);
    ElMessage.success('安全检测完成');
  } catch (error) {
    const msg = error?.response?.data?.detail || '安全检测失败';
    ElMessage.error(msg);
  } finally {
    securityLoading.value = false;
  }
}

const formattedReport = computed(() => {
  if (!report.value) return null;
  const content = report.value.content || {};
  const repo = report.value.repository || report.value.repo || {};
  return {
    repository_name: report.value.repo_full_name || report.value.repository_name || 'Unknown',
    stars: report.value.stars || repo.stargazers_count || 0,
    forks: report.value.forks || repo.forks_count || 0,
    watchers: report.value.watchers || repo.watchers_count || 0,
    open_issues: report.value.open_issues || repo.open_issues_count || 0,
    language: report.value.language || repo.language || '',
    license: report.value.license || (repo.license?.spdx_id || repo.license?.name) || '',
    default_branch: report.value.default_branch || repo.default_branch || '',
    created_at: report.value.created_at || repo.created_at || '',
    updated_at: report.value.updated_at || repo.updated_at || '',
    homepage: report.value.homepage || repo.homepage || '',
    summary: content.summary || report.value.summary || 'No summary available',
    tech_stack: content.tech_stack || [],
    strengths: content.highlights || content.strengths || [],
    weaknesses: content.weaknesses || [],
    suggestions: content.suggestions || (content.learning_advice ? [content.learning_advice] : []),
  };
});

function formatNumber(num) {
  if (!num && num !== 0) return '-';
  if (num >= 10000) return (num / 10000).toFixed(1) + 'k';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
}

function parseList(text) {
  if (!text) return [];
  if (Array.isArray(text)) return text;
  return text.split('\n').filter(item => item.trim());
}

function getLabel(key) {
  return labelMap[key] || key;
}

function tryExample(ex) {
  repoUrl.value = `https://github.com/${ex}`;
  handleAnalyze();
}

async function handleAnalyze() {
  if (!repoUrl.value.trim()) {
    ElMessage.warning('请输入仓库地址');
    return;
  }
  analyzing.value = true;
  report.value = null;
  try {
    const res = await api.analyzeRepo({ repo_url: repoUrl.value });
    if (res.data?.report_id) {
      await fetchReportDetail(res.data.report_id);
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '分析失败，请检查仓库地址后重试');
  } finally {
    analyzing.value = false;
  }
}

async function handleRefresh() {
  if (!report.value?.repo_full_name) return;
  refreshing.value = true;
  try {
    const res = await api.analyzeRepo({
      repo_url: `https://github.com/${report.value.repo_full_name}`,
      force_refresh: true,
    });
    if (res.data?.report_id) {
      await fetchReportDetail(res.data.report_id);
    }
    ElMessage.success('重新分析完成');
  } catch (error) {
    ElMessage.error('重新分析失败');
  } finally {
    refreshing.value = false;
  }
}

async function fetchReportDetail(reportId) {
  try {
    const res = await api.getReportDetail(reportId);
    report.value = res.data;
    if (res.data?.repo_id) {
      const favRes = await api.checkFavorite(res.data.repo_id);
      isFavorited.value = favRes.data?.is_favorited || false;
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('加载报告失败');
  }
}

async function handleFavorite() {
  if (!report.value?.repo_id) {
    ElMessage.warning('无法收藏：缺少仓库信息');
    return;
  }
  try {
    if (isFavorited.value) {
      await api.deleteFavorite(report.value.repo_id);
      isFavorited.value = false;
      ElMessage.success('已取消收藏');
    } else {
      await api.addFavorite({
        repo_id: report.value.repo_id,
        repo_full_name: report.value.repo_full_name,
        note: '',
      });
      isFavorited.value = true;
      ElMessage.success('收藏成功');
    }
  } catch (error) {
    ElMessage.error('操作失败');
  }
}

onMounted(() => {
  if (route.query.reportId) {
    fetchReportDetail(route.query.reportId);
  }
  if (route.query.url) {
    repoUrl.value = route.query.url;
  }
});
</script>

<style scoped>
.home {
  min-height: 60vh;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
}

.empty-inner {
  text-align: center;
  max-width: 720px;
  width: 100%;
}

.empty-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin: 0 0 var(--space-3) 0;
  letter-spacing: -0.02em;
}

.empty-subtitle {
  font-size: var(--font-size-md);
  color: var(--fg-secondary);
  margin: 0 0 var(--space-6) 0;
}

.search-box {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
}

.search-input {
  flex: 1;
  height: 40px;
  padding: 0 var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  font-size: var(--font-size-base);
  font-family: var(--geist-mono);
  color: var(--fg-primary);
  background: var(--bg-background);
  outline: none;
  transition: border-color var(--transition-fast);
}

.search-input:focus {
  border-color: var(--fg-primary);
}

.search-input::placeholder {
  color: var(--fg-tertiary);
}

.analyze-btn {
  height: 40px;
  padding: 0 var(--space-5);
  border: none;
  border-radius: var(--radius);
  background: var(--fg-primary);
  color: var(--bg-background);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: opacity var(--transition-fast);
  white-space: nowrap;
}

.analyze-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.examples {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.examples-label {
  font-size: var(--font-size-sm);
  color: var(--fg-tertiary);
}

.example-btn {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-3);
  font-family: var(--geist-mono);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.example-btn:hover {
  border-color: var(--fg-secondary);
  color: var(--fg-primary);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.loading-inner {
  text-align: center;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 2px solid var(--border-default);
  border-top-color: var(--fg-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--space-4);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: var(--font-size-md);
  color: var(--fg-primary);
  margin: 0 0 var(--space-1) 0;
  font-weight: var(--font-weight-medium);
}

.loading-subtext {
  font-size: var(--font-size-sm);
  color: var(--fg-tertiary);
  margin: 0;
}

.result-page {
  max-width: 960px;
  margin: 0 auto;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--border-default);
  gap: var(--space-4);
  flex-wrap: wrap;
}

.header-left {
  flex: 1;
  min-width: 0;
}

.repo-name {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin-bottom: var(--space-3);
  font-family: var(--geist-mono);
  letter-spacing: -0.01em;
}

.repo-stats {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: var(--font-weight-medium);
}

.stat-value {
  font-size: var(--font-size-md);
  color: var(--fg-primary);
  font-weight: var(--font-weight-semibold);
}

.stat-value.score {
  color: var(--accent-blue);
  font-family: var(--geist-mono);
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: var(--border-default);
}

.header-right {
  display: flex;
  gap: var(--space-2);
}

.btn-secondary,
.btn-primary {
  height: 36px;
  padding: 0 var(--space-4);
  border-radius: var(--radius);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-secondary {
  background: var(--bg-background);
  border: 1px solid var(--border-default);
  color: var(--fg-primary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--border-strong);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--fg-primary);
  border: 1px solid var(--fg-primary);
  color: var(--bg-background);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary.is-active {
  background: var(--bg-secondary);
  border-color: var(--border-default);
  color: var(--fg-primary);
}

.result-tabs {
  display: flex;
  gap: var(--space-6);
  border-bottom: 1px solid var(--border-default);
  margin-bottom: var(--space-6);
}

.tab-btn {
  background: none;
  border: none;
  padding: var(--space-3) 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--fg-secondary);
  cursor: pointer;
  position: relative;
  transition: color var(--transition-fast);
}

.tab-btn:hover {
  color: var(--fg-primary);
}

.tab-btn.active {
  color: var(--fg-primary);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--fg-primary);
}

.result-content {
  min-height: 300px;
}

.tab-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.section-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.summary-text {
  font-size: var(--font-size-md);
  color: var(--fg-secondary);
  line-height: 1.7;
  margin: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-2);
}

.metric-card {
  background: var(--bg-secondary);
  border-radius: var(--radius);
  padding: var(--space-4) var(--space-5);
  text-align: left;
  border: 1px solid var(--border-secondary);
}

.metric-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin-bottom: var(--space-1);
  font-family: var(--geist-mono);
  letter-spacing: -0.01em;
}

.metric-label {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: var(--font-weight-medium);
}

.tech-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tech-tag {
  font-size: var(--font-size-sm);
  color: var(--fg-primary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-3);
  font-family: var(--geist-mono);
}

.score-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.score-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.score-label {
  width: 140px;
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  flex-shrink: 0;
}

.score-bar-wrap {
  flex: 1;
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--border-secondary);
}

.score-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-blue-light), var(--accent-blue));
  border-radius: 4px;
  transition: width var(--transition-slow);
}

.score-num {
  width: 40px;
  text-align: right;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  font-family: var(--geist-mono);
  flex-shrink: 0;
}

.suitable-text {
  font-size: var(--font-size-base);
  color: var(--fg-secondary);
  margin: 0;
  line-height: 1.6;
}

.point-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.point-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  background: var(--bg-background);
}

.point-marker {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}

.point-item.positive .point-marker {
  background: var(--bg-secondary);
  color: var(--fg-primary);
}

.point-item.negative .point-marker {
  background: var(--bg-secondary);
  color: var(--error-light);
}

.point-text {
  flex: 1;
  font-size: var(--font-size-base);
  color: var(--fg-secondary);
  line-height: 1.6;
}

/* 安全检测样式 */
.security-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-10) 0;
}

.security-empty .empty-text {
  color: var(--fg-tertiary);
  font-size: var(--font-size-md);
  margin: 0;
}

.security-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-10) 0;
  color: var(--fg-tertiary);
  font-size: var(--font-size-md);
}

.security-result {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.security-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.risk-badge.risk-low {
  background: var(--bg-secondary);
  color: #67c23a;
}

.risk-badge.risk-medium {
  background: var(--bg-secondary);
  color: #e6a23c;
}

.risk-badge.risk-high {
  background: var(--bg-secondary);
  color: #f56c6c;
}

.risk-badge.risk-critical {
  background: #2a0000;
  color: #ff4d4f;
}

.risk-score {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  font-weight: var(--font-weight-medium);
}

.security-summary {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--fg-secondary);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-secondary);
  border-radius: var(--radius);
  margin: 0;
}

.sub-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.security-table {
  width: 100%;
  font-size: var(--font-size-sm);
}

.security-table :deep(.el-table__header-wrapper) {
  background: var(--bg-secondary);
}

.security-table :deep(.el-table__header-row) {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.security-table :deep(.el-table__body-row) {
  color: var(--fg-secondary);
}

.security-table :deep(.el-table__cell) {
  padding: var(--space-2) var(--space-3);
  line-height: 1.5;
}

.status-tag {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-tag.pass,
.status-tag.通过 {
  background: var(--bg-secondary);
  color: #67c23a;
}

.status-tag.warning,
.status-tag.警告 {
  background: var(--bg-secondary);
  color: #e6a23c;
}

.status-tag.failed,
.status-tag.失败 {
  background: #2a0000;
  color: #ff4d4f;
}

.severity-tag {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.severity-tag.severity-critical {
  background: #2a0000;
  color: #ff4d4f;
}

.severity-tag.severity-high {
  background: var(--bg-secondary);
  color: #f56c6c;
}

.severity-tag.severity-medium {
  background: var(--bg-secondary);
  color: #e6a23c;
}

.severity-tag.severity-low {
  background: var(--bg-secondary);
  color: #67c23a;
}

.safe-state {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-6);
  justify-content: center;
  color: #67c23a;
  font-size: var(--font-size-md);
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .result-header {
    flex-direction: column;
  }

  .score-label {
    width: 100px;
  }
}
</style>
