<template>
  <div class="analyze">
    <div class="page-header">
      <el-button @click="$router.push('/')" :icon="ArrowLeft">返回首页</el-button>
      <h2>仓库分析结果</h2>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <LoadingState type="spinner" message="正在获取分析结果..." />
    </div>

    <div v-else-if="report" class="report-container">
      <div class="report-main">
        <ReportViewer :report="formattedReport" :report-id="report?.id" :security="report?.content?.security" @security-done="fetchReport" />
      </div>
      <div class="report-side">
        <ScorePanel
          :scores="{ overall: report.overall_score }"
          :breakdown="scoreBreakdown"
          :suitable-for="suitableForText"
        />
        <div class="actions">
          <el-button type="primary" @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            重新分析
          </el-button>
          <el-button @click="handleFavorite">
            <el-icon><Star /></el-icon>
            {{ isFavorited ? '已收藏' : '收藏' }}
          </el-button>
        </div>
      </div>
    </div>

    <div v-else class="empty-wrapper">
      <el-empty description="暂无分析结果">
        <el-button type="primary" @click="$router.push('/')">
          去首页分析仓库
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, Refresh, Star } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import api from '../api';
import ReportViewer from '../components/ReportViewer.vue';
import ScorePanel from '../components/ScorePanel.vue';
import LoadingState from '../components/LoadingState.vue';

const route = useRoute();
const router = useRouter();

const report = ref(null);
const loading = ref(true);
const isFavorited = ref(false);

const scoreBreakdown = computed(() => {
  if (!report.value) return {};
  if (report.value.score_breakdown) {
    return report.value.score_breakdown;
  }
  if (report.value.content?.score_breakdown) {
    return report.value.content.score_breakdown;
  }
  return {};
});

const suitableForText = computed(() => {
  if (!report.value) return '';
  let suitable = report.value.suitable_for;
  if (!suitable && report.value.content?.suitable_for) {
    suitable = report.value.content.suitable_for;
  }
  if (Array.isArray(suitable)) {
    return suitable.join('、');
  }
  return suitable || '';
});

const formattedReport = computed(() => {
  if (!report.value) return null;
  const content = report.value.content || {};
  const repo = report.value.repository || report.value.repo || {};
  return {
    repository_name: report.value.repo_full_name || report.value.repository_name || '未知仓库',
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
    summary: content.summary || report.value.summary || '暂无简介',
    tech_stack: content.tech_stack || [],
    strengths: content.highlights || content.strengths || [],
    weaknesses: content.weaknesses || [],
    suggestions: content.suggestions || (content.learning_advice ? [content.learning_advice] : []),
  };
});

async function fetchReport() {
  loading.value = true;
  try {
    if (!route.query.reportId) return;
    const res = await api.getReportDetail(route.query.reportId);
    report.value = res.data;
    if (res.data?.repo_id) {
      const favRes = await api.checkFavorite(res.data.repo_id);
      isFavorited.value = favRes.data?.is_favorited || false;
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('获取报告失败');
  } finally {
    loading.value = false;
  }
}

async function handleRefresh() {
  if (!report.value?.repo_full_name) return;
  loading.value = true;
  try {
    const res = await api.analyzeRepo({
      repo_url: `https://github.com/${report.value.repo_full_name}`,
      force_refresh: true
    });
    if (res.data?.report_id) {
      router.replace({ query: { reportId: res.data.report_id } });
      await fetchReport();
    }
    ElMessage.success('重新分析完成');
  } catch (error) {
    ElMessage.error('重新分析失败');
  } finally {
    loading.value = false;
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
        note: ''
      });
      isFavorited.value = true;
      ElMessage.success('收藏成功');
    }
  } catch (error) {
    ElMessage.error('操作失败');
  }
}

onMounted(() => {
  fetchReport();
});
</script>

<style scoped>
.analyze {
  min-height: 100vh;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.loading-wrapper,
.empty-wrapper {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.report-container {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.report-main {
  flex: 1;
  min-width: 0;
}

.report-side {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.actions :deep(.el-button) {
  width: 100%;
}

@media (max-width: 900px) {
  .report-container {
    flex-direction: column;
  }
  .report-side {
    width: 100%;
  }
}
</style>
