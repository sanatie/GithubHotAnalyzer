<template>
  <div class="chat-page">
    <!-- 输入区 -->
    <div class="chat-input-section">
      <div class="chat-input-wrapper">
        <el-input
          v-model="query"
          type="textarea"
          :rows="3"
          placeholder="描述你的需求，例如：我想学嵌入式开发，推荐 STM32 相关项目"
          resize="none"
          maxlength="500"
          show-word-limit
          @keydown.enter.exact.prevent="handleRecommend"
          :disabled="loading"
        />
        <div class="chat-actions">
          <el-button type="primary" @click="handleRecommend" :loading="loading">
            推 荐
          </el-button>
          <el-button @click="handleClear" :disabled="loading">清 空</el-button>
        </div>
      </div>

      <!-- 快捷标签 -->
      <div class="quick-tags">
        <span class="quick-label">快捷标签：</span>
        <el-tag
          v-for="tag in quickTags"
          :key="tag"
          class="quick-tag"
          effect="plain"
          @click="handleQuickTag(tag)"
        >
          {{ tag }}
        </el-tag>
      </div>

      <!-- 历史记录 -->
      <div class="history-section" v-if="history.length > 0">
        <span class="quick-label">最近查询：</span>
        <el-tag
          v-for="(h, i) in history"
          :key="i"
          class="history-tag"
          type="info"
          effect="plain"
          @click="query = h; handleRecommend()"
        >
          {{ h.length > 20 ? h.slice(0, 20) + '...' : h }}
        </el-tag>
        <el-button
          class="history-clear"
          link
          type="danger"
          size="small"
          @click="handleClearHistory"
        >
          清空
        </el-button>
      </div>
    </div>

    <!-- 注入警告 -->
    <el-alert
      v-if="injectionDetected"
      title="检测到疑似 Prompt 注入"
      type="warning"
      description="您的输入中包含可能影响 AI 正常工作的内容，已自动隔离处理。"
      show-icon
      :closable="true"
      style="margin-bottom: 16px;"
    />

    <!-- 结果区 -->
    <div class="chat-results" v-if="loading || results.length > 0 || error">
      <!-- 加载中 -->
      <div v-if="loading" class="loading-section">
        <div class="skeleton-card" v-for="i in 3" :key="i">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line skeleton-desc"></div>
          <div class="skeleton-line skeleton-tags"></div>
        </div>
      </div>

      <!-- 错误状态 -->
      <el-result
        v-else-if="error"
        icon="error"
        title="推荐失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="handleRecommend">重 试</el-button>
        </template>
      </el-result>

      <!-- 正常结果 -->
      <template v-else>
        <div class="results-header">
          <span class="results-title">推荐结果</span>
          <span class="results-count">共 {{ results.length }} 个项目</span>
        </div>

        <div
          v-for="(item, idx) in results"
          :key="idx"
          class="recommend-card"
          :class="{ 'top-rank': idx < 3 }"
          :style="{ animationDelay: idx * 0.15 + 's' }"
        >
          <div class="card-rank">{{ idx + 1 }}</div>
          <div class="card-body">
            <!-- 标题行 -->
            <div class="card-header">
              <span class="card-name" @click="copyName(item.name)">
                {{ item.name }}
              </span>
              <el-tag size="small" type="info" effect="plain">
                {{ item.language }}
              </el-tag>
              <span class="card-stars">{{ item.stars }}</span>
            </div>

            <!-- 作者 -->
            <div class="card-author">{{ item.author }}</div>

            <!-- 描述 -->
            <div class="card-desc">{{ item.description }}</div>

            <!-- 应用场景 -->
            <div class="card-field">
              <span class="field-label">应用场景</span>
              <span class="field-value">{{ item.use_case }}</span>
            </div>

            <!-- 推荐理由 -->
            <div class="card-field">
              <span class="field-label">推荐理由</span>
              <span class="field-value">{{ item.reason }}</span>
            </div>

            <!-- 操作按钮 -->
            <div class="card-actions">
              <el-button
                size="small"
                type="primary"
                plain
                @click="openGithub(item.github_url)"
              >
                GitHub
              </el-button>
              <el-button
                size="small"
                type="success"
                plain
                @click="handleAnalyze(item)"
              >
                分析
              </el-button>
              <el-button
                size="small"
                type="warning"
                plain
                :loading="favoriting === idx"
                @click="handleFavorite(item, idx)"
              >
                收藏
              </el-button>
              <el-button
                size="small"
                :type="isInCart(item) ? 'success' : 'primary'"
                :plain="false"
                @click="handleAddToCart(item)"
              >
                {{ isInCart(item) ? '已加入' : '加入购物车' }}
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!loading && results.length === 0 && !error">
      <el-empty description="输入需求后获取 AI 推荐项目" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api';
import useCart from '../stores/cart';

const router = useRouter();
const { isInCart, addToCart } = useCart();

function handleAddToCart(item) {
  const res = addToCart({
    name: item.name,
    author: item.author,
    description: item.description || '',
    language: item.language || '',
    stars: item.stars || '',
    github_url: item.github_url || `https://github.com/${item.author}/${item.name}`,
  });
  ElMessage[res.added ? 'success' : 'info'](res.message);
}

const query = ref('');
const loading = ref(false);
const results = ref([]);
const error = ref('');
const injectionDetected = ref(false);
const favoriting = ref(-1);
const history = ref(JSON.parse(localStorage.getItem('chat_history') || '[]'));

const quickTags = [
  '前端框架', '后端框架', '嵌入式', 'AI/ML',
  'DevOps', '数据库', '移动开发', '游戏引擎'
];

async function handleRecommend() {
  if (!query.value.trim()) {
    ElMessage.warning('请输入需求描述');
    return;
  }

  loading.value = true;
  error.value = '';
  results.value = [];
  injectionDetected.value = false;

  // 保存历史
  const q = query.value.trim();
  const hist = history.value.filter(h => h !== q);
  hist.unshift(q);
  if (hist.length > 5) hist.pop();
  history.value = hist;
  localStorage.setItem('chat_history', JSON.stringify(hist));

  try {
    const resp = await api.chatRecommend({ query: q });
    injectionDetected.value = resp.data.injection_detected;
    results.value = resp.data.items || [];
    if (results.value.length === 0) {
      error.value = 'AI 未返回推荐结果，请尝试更具体的需求描述';
    }
  } catch (err) {
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else if (err.message) {
      error.value = err.message;
    } else {
      error.value = '网络错误，请检查后端服务是否启动';
    }
  } finally {
    loading.value = false;
  }
}

function handleClear() {
  query.value = '';
  results.value = [];
  error.value = '';
  injectionDetected.value = false;
}

function handleClearHistory() {
  history.value = [];
  localStorage.removeItem('chat_history');
  ElMessage.info('已清空最近查询');
}

function handleQuickTag(tag) {
  const tagMap = {
    '前端框架': '推荐前端开发框架相关的 GitHub 项目',
    '后端框架': '推荐后端开发框架相关的 GitHub 项目',
    '嵌入式': '推荐嵌入式开发相关的 GitHub 项目，包括 STM32 和 RTOS',
    'AI/ML': '推荐人工智能和机器学习相关的 GitHub 项目',
    'DevOps': '推荐 DevOps 和运维工具相关的 GitHub 项目',
    '数据库': '推荐数据库相关的 GitHub 项目',
    '移动开发': '推荐移动端开发框架相关的 GitHub 项目',
    '游戏引擎': '推荐游戏引擎相关的 GitHub 项目',
  };
  query.value = tagMap[tag] || tag;
  handleRecommend();
}

function openGithub(url) {
  if (url) window.open(url, '_blank');
}

function handleAnalyze(item) {
  router.push({ path: '/', query: { url: item.github_url } });
}

async function handleFavorite(item, idx) {
  favoriting.value = idx;
  try {
    const fullName = item.author + '/' + item.name;
    const repoRes = await api.getRepoByFullName(fullName);
    const repo = repoRes.data;
    await api.addFavorite({
      repo_id: repo.id,
      repo_full_name: fullName,
      note: 'AI 推荐项目'
    });
    ElMessage.success('收藏成功');
  } catch (err) {
    if (err.response?.status === 404) {
      ElMessage.info('请先点击"分析"按钮分析该项目，然后即可收藏');
    } else {
      ElMessage.error('收藏失败：' + (err.response?.data?.detail || err.message));
    }
  } finally {
    favoriting.value = -1;
  }
}

async function copyName(name) {
  try {
    await navigator.clipboard.writeText(name);
    ElMessage.success(`已复制：${name}`);
  } catch {
    ElMessage.warning('复制失败');
  }
}
</script>

<style scoped>
.chat-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

/* 输入区 */
.chat-input-section {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  border: 1px solid var(--border-color, #ebeef5);
}

.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 快捷标签 */
.quick-tags, .history-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.quick-label {
  font-size: 13px;
  color: var(--text-secondary, #909399);
  white-space: nowrap;
}

.quick-tag, .history-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.quick-tag:hover, .history-tag:hover {
  transform: translateY(-1px);
}

.history-clear {
  margin-left: auto;
}

/* 结果区 */
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.results-title {
  font-size: 16px;
  font-weight: 600;
}

.results-count {
  font-size: 13px;
  color: var(--text-secondary, #909399);
}

/* 推荐卡片 */
.recommend-card {
  display: flex;
  gap: 16px;
  background: var(--card-bg, #fff);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid var(--border-color, #ebeef5);
  transition: box-shadow 0.3s, transform 0.3s;
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
}

.recommend-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.top-rank {
  border-left: 3px solid var(--primary-color, #409eff);
}

.card-rank {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary-color, #409eff);
  min-width: 36px;
  text-align: center;
  line-height: 1.2;
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.card-name {
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-primary, #303133);
}

.card-name:hover {
  color: var(--primary-color, #409eff);
}

.card-stars {
  font-size: 13px;
  color: var(--text-secondary, #909399);
  margin-left: auto;
}

.card-author {
  font-size: 13px;
  color: var(--text-secondary, #909399);
  margin: 4px 0 8px;
}

.card-desc {
  font-size: 14px;
  color: var(--text-regular, #606266);
  line-height: 1.6;
  margin-bottom: 12px;
}

.card-field {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.field-label {
  min-width: 70px;
  color: var(--text-secondary, #909399);
  flex-shrink: 0;
}

.field-value {
  color: var(--text-regular, #606266);
  line-height: 1.5;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

/* 骨架屏 */
.loading-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-card {
  background: var(--card-bg, #fff);
  border-radius: 10px;
  padding: 20px;
  border: 1px solid var(--border-color, #ebeef5);
}

.skeleton-line {
  height: 16px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
  margin-bottom: 12px;
}

.skeleton-title { width: 30%; }
.skeleton-desc { width: 80%; height: 12px; }
.skeleton-tags { width: 40%; height: 12px; }

/* 空状态 */
.empty-state {
  padding: 60px 0;
}

/* 动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 响应式 */
@media (max-width: 768px) {
  .card-rank {
    font-size: 20px;
    min-width: 28px;
  }
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .card-stars {
    margin-left: 0;
  }
}
</style>
