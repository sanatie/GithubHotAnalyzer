<template>
  <div class="favorites">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">我的收藏</h1>
        <p class="page-desc">共 {{ total }} 个收藏仓库</p>
      </div>
      <div class="header-right">
        <div class="search-wrap">
          <input
            v-model="keyword"
            class="search-input"
            placeholder="搜索收藏..."
            @input="handleSearchInput"
          />
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-row">
      <div class="spinner-sm" />
      <span>加载中...</span>
    </div>

    <div v-else-if="favorites.length === 0" class="empty-state">
      <p class="empty-text">{{ keyword ? '未找到匹配的收藏' : '暂无收藏的仓库' }}</p>
      <button class="btn-primary" @click="$router.push('/')">去探索仓库</button>
    </div>

    <div v-else class="repo-grid">
      <div v-for="item in favorites" :key="item.id" class="repo-card">
        <div class="card-header">
          <img
            v-if="item.repository?.avatar_url"
            :src="item.repository.avatar_url"
            class="avatar"
            alt=""
          />
          <div class="avatar-fallback" v-else>
            {{ getItemInitial(item) }}
          </div>
          <div class="repo-info">
            <div class="repo-name" @click="goDetail(item)">{{ item.repo_full_name }}</div>
            <div class="repo-meta">
              <span v-if="item.repository?.language" class="lang-dot">{{ item.repository.language }}</span>
              <span v-if="item.repository?.stargazers_count" class="star-count">
                {{ formatNumber(item.repository.stargazers_count) }}
              </span>
              <span v-if="item.overall_score !== undefined && item.overall_score !== null" class="score">
                {{ item.overall_score }}
              </span>
            </div>
          </div>
        </div>
        <p v-if="item.repository?.description" class="repo-desc">
          {{ item.repository.description }}
        </p>
        <div class="card-footer">
          <span class="fav-time">收藏于 {{ formatDate(item.created_at) }}</span>
          <div class="card-actions">
            <button class="link-btn" @click="goDetail(item)">查看报告</button>
            <button class="link-btn danger" @click="handleUnfavorite(item.id)">取消收藏</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="total > 0" class="pagination">
      <button class="page-btn" :disabled="page === 1" @click="page = page - 1; fetchFavorites()">
        上一页
      </button>
      <span class="page-info">
        第 {{ page }} / {{ totalPages }} 页
      </span>
      <button
        class="page-btn"
        :disabled="page >= totalPages"
        @click="page = page + 1; fetchFavorites()"
      >
        下一页
      </button>
      <select class="page-size" :value="pageSize" @change="handleSizeChange">
        <option :value="12">12 个/页</option>
        <option :value="24">24 个/页</option>
        <option :value="48">48 个/页</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api';

const router = useRouter();

const favorites = ref([]);
const loading = ref(false);
const keyword = ref('');
const page = ref(1);
const pageSize = ref(12);
const total = ref(0);

let searchTimer = null;

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value) || 1;
});

function getItemInitial(item) {
  const name = item.repo_full_name || item.repository?.full_name || '?';
  return name.charAt(0).toUpperCase();
}

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
  const now = new Date();
  const diff = now - d;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return '今天';
  if (days === 1) return '昨天';
  if (days < 30) return `${days} 天前`;
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

async function fetchFavorites() {
  loading.value = true;
  try {
    const res = await api.getFavorites({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    });
    if (res.data) {
      favorites.value = res.data.items || res.data || [];
      total.value = res.data.total || favorites.value.length;
    }
  } catch (error) {
    console.error(error);
    favorites.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function goDetail(item) {
  if (item.report_id) {
    router.push({ name: 'Home', query: { reportId: item.report_id } });
    return;
  }
  const repoFullName = item.repo_full_name || item.repository?.full_name;
  if (repoFullName) {
    router.push({ name: 'Home', query: { url: `https://github.com/${repoFullName}` } });
    return;
  }
  router.push({ name: 'Home' });
}

async function handleUnfavorite(favId) {
  try {
    await api.deleteFavorite(favId);
    ElMessage.success('已取消收藏');
    if (favorites.value.length === 1 && page.value > 1) {
      page.value -= 1;
    }
    fetchFavorites();
  } catch (error) {
    console.error(error);
  }
}

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    page.value = 1;
    fetchFavorites();
  }, 300);
}

function handleSizeChange(e) {
  pageSize.value = parseInt(e.target.value, 10);
  page.value = 1;
  fetchFavorites();
}

onMounted(() => {
  fetchFavorites();
});
</script>

<style scoped>
.favorites {
  min-height: 60vh;
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

.btn-primary {
  height: 36px;
  padding: 0 var(--space-4);
  border-radius: var(--radius);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  background: var(--fg-primary);
  border: 1px solid var(--fg-primary);
  color: var(--bg-background);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.repo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-3);
}

.repo-card {
  background: var(--bg-background);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: all var(--transition-fast);
}

.repo-card:hover {
  border-color: var(--border-strong);
}

.card-header {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
  flex-shrink: 0;
  background: var(--bg-secondary);
}

.avatar-fallback {
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-secondary);
  flex-shrink: 0;
  font-family: var(--geist-mono);
}

.repo-info {
  flex: 1;
  min-width: 0;
}

.repo-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  cursor: pointer;
  font-family: var(--geist-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: var(--space-1);
}

.repo-name:hover {
  text-decoration: underline;
}

.repo-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.lang-dot {
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
}

.star-count {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
}

.score {
  font-size: var(--font-size-xs);
  color: var(--accent-blue);
  font-weight: var(--font-weight-semibold);
  font-family: var(--geist-mono);
}

.repo-desc {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-secondary);
  flex-wrap: wrap;
  gap: var(--space-2);
}

.fav-time {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
}

.card-actions {
  display: flex;
  gap: var(--space-3);
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color var(--transition-fast);
  font-weight: var(--font-weight-medium);
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
  margin-top: var(--space-8);
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

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-input {
    width: 100%;
  }

  .repo-grid {
    grid-template-columns: 1fr;
  }
}
</style>
