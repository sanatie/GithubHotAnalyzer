<template>
  <div class="cart">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">推荐购物车</h1>
        <p class="page-desc">共 {{ cartCount }} 个项目</p>
      </div>
      <div class="header-right">
        <button
          class="btn-secondary"
          :disabled="selectedAuthors.length === 0"
          @click="handleBatchCollection"
        >
          批量收藏 {{ selectedAuthors.length > 0 ? `(${selectedAuthors.length})` : '' }}
        </button>
        <button class="btn-danger" :disabled="cartCount === 0" @click="confirmClear = true">
          清空购物车
        </button>
      </div>
    </div>

    <div v-if="cartCount === 0" class="empty-state">
      <p class="empty-text">购物车为空，去添加一些项目吧</p>
      <div class="empty-actions">
        <button class="btn-primary" @click="$router.push('/chat')">去 AI 推荐</button>
        <button class="btn-secondary" @click="$router.push('/trending')">去排行榜</button>
      </div>
    </div>

    <div v-else class="item-list">
      <div v-for="(item, idx) in cartItems" :key="`${item.author}/${item.name}`" class="item-card">
        <label class="select-box">
          <input
            type="checkbox"
            :checked="selectedAuthors.includes(`${item.author}/${item.name}`)"
            @change="toggleSelect(item)"
          />
        </label>
        <span class="rank">{{ idx + 1 }}</span>
        <div class="item-body">
          <div class="item-name">
            <a :href="item.github_url" target="_blank" rel="noopener" class="repo-link">
              {{ item.author }}/{{ item.name }}
            </a>
            <span v-if="item.language" class="lang-tag">{{ item.language }}</span>
            <span v-if="item.stars" class="stars-text">{{ item.stars }}</span>
          </div>
          <p v-if="item.description" class="item-desc">{{ item.description }}</p>
        </div>
        <div class="item-actions">
          <button class="link-btn" @click="handleAnalyze(item)">分析</button>
          <button class="link-btn" @click="handleCopy(item)">复制</button>
          <button class="link-btn danger" @click="handleRemove(idx)">移除</button>
        </div>
      </div>
    </div>

    <div v-if="confirmClear" class="modal-overlay" @click.self="confirmClear = false">
      <div class="modal">
        <h3 class="modal-title">清空购物车</h3>
        <p class="modal-desc">将清空全部 {{ cartCount }} 个项目，不可恢复。</p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="confirmClear = false">取消</button>
          <button class="btn-danger" @click="handleClear">确认清空</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import useCart from '../stores/cart';
import api from '../api';

const router = useRouter();
const { cartItems, cartCount, removeFromCartByIndex, clearCart } = useCart();

const selectedAuthors = ref([]);
const confirmClear = ref(false);

function toggleSelect(item) {
  const key = `${item.author}/${item.name}`;
  const idx = selectedAuthors.value.indexOf(key);
  if (idx > -1) {
    selectedAuthors.value.splice(idx, 1);
  } else {
    selectedAuthors.value.push(key);
  }
}

function handleRemove(idx) {
  const item = cartItems.value[idx];
  if (!item) return;
  const key = `${item.author}/${item.name}`;
  removeFromCartByIndex(idx);
  const si = selectedAuthors.value.indexOf(key);
  if (si > -1) selectedAuthors.value.splice(si, 1);
  ElMessage.success('已移除');
}

function handleClear() {
  clearCart();
  selectedAuthors.value = [];
  confirmClear.value = false;
  ElMessage.success('购物车已清空');
}

async function handleCopy(item) {
  try {
    await navigator.clipboard.writeText(`${item.author}/${item.name}`);
    ElMessage.success('已复制项目名');
  } catch (e) {
    ElMessage.error('复制失败');
  }
}

function handleAnalyze(item) {
  router.push({
    name: 'Home',
    query: { repo: `${item.author}/${item.name}` },
  });
}

async function handleBatchCollection() {
  if (selectedAuthors.value.length === 0) return;
  let successCount = 0;
  let failCount = 0;
  for (const author of selectedAuthors.value) {
    const item = cartItems.value.find(i => `${i.author}/${i.name}` === author);
    if (!item) continue;
    try {
      // 先查找本地仓库，不存在则直接以完整信息收藏
      await api.addFavorite({
        repository_id: null,
        name: item.name,
        author: item.author,
        html_url: item.github_url,
        description: item.description,
        language: item.language,
        stargazers_count: 0,
        note: '来自推荐购物车',
        tags: [item.language, '购物车'],
      });
      successCount++;
    } catch (e) {
      failCount++;
    }
  }
  const msg = failCount > 0
    ? `收藏成功 ${successCount} 个，失败 ${failCount} 个`
    : `已收藏 ${successCount} 个项目`;
  if (failCount > 0) {
    ElMessage.warning(msg);
  } else {
    ElMessage.success(msg);
  }
}
</script>

<style scoped>
.cart {
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

.header-right {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
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

.btn-secondary:disabled,
.btn-danger:disabled {
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

.empty-state {
  text-align: center;
  padding: var(--space-10) 0;
}

.empty-text {
  font-size: var(--font-size-base);
  color: var(--fg-tertiary);
  margin: 0 0 var(--space-4) 0;
}

.empty-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  padding: var(--space-4);
  background: var(--bg-background);
}

.item-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius);
  background: var(--bg-secondary);
}

.select-box {
  display: flex;
  align-items: center;
  margin-top: 4px;
  cursor: pointer;
}

.select-box input {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--fg-primary);
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
  min-width: 0;
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
  word-break: break-all;
}

.repo-link:hover {
  text-decoration: underline;
}

.lang-tag {
  display: inline-block;
  padding: 2px var(--space-2);
  background: var(--bg-background);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
}

.stars-text {
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  font-family: var(--geist-mono);
}

.item-desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-actions {
  flex-shrink: 0;
  display: flex;
  gap: var(--space-2);
  margin-top: 2px;
}

.link-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color var(--transition-fast);
}

.link-btn:hover {
  color: var(--fg-primary);
}

.link-btn.danger:hover {
  color: var(--error-light);
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

  .item-actions {
    flex-direction: column;
  }
}
</style>