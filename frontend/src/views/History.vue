<template>
  <div class="history">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">历史记录</h1>
        <p class="page-desc">共 {{ total }} 条记录</p>
      </div>
      <div class="header-right">
        <div class="search-wrap">
          <input
            v-model="keyword"
            class="search-input"
            :placeholder="activeTab === 'reports' ? '搜索仓库...' : '搜索对话问题...'"
            @input="handleSearchInput"
          />
        </div>
        <button
          class="btn-secondary"
          :disabled="selectedIds.length === 0"
          @click="handleBatchDelete"
        >
          删除 {{ selectedIds.length > 0 ? `(${selectedIds.length})` : '' }}
        </button>
        <button class="btn-danger" @click="showDeleteAllConfirm = true">
          清空全部
        </button>
      </div>
    </div>

    <div class="tabs">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'reports' }"
        @click="switchTab('reports')"
      >
        分析报告
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'chat' }"
        @click="switchTab('chat')"
      >
        AI 对话
      </button>
    </div>

    <!-- 分析报告 Tab -->
    <template v-if="activeTab === 'reports'">
      <div v-if="loading" class="loading-row">
        <div class="spinner-sm" />
        <span>加载中...</span>
      </div>

      <div v-else-if="reports.length === 0" class="empty-state">
        <p class="empty-text">{{ keyword ? '未找到匹配的报告' : '暂无分析历史' }}</p>
        <button class="btn-primary" @click="$router.push('/')">去分析仓库</button>
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-check">
                <input
                  type="checkbox"
                  :checked="isAllSelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="col-name">仓库</th>
              <th class="col-score">评分</th>
              <th class="col-lang">语言</th>
              <th class="col-num">Stars</th>
              <th class="col-date">分析时间</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in reports" :key="row.id" class="table-row">
              <td class="col-check">
                <input
                  type="checkbox"
                  :checked="selectedIds.includes(row.id)"
                  @change="toggleSelect(row.id)"
                />
              </td>
              <td class="col-name">
                <span class="repo-name" @click="goDetail(row.id)">{{ row.repo_full_name }}</span>
              </td>
              <td class="col-score">
                <span class="score-badge" :class="getScoreClass(row.overall_score)">
                  {{ row.overall_score }}
                </span>
              </td>
              <td class="col-lang">
                <span v-if="row.language" class="lang-tag">{{ row.language }}</span>
                <span v-else class="muted">—</span>
              </td>
              <td class="col-num mono">{{ formatNumber(row.stars) }}</td>
              <td class="col-date mono">{{ formatDate(row.created_at) }}</td>
              <td class="col-actions">
                <button class="link-btn" @click="goDetail(row.id)">查看</button>
                <button class="link-btn danger" @click="handleDelete(row.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- AI 对话 Tab -->
    <template v-else>
      <div v-if="loading" class="loading-row">
        <div class="spinner-sm" />
        <span>加载中...</span>
      </div>

      <div v-else-if="chatRecords.length === 0" class="empty-state">
        <p class="empty-text">{{ keyword ? '未找到匹配的对话' : '暂无 AI 对话记录' }}</p>
        <button class="btn-primary" @click="$router.push('/chat')">去 AI 推荐</button>
      </div>

      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th class="col-check">
                <input
                  type="checkbox"
                  :checked="isAllChatSelected"
                  @change="toggleSelectAllChat"
                />
              </th>
              <th class="col-query">问题</th>
              <th class="col-num">推荐数</th>
              <th class="col-inject">注入标记</th>
              <th class="col-date">时间</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in chatRecords" :key="row.id" class="table-row">
              <td class="col-check">
                <input
                  type="checkbox"
                  :checked="selectedChatIds.includes(row.id)"
                  @change="toggleSelectChat(row.id)"
                />
              </td>
              <td class="col-query">
                <span class="repo-name" @click="openDetail(row)">{{ row.query }}</span>
              </td>
              <td class="col-num mono">{{ row.total }}</td>
              <td class="col-inject">
                <span class="inject-tag" :class="row.injection_detected ? 'warn' : 'safe'">
                  {{ row.injection_detected ? '警告' : '安全' }}
                </span>
              </td>
              <td class="col-date mono">{{ formatDate(row.created_at) }}</td>
              <td class="col-actions">
                <button class="link-btn" @click="openDetail(row)">查看</button>
                <button class="link-btn danger" @click="handleDeleteChat(row.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="total > 0" class="pagination">
      <button class="page-btn" :disabled="page === 1" @click="page = page - 1; fetchData()">
        上一页
      </button>
      <span class="page-info">
        第 {{ page }} / {{ totalPages }} 页
      </span>
      <button
        class="page-btn"
        :disabled="page >= totalPages"
        @click="page = page + 1; fetchData()"
      >
        下一页
      </button>
      <select class="page-size" :value="pageSize" @change="handleSizeChange">
        <option :value="10">10 条/页</option>
        <option :value="20">20 条/页</option>
        <option :value="50">50 条/页</option>
      </select>
    </div>

    <!-- 对话详情弹窗 -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal modal-lg">
        <div class="modal-head">
          <h3 class="modal-title">对话详情</h3>
          <button class="modal-close" @click="showDetail = false">×</button>
        </div>
        <p class="modal-desc">
          <strong>问题：</strong>{{ currentDetail?.query }}
          <span class="inject-tag" :class="currentDetail?.injection_detected ? 'warn' : 'safe'">
            {{ currentDetail?.injection_detected ? '警告' : '安全' }}
          </span>
        </p>
        <div class="detail-items">
          <div v-for="(item, idx) in currentDetail?.items || []" :key="idx" class="detail-item">
            <span class="rank">{{ idx + 1 }}</span>
            <div class="item-body">
              <div class="item-name">
                <a :href="item.github_url" target="_blank" rel="noopener" class="repo-link">
                  {{ item.author }}/{{ item.name }}
                </a>
                <span class="lang-tag">{{ item.language }}</span>
                <span class="stars-text">{{ item.stars }}</span>
              </div>
              <p class="item-desc">{{ item.description }}</p>
              <p class="item-meta"><strong>场景：</strong>{{ item.use_case }}</p>
              <p class="item-meta"><strong>理由：</strong>{{ item.reason }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showDeleteAllConfirm" class="modal-overlay" @click.self="showDeleteAllConfirm = false">
      <div class="modal">
        <h3 class="modal-title">清空全部历史</h3>
        <p class="modal-desc">此操作将永久删除全部 {{ total }} 条{{ activeTab === 'reports' ? '分析报告' : '对话记录' }}，不可恢复。</p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDeleteAllConfirm = false">取消</button>
          <button class="btn-danger" @click="confirmDeleteAll">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api';

const router = useRouter();

const reports = ref([]);
const chatRecords = ref([]);
const loading = ref(false);
const keyword = ref('');
const page = ref(1);
const pageSize = ref(10);
const total = ref(0);
const selectedIds = ref([]);
const selectedChatIds = ref([]);
const showDeleteAllConfirm = ref(false);
const activeTab = ref('reports');
const showDetail = ref(false);
const currentDetail = ref(null);

let searchTimer = null;

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value) || 1;
});

const isAllSelected = computed(() => {
  return reports.value.length > 0 && reports.value.every(r => selectedIds.value.includes(r.id));
});

const isAllChatSelected = computed(() => {
  return chatRecords.value.length > 0 && chatRecords.value.every(r => selectedChatIds.value.includes(r.id));
});

function formatNumber(num) {
  if (!num && num !== 0) return '0';
  if (num >= 10000) return (num / 10000).toFixed(1) + 'k';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function getScoreClass(score) {
  if (score >= 80) return 'score-high';
  if (score >= 60) return 'score-mid';
  return 'score-low';
}

function switchTab(tab) {
  if (activeTab.value === tab) return;
  activeTab.value = tab;
  keyword.value = '';
  page.value = 1;
  selectedIds.value = [];
  selectedChatIds.value = [];
  fetchData();
}

async function fetchData() {
  if (activeTab.value === 'reports') {
    await fetchReports();
  } else {
    await fetchChatRecords();
  }
}

async function fetchReports() {
  loading.value = true;
  try {
    const res = await api.getReportList({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    });
    if (res.data) {
      reports.value = res.data.items || res.data || [];
      total.value = res.data.total || reports.value.length;
    }
  } catch (error) {
    console.error(error);
    reports.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
    selectedIds.value = [];
  }
}

async function fetchChatRecords() {
  loading.value = true;
  try {
    const res = await api.getChatHistory({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    });
    if (res.data) {
      chatRecords.value = res.data.items || [];
      total.value = res.data.total || 0;
    }
  } catch (error) {
    console.error(error);
    chatRecords.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
    selectedChatIds.value = [];
  }
}

function goDetail(reportId) {
  router.push({ name: 'Home', query: { reportId } });
}

function openDetail(row) {
  currentDetail.value = row;
  showDetail.value = true;
}

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id);
  if (idx > -1) {
    selectedIds.value.splice(idx, 1);
  } else {
    selectedIds.value.push(id);
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = [];
  } else {
    selectedIds.value = reports.value.map(r => r.id);
  }
}

function toggleSelectChat(id) {
  const idx = selectedChatIds.value.indexOf(id);
  if (idx > -1) {
    selectedChatIds.value.splice(idx, 1);
  } else {
    selectedChatIds.value.push(id);
  }
}

function toggleSelectAllChat() {
  if (isAllChatSelected.value) {
    selectedChatIds.value = [];
  } else {
    selectedChatIds.value = chatRecords.value.map(r => r.id);
  }
}

async function handleDelete(reportId) {
  try {
    await api.deleteReport(reportId);
    ElMessage.success('删除成功');
    if (reports.value.length === 1 && page.value > 1) {
      page.value -= 1;
    }
    fetchData();
  } catch (error) {
    console.error(error);
  }
}

async function handleDeleteChat(recordId) {
  try {
    await api.deleteChatHistory(recordId);
    ElMessage.success('删除成功');
    if (chatRecords.value.length === 1 && page.value > 1) {
      page.value -= 1;
    }
    fetchData();
  } catch (error) {
    console.error(error);
  }
}

async function handleBatchDelete() {
  if (activeTab.value === 'reports') {
    if (selectedIds.value.length === 0) return;
    try {
      await api.deleteReportsBatch(selectedIds.value);
      ElMessage.success(`已删除 ${selectedIds.value.length} 条记录`);
      const remaining = reports.value.length - selectedIds.value.length;
      if (remaining <= 0 && page.value > 1) {
        page.value -= 1;
      }
      fetchReports();
    } catch (error) {
      console.error(error);
      ElMessage.error('批量删除失败');
    }
  } else {
    if (selectedChatIds.value.length === 0) return;
    // 后端不提供批量删除接口，逐个删除
    try {
      let successCount = 0;
      for (const id of selectedChatIds.value) {
        try {
          await api.deleteChatHistory(id);
          successCount++;
        } catch (e) { /* 忽略单个失败 */ }
      }
      ElMessage.success(`已删除 ${successCount} 条记录`);
      const remaining = chatRecords.value.length - selectedChatIds.value.length;
      if (remaining <= 0 && page.value > 1) {
        page.value -= 1;
      }
      fetchChatRecords();
    } catch (error) {
      console.error(error);
      ElMessage.error('批量删除失败');
    }
  }
}

async function confirmDeleteAll() {
  try {
    if (activeTab.value === 'reports') {
      const res = await api.deleteAllReports();
      ElMessage.success(res.data?.message || '已清空全部报告');
    } else {
      const res = await api.clearChatHistory();
      ElMessage.success(res.data?.message || '已清空全部对话记录');
    }
    page.value = 1;
    showDeleteAllConfirm.value = false;
    fetchData();
  } catch (error) {
    console.error(error);
    ElMessage.error('清空失败');
  }
}

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    page.value = 1;
    fetchData();
  }, 300);
}

function handlePageChange(p) {
  page.value = p;
  fetchData();
}

function handleSizeChange(e) {
  pageSize.value = parseInt(e.target.value, 10);
  page.value = 1;
  fetchData();
}

onMounted(() => {
  fetchData();
});

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer);
});
</script>

<style scoped>
.history {
  min-height: 60vh;
}

.tabs {
  display: flex;
  gap: var(--space-2);
  border-bottom: 1px solid var(--border-default);
  margin-bottom: var(--space-6);
}

.tab-btn {
  background: none;
  border: none;
  padding: var(--space-3) var(--space-5);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--fg-tertiary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--fg-primary);
}

.tab-btn.active {
  color: var(--fg-primary);
  border-bottom-color: var(--fg-primary);
}

.col-query {
  min-width: 220px;
}

.col-inject {
  width: 110px;
}

.inject-tag {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.inject-tag.safe {
  background: var(--accent-green, #10b981);
  color: white;
}

.inject-tag.warn {
  background: var(--warning, #f59e0b);
  color: white;
}

.modal-lg {
  max-width: 640px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-close {
  background: none;
  border: none;
  font-size: var(--font-size-xl);
  color: var(--fg-tertiary);
  cursor: pointer;
  line-height: 1;
}

.modal-close:hover {
  color: var(--fg-primary);
}

.detail-items {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.detail-item {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  background: var(--bg-secondary);
}

.rank {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: var(--fg-primary);
  color: var(--bg-background);
  font-family: var(--geist-mono);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.item-body {
  flex: 1;
}

.item-name {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-bottom: var(--space-1);
}

.repo-link {
  color: var(--fg-primary);
  font-family: var(--geist-mono);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
}

.repo-link:hover {
  text-decoration: underline;
}

.stars-text {
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
}

.item-desc {
  margin: 0 0 var(--space-1) 0;
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
}

.item-meta {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  line-height: 1.5;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: var(--space-6);
  gap: var(--space-4);
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.page-desc {
  font-size: var(--font-size-sm);
  color: var(--fg-tertiary);
  margin: 0;
  font-family: var(--geist-mono);
}

.header-right {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
}

.search-wrap {
  position: relative;
}

.search-input {
  width: 240px;
  height: 36px;
  padding: 0 var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  font-size: var(--font-size-sm);
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

.btn-secondary,
.btn-primary,
.btn-danger {
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
  opacity: 0.4;
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

.btn-danger {
  background: var(--bg-background);
  border: 1px solid var(--border-default);
  color: var(--error-light);
}

.btn-danger:hover:not(:disabled) {
  background: var(--error-light);
  border-color: var(--error-light);
  color: white;
}

.loading-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-10) 0;
  color: var(--fg-tertiary);
  font-size: var(--font-size-sm);
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-default);
  border-top-color: var(--fg-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: var(--space-10) 0;
}

.empty-text {
  font-size: var(--font-size-base);
  color: var(--fg-tertiary);
  margin: 0 0 var(--space-4) 0;
}

.table-wrap {
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--bg-background);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.data-table thead {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
}

.data-table th {
  text-align: left;
  padding: var(--space-2) var(--space-4);
  font-weight: var(--font-weight-medium);
  color: var(--fg-secondary);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border-default);
}

.data-table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-secondary);
  color: var(--fg-primary);
  vertical-align: middle;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: var(--bg-secondary);
}

.col-check {
  width: 40px;
}

.col-name {
  min-width: 240px;
}

.col-score {
  width: 100px;
}

.col-lang {
  width: 140px;
}

.col-num {
  width: 100px;
}

.col-date {
  width: 160px;
}

.col-actions {
  width: 140px;
  text-align: right;
}

.repo-name {
  font-family: var(--geist-mono);
  font-weight: var(--font-weight-medium);
  color: var(--fg-primary);
  cursor: pointer;
  font-size: var(--font-size-sm);
}

.repo-name:hover {
  text-decoration: underline;
}

.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 24px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  font-family: var(--geist-mono);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.score-high {
  background: var(--accent-blue);
  color: white;
}

.score-mid {
  background: var(--bg-secondary);
  color: var(--fg-primary);
  border: 1px solid var(--border-default);
}

.score-low {
  background: var(--bg-secondary);
  color: var(--error-light);
  border: 1px solid var(--border-default);
}

.lang-tag {
  display: inline-block;
  padding: 2px var(--space-2);
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
}

.mono {
  font-family: var(--geist-mono);
  color: var(--fg-secondary);
}

.muted {
  color: var(--fg-tertiary);
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  margin-left: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color var(--transition-fast);
}

.link-btn:first-child {
  margin-left: 0;
}

.link-btn:hover {
  color: var(--fg-primary);
}

.link-btn.danger:hover {
  color: var(--error-light);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  margin-top: var(--space-6);
}

.page-btn {
  height: 32px;
  padding: 0 var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  background: var(--bg-background);
  color: var(--fg-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--border-strong);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
}

.page-size {
  height: 32px;
  padding: 0 var(--space-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  background: var(--bg-background);
  color: var(--fg-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  outline: none;
}

.page-size:focus {
  border-color: var(--fg-primary);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-background);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  padding: var(--space-6);
  max-width: 400px;
  width: 90%;
}

.modal-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin: 0 0 var(--space-3) 0;
}

.modal-desc {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  margin: 0 0 var(--space-6) 0;
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .col-lang,
  .col-date {
    display: none;
  }
}
</style>
