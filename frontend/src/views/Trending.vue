<template>
  <div class="trending-page">
    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-left">
        <select v-model="selectedLanguage" class="filter-select" @change="fetchTrending">
          <option value="">All Languages</option>
          <option v-for="lang in languages" :key="lang" :value="lang">{{ lang }}</option>
        </select>
        <div class="filter-info">
          <span class="info-label">Total:</span>
          <span class="info-value">{{ total.toLocaleString() }}</span>
        </div>
      </div>
      <button class="refresh-btn" @click="fetchTrending" :disabled="loading">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-3.5-7.1L21 8M21 3v5h-5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span>Refresh</span>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="skeleton-list">
      <div v-for="i in 6" :key="i" class="skeleton-row">
        <div class="skeleton-rank"></div>
        <div class="skeleton-content">
          <div class="skeleton-line skeleton-line-lg"></div>
          <div class="skeleton-line skeleton-line-sm"></div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" stroke-linecap="round" />
        <circle cx="12" cy="16" r="0.5" fill="currentColor" />
      </svg>
      <p class="error-text">{{ error }}</p>
      <button class="retry-btn" @click="fetchTrending">Retry</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="items.length === 0" class="empty-state">
      <p>No trending repositories found</p>
    </div>

    <!-- Data Content -->
    <template v-else>
      <!-- Top 3 Podium -->
      <div class="podium">
        <div
          v-for="item in topThree"
          :key="item.rank"
          class="podium-card"
          :class="['rank-' + item.rank]"
        >
          <div class="podium-rank">{{ item.rank }}</div>
          <img v-if="item.avatar_url" :src="item.avatar_url" :alt="item.full_name" class="podium-avatar" />
          <div v-else class="podium-avatar-placeholder"></div>
          <a :href="item.html_url" target="_blank" rel="noopener" class="podium-name">{{ item.full_name }}</a>
          <p class="podium-desc">{{ item.description || 'No description' }}</p>
          <div class="podium-stats">
            <div class="stat-item">
              <span class="stat-label">Stars</span>
              <span class="stat-value">{{ formatNumber(item.stargazers_count) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Forks</span>
              <span class="stat-value">{{ formatNumber(item.forks_count) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Issues</span>
              <span class="stat-value">{{ formatNumber(item.open_issues_count) }}</span>
            </div>
          </div>
          <!-- Star Bar -->
          <div class="star-bar-container">
            <div class="star-bar" :style="{ width: starBarWidth(item.stargazers_count) }"></div>
          </div>
          <span v-if="item.language" class="lang-tag" :style="{ borderColor: langColor(item.language) }">
            {{ item.language }}
          </span>
          <button
            class="podium-cart-btn"
            :class="{ added: isInCart(item) }"
            @click="handleAddToCart(item)"
          >
            {{ isInCart(item) ? '✓ 已加入' : '＋ 加入购物车' }}
          </button>
        </div>
      </div>

      <!-- Rank List 4-20 -->
      <div class="rank-table">
        <div class="table-header">
          <div class="col-rank">Rank</div>
          <div class="col-repo">Repository</div>
          <div class="col-lang">Language</div>
          <div class="col-stat">Stars</div>
          <div class="col-stat">Forks</div>
          <div class="col-stat">Issues</div>
          <div class="col-stat">Watchers</div>
          <div class="col-action"></div>
        </div>
        <div
          v-for="item in restItems"
          :key="item.rank"
          class="table-row"
        >
          <div class="col-rank">{{ item.rank }}</div>
          <div class="col-repo">
            <img v-if="item.avatar_url" :src="item.avatar_url" :alt="item.full_name" class="row-avatar" />
            <div v-else class="row-avatar-placeholder"></div>
            <div class="repo-info">
              <a :href="item.html_url" target="_blank" rel="noopener" class="repo-name">{{ item.full_name }}</a>
              <p class="repo-desc">{{ item.description || 'No description' }}</p>
            </div>
          </div>
          <div class="col-lang">
            <span v-if="item.language" class="lang-tag-sm" :style="{ borderColor: langColor(item.language) }">
              {{ item.language }}
            </span>
            <span v-else class="lang-none">--</span>
          </div>
          <div class="col-stat">
            <span class="stat-num">{{ formatNumber(item.stargazers_count) }}</span>
            <div class="mini-bar-container">
              <div class="mini-bar" :style="{ width: starBarWidth(item.stargazers_count) }"></div>
            </div>
          </div>
          <div class="col-stat">{{ formatNumber(item.forks_count) }}</div>
          <div class="col-stat">{{ formatNumber(item.open_issues_count) }}</div>
          <div class="col-stat">{{ formatNumber(item.watchers_count) }}</div>
          <div class="col-action">
            <button
              class="cart-btn"
              :class="{ added: isInCart(item) }"
              @click="handleAddToCart(item)"
            >
              {{ isInCart(item) ? '已加入' : '加入购物车' }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api';
import useCart from '../stores/cart';

const { isInCart, addToCart } = useCart();

function handleAddToCart(item) {
  const [author, ...nameParts] = (item.full_name || '').split('/');
  const name = nameParts.join('/');
  const res = addToCart({
    name,
    author,
    description: item.description || '',
    language: item.language || '',
    stars: formatNumber(item.stargazers_count),
    github_url: item.html_url || `https://github.com/${item.full_name}`,
  });
  ElMessage[res.added ? 'success' : 'info'](res.message);
}

const loading = ref(false);
const error = ref('');
const items = ref([]);
const total = ref(0);
const selectedLanguage = ref('');

const languages = [
  'Python', 'JavaScript', 'TypeScript', 'Java', 'Go',
  'Rust', 'C++', 'C', 'C#', 'Ruby',
  'PHP', 'Swift', 'Kotlin', 'Dart', 'Shell',
  'HTML', 'CSS', 'Vue', 'Markdown',
];

const topThree = computed(() => items.value.slice(0, 3));
const restItems = computed(() => items.value.slice(3));

const maxStars = computed(() => {
  if (items.value.length === 0) return 1;
  return items.value[0].stargazers_count || 1;
});

const starBarWidth = (stars) => {
  const pct = (stars / maxStars.value) * 100;
  return pct > 100 ? '100%' : `${pct}%`;
};

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return String(num);
};

const langColors = {
  Python: '#3572A5',
  JavaScript: '#f1e05a',
  TypeScript: '#3178c6',
  Java: '#b07219',
  Go: '#00ADD8',
  Rust: '#dea584',
  'C++': '#f34b7d',
  C: '#555555',
  'C#': '#178600',
  Ruby: '#701516',
  PHP: '#4F5D95',
  Swift: '#F05138',
  Kotlin: '#A97BFF',
  Dart: '#00B4AB',
  Shell: '#89e051',
  HTML: '#e34c26',
  CSS: '#563d7c',
  Vue: '#41b883',
  Markdown: '#083fa1',
};

const langColor = (lang) => langColors[lang] || '#999';

const fetchTrending = async () => {
  loading.value = true;
  error.value = '';
  try {
    const res = await api.getTrending({
      language: selectedLanguage.value || undefined,
      since: 'weekly',
      limit: 20,
    });
    items.value = res.data.items || [];
    total.value = res.data.total || 0;
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '获取排行榜数据失败';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchTrending();
});
</script>

<style scoped>
.trending-page {
  max-width: 1920px;
  margin: 0 auto;
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.filter-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.filter-select {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-background);
  font-size: var(--font-size-sm);
  font-family: var(--geist-sans);
  color: var(--fg-primary);
  cursor: pointer;
  outline: none;
  transition: border-color var(--transition-fast);
}

.filter-select:hover {
  border-color: var(--border-strong);
}

.filter-select:focus {
  border-color: var(--accent-blue);
}

.filter-info {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.info-label {
  font-size: var(--font-size-sm);
  color: var(--fg-tertiary);
}

.info-value {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
  font-weight: var(--font-weight-medium);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-background);
  font-size: var(--font-size-sm);
  font-family: var(--geist-sans);
  color: var(--fg-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--fg-primary);
  color: var(--fg-primary);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Podium Top 3 */
.podium {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.podium-card {
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: var(--bg-card);
  transition: border-color var(--transition-base);
}

.podium-card:hover {
  border-color: var(--border-strong);
}

.podium-card.rank-1 {
  border-color: var(--fg-primary);
  border-width: 2px;
}

.podium-card.rank-2 {
  border-color: var(--border-strong);
}

.podium-card.rank-3 {
  border-color: var(--border-strong);
}

.podium-rank {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--fg-primary);
  line-height: 1;
  margin-bottom: var(--space-3);
  font-family: var(--geist-mono);
}

.rank-1 .podium-rank {
  color: var(--fg-primary);
}

.rank-2 .podium-rank {
  color: var(--fg-secondary);
}

.rank-3 .podium-rank {
  color: var(--fg-tertiary);
}

.podium-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin-bottom: var(--space-3);
}

.podium-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--bg-secondary);
  margin-bottom: var(--space-3);
}

.podium-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  text-decoration: none;
  margin-bottom: var(--space-2);
  word-break: break-all;
}

.podium-name:hover {
  color: var(--accent-blue);
}

.podium-desc {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  line-height: 1.4;
  margin-bottom: var(--space-4);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.podium-stats {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
}

.stat-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  font-family: var(--geist-mono);
}

.star-bar-container {
  width: 100%;
  height: 4px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: var(--space-3);
}

.star-bar {
  height: 100%;
  background: var(--fg-primary);
  border-radius: 2px;
  transition: width var(--transition-slow);
}

.lang-tag {
  display: inline-block;
  padding: 2px var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  border-left: 3px solid;
}

.podium-cart-btn {
  margin-top: var(--space-3);
  padding: 5px var(--space-4);
  font-size: var(--font-size-xs);
  font-family: var(--geist-sans);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-background);
  color: var(--fg-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.podium-cart-btn:hover {
  border-color: var(--fg-primary);
  color: var(--fg-primary);
}

.podium-cart-btn.added {
  border-color: var(--fg-primary);
  background: var(--fg-primary);
  color: var(--bg-background);
}

/* Rank Table */
.rank-table {
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  overflow-x: auto;
}

.table-header {
  display: grid;
  grid-template-columns: 70px minmax(520px, 1fr) 160px 200px 130px 130px 130px 180px;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  background: var(--bg-canvas);
  border-bottom: 1px solid var(--border-default);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--fg-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.table-row {
  display: grid;
  grid-template-columns: 70px minmax(520px, 1fr) 160px 200px 130px 130px 130px 180px;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  row-gap: var(--space-2);
  min-height: 64px;
  border-bottom: 1px solid var(--border-secondary);
  transition: background-color var(--transition-fast);
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: var(--bg-hover);
}

.col-rank {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
}

.col-repo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.row-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex-shrink: 0;
}

.row-avatar-placeholder {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-secondary);
  flex-shrink: 0;
}

.repo-info {
  min-width: 0;
  overflow: hidden;
}

.repo-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--fg-primary);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.repo-name:hover {
  color: var(--accent-blue);
}

.repo-desc {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.col-lang {
  display: flex;
  align-items: center;
}

.lang-tag-sm {
  display: inline-block;
  padding: 1px var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  border-left: 3px solid;
  white-space: nowrap;
}

.lang-none {
  font-size: var(--font-size-xs);
  color: var(--fg-muted);
}

.col-stat {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
  font-weight: var(--font-weight-medium);
}

.col-stat .stat-num {
  display: block;
  margin-bottom: 4px;
}

.mini-bar-container {
  width: 80px;
  height: 3px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
}

.mini-bar {
  height: 100%;
  background: var(--border-strong);
  border-radius: 2px;
  transition: width var(--transition-slow);
}

.col-action {
  display: flex;
  justify-content: flex-end;
}

.cart-btn {
  padding: 4px var(--space-3);
  font-size: var(--font-size-xs);
  font-family: var(--geist-sans);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-background);
  color: var(--fg-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--transition-fast);
}

.cart-btn:hover {
  border-color: var(--fg-primary);
  color: var(--fg-primary);
}

.cart-btn.added {
  border-color: var(--fg-primary);
  background: var(--fg-primary);
  color: var(--bg-background);
}

/* Skeleton */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.skeleton-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius);
}

.skeleton-rank {
  width: 40px;
  height: 40px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.skeleton-line {
  height: 12px;
  background: var(--bg-secondary);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-line-lg {
  width: 60%;
}

.skeleton-line-sm {
  width: 40%;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10);
  color: var(--fg-tertiary);
  gap: var(--space-4);
}

.error-text {
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
}

.retry-btn {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-background);
  font-size: var(--font-size-sm);
  color: var(--fg-primary);
  cursor: pointer;
}

.retry-btn:hover {
  border-color: var(--fg-primary);
}

/* Empty State */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-10);
  color: var(--fg-tertiary);
  font-size: var(--font-size-sm);
}

/* Responsive */
@media (max-width: 768px) {
  .podium {
    grid-template-columns: 1fr;
  }

  .table-header {
    display: none;
  }

  .table-row {
    grid-template-columns: 40px 1fr;
    gap: var(--space-2);
  }

  .table-row .col-lang,
  .table-row .col-stat {
    display: none;
  }
}
</style>
