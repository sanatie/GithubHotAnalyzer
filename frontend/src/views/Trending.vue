<template>
  <div class="trending-page">
    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-left">
        <div class="since-tabs">
          <button
            v-for="opt in sinceOptions"
            :key="opt.value"
            class="since-tab"
            :class="{ active: selectedSince === opt.value }"
            @click="selectedSince = opt.value; fetchTrending()"
          >
            {{ opt.label }}
          </button>
        </div>
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
      <!-- Summary / Visualization Panel -->
      <div class="viz-panel">
        <div class="summary-cards">
          <div class="summary-card">
            <span class="summary-label">总 Star</span>
            <span class="summary-value">{{ formatNumber(totalStars) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">总 Fork</span>
            <span class="summary-value">{{ formatNumber(totalForks) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">平均 Star</span>
            <span class="summary-value">{{ formatNumber(avgStars) }}</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">上榜语言</span>
            <span class="summary-value">{{ topLanguages.length }}</span>
          </div>
        </div>

        <!-- Language Distribution -->
        <div class="lang-distribution">
          <div class="viz-title">语言分布</div>
          <div class="lang-bars">
            <div
              v-for="lang in topLanguages"
              :key="lang.name"
              class="lang-bar-row"
            >
              <div class="lang-bar-label">
                <span class="lang-dot" :style="{ background: langColor(lang.name) }"></span>
                <span class="lang-name">{{ lang.name }}</span>
                <span class="lang-count">{{ lang.count }} 个</span>
              </div>
              <div class="lang-bar-track">
                <div
                  class="lang-bar"
                  :style="{ width: lang.percent + '%', background: langColor(lang.name) }"
                ></div>
              </div>
              <span class="lang-percent">{{ lang.percent }}%</span>
            </div>
          </div>
        </div>
      </div>

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
          <div class="col-trend">趋势</div>
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
          <div class="col-trend">
            <span
              v-if="getTrend(item)"
              class="trend-badge"
              :class="getTrend(item).dir"
            >
              {{ getTrend(item).arrow }}
            </span>
            <span v-else class="trend-none">—</span>
          </div>
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

const sinceOptions = [
  { value: 'daily', label: '今日' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
];

const selectedSince = ref('weekly');

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

const totalStars = computed(() =>
  items.value.reduce((s, i) => s + (i.stargazers_count || 0), 0)
);

const starBarWidth = (stars) => {
  const pct = (stars / maxStars.value) * 100;
  return pct > 100 ? '100%' : `${pct}%`;
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
  Unknown: '#999',
};

const langColor = (lang) => langColors[lang] || '#999';
const totalForks = computed(() =>
  items.value.reduce((s, i) => s + (i.forks_count || 0), 0)
);
const avgStars = computed(() =>
  items.value.length ? Math.round(totalStars.value / items.value.length) : 0
);

const topLanguages = computed(() => {
  const map = new Map();
  for (const item of items.value) {
    const l = item.language || 'Unknown';
    map.set(l, (map.get(l) || 0) + 1);
  }
  const arr = [...map.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);
  const totalCount = arr.reduce((s, x) => s + x.count, 0) || 1;
  return arr.map((x) => ({
    ...x,
    percent: Math.round((x.count / totalCount) * 100),
  }));
});

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return String(num);
};

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

// 趋势对比：将当前周期项目与上一周期榜单对比，标记排名升降/新上榜
const prevByFullName = ref(new Map());

const getTrend = (item) => {
  if (prevByFullName.value.size === 0) return null;
  const prevRank = prevByFullName.value.get(item.full_name);
  if (prevRank === undefined) {
    return { dir: 'up', arrow: '↑ 新上榜' };
  }
  if (prevRank > item.rank) {
    return { dir: 'up', arrow: `↑ ${prevRank - item.rank}` };
  }
  if (prevRank < item.rank) {
    return { dir: 'down', arrow: `↓ ${item.rank - prevRank}` };
  }
  return { dir: 'same', arrow: '—' };
};

const fetchTrending = async () => {
  loading.value = true;
  error.value = '';
  try {
    const params = {
      language: selectedLanguage.value || undefined,
      since: selectedSince.value,
      limit: 20,
    };
    const res = await api.getTrending(params);
    items.value = res.data.items || [];
    total.value = res.data.total || 0;

    // 拉取相邻更短周期的榜单用于趋势对比
    const prevSince = selectedSince.value === 'daily' ? null
      : selectedSince.value === 'weekly' ? 'daily' : 'weekly';
    if (prevSince) {
      try {
        const prevRes = await api.getTrending({
          language: selectedLanguage.value || undefined,
          since: prevSince,
          limit: 20,
        });
        const map = new Map();
        (prevRes.data.items || []).forEach((it, idx) => map.set(it.full_name, idx + 1));
        prevByFullName.value = map;
      } catch (e) {
        prevByFullName.value = new Map();
      }
    } else {
      prevByFullName.value = new Map();
    }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '获取排行榜数据失败';
    prevByFullName.value = new Map();
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

.since-tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
}

.since-tab {
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-sm);
  font-family: var(--geist-sans);
  color: var(--fg-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.since-tab:hover {
  color: var(--fg-primary);
}

.since-tab.active {
  color: var(--fg-primary);
  background: var(--bg-background);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  font-weight: var(--font-weight-medium);
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

/* Visualization Panel */
.viz-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-4);
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
}

.summary-label {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
}

.summary-value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  font-family: var(--geist-mono);
}

.lang-distribution {
  padding: var(--space-5);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  background: var(--bg-card);
}

.viz-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin-bottom: var(--space-4);
}

.lang-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.lang-bar-row {
  display: grid;
  grid-template-columns: 200px 1fr 48px;
  align-items: center;
  gap: var(--space-3);
}

.lang-bar-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.lang-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.lang-name {
  font-size: var(--font-size-sm);
  color: var(--fg-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lang-count {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  white-space: nowrap;
}

.lang-bar-track {
  height: 8px;
  border-radius: 4px;
  background: var(--bg-secondary);
  overflow: hidden;
}

.lang-bar {
  height: 100%;
  border-radius: 4px;
  transition: width var(--transition-base);
}

.lang-percent {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
  text-align: right;
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
  grid-template-columns: 70px 120px minmax(440px, 1fr) 150px 180px 120px 120px 120px 170px;
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
  grid-template-columns: 70px 120px minmax(440px, 1fr) 150px 180px 120px 120px 120px 170px;
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

.col-trend {
  display: flex;
  align-items: center;
}

.trend-badge {
  font-family: var(--geist-mono);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
}

.trend-badge.up {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.12);
}

.trend-badge.down {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.12);
}

.trend-badge.same {
  color: var(--fg-tertiary);
  background: var(--bg-secondary);
}

.trend-none {
  color: var(--fg-tertiary);
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
