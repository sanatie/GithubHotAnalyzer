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
          @click="showDownloader = true"
        >
          下载管理器{{ tasks.length > 0 ? ` (${activeTaskCount})` : '' }}
        </button>
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
          <button class="link-btn" @click="openDownloadDialog(item)">下载</button>
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

    <!-- 下载弹窗 -->
    <div v-if="showDownloadDialog" class="modal-overlay" @click.self="closeDownloadDialog">
      <div class="modal download-modal">
        <h3 class="modal-title">下载 {{ downloadTarget?.author }}/{{ downloadTarget?.name }}</h3>
        <p v-if="probeLoading" class="download-loading">正在探测项目可下载内容...</p>

        <template v-else-if="probeInfo">
          <!-- 下载类型选择 -->
          <div class="download-types">
            <label
              v-for="opt in downloadTypeOptions"
              :key="opt.value"
              class="dt-item"
              :class="{ disabled: opt.value === 'release' && !probeInfo.has_release }"
            >
              <input
                type="radio"
                :value="opt.value"
                v-model="downloadForm.contentType"
                :disabled="opt.value === 'release' && !probeInfo.has_release"
                @change="syncFormFromType"
              />
              <span class="dt-label">{{ opt.label }}</span>
              <span v-if="opt.value === 'release' && !probeInfo.has_release" class="dt-note">(无Release)</span>
            </label>
          </div>

          <!-- 目标 URL -->
          <div class="form-field">
            <label class="form-label">下载链接</label>
            <input
              v-model="downloadForm.url"
              class="form-input"
              :placeholder="pickDownloadUrl()"
            />
          </div>

          <!-- git clone 镜像源 -->
          <div v-if="downloadForm.contentType === 'gitclone'" class="form-field">
            <label class="form-label">镜像源</label>
            <input
              v-model="downloadForm.mirror"
              class="form-input"
              placeholder="留空=直连 github.com；填 GitHub 加速镜像前缀，如 https://ghfast.top/https://github.com"
            />
            <div class="form-hint">github.com 直连被墙时可填镜像前缀，会自动拼到仓库地址上</div>
          </div>

          <!-- 保存目录 -->
          <div class="form-field">
            <label class="form-label">保存目录</label>
            <div class="dir-row">
              <input v-model="downloadForm.saveDir" class="form-input" placeholder="默认下载目录" />
              <button type="button" class="dir-browse-btn" @click="handleSelectDir">浏览</button>
            </div>
            <div class="form-hint">{{ defaultDir }}</div>
          </div>

          <!-- 保存文件名 -->
          <div class="form-field">
            <label class="form-label">文件名</label>
            <input v-model="downloadForm.filename" class="form-input" :placeholder="defaultFilename" />
          </div>
        </template>

        <div class="modal-actions">
          <button class="btn-secondary" @click="closeDownloadDialog">取消</button>
          <button
            class="btn-primary"
            :disabled="!downloadForm.contentType || probeLoading"
            @click="handleStartDownload"
          >
            开始下载
          </button>
        </div>
      </div>
    </div>

    <!-- 下载管理器面板 -->
    <div v-if="showDownloader" class="modal-overlay" @click.self="closeDownloader">
      <div class="downloader-panel">
        <div class="downloader-head">
          <h3 class="downloader-title">下载管理器</h3>
          <button class="close-x" @click="showDownloader = false">×</button>
        </div>

        <div v-if="tasks.length === 0" class="downloader-empty">
          <p>暂无下载任务</p>
        </div>

        <div v-else class="downloader-list">
          <div v-for="t in tasks" :key="t.id" class="task-card" :class="t.status">
            <div class="task-top">
              <span class="task-repo">{{ t.author }}/{{ t.repository }}</span>
              <span class="task-status">{{ statusText(t.status) }}</span>
            </div>
            <div class="task-meta">
              <span class="task-type">{{ typeText(t.content_type) }}</span>
              <span class="task-file mono">{{ t.filename }}</span>
            </div>
            <div class="task-progress-track">
              <div class="task-progress-bar" :style="{ width: t.progress + '%' }"></div>
            </div>
            <div class="task-bottom">
              <span class="task-size mono">{{ formatBytes(t.downloaded) }} / {{ formatBytes(t.total_size) }}</span>
              <span class="task-speed mono">{{ formatSpeed(t.speed) }}</span>
              <span class="task-pct mono">{{ t.progress }}%</span>
            </div>
            <div v-if="t.status === 'failed'" class="task-error">{{ t.error }}</div>
            <div class="task-actions">
              <template v-if="t.status === 'downloading' || t.status === 'pending'">
                <button class="link-btn danger" @click="handleCancel(t.id)">取消</button>
              </template>
              <template v-else-if="t.status === 'completed'">
                <button class="link-btn" @click="handleOpenDir(t.id)">打开目录</button>
                <button class="link-btn danger" @click="handleDeleteTask(t.id)">删除</button>
              </template>
              <template v-else>
                <button class="link-btn danger" @click="handleDeleteTask(t.id)">删除</button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import useCart from '../stores/cart';
import api from '../api';

const router = useRouter();
const { cartItems, cartCount, removeFromCartByIndex, clearCart } = useCart();

const selectedAuthors = ref([]);
const confirmClear = ref(false);

// ----- 下载功能状态 -----
const showDownloader = ref(false);
const showDownloadDialog = ref(false);
const downloadTarget = ref(null);
const probeLoading = ref(false);
const probeInfo = ref(null);
const defaultDir = ref('');
const tasks = ref([]);
let pollTimer = null;

const downloadForm = ref({
  contentType: 'zip',
  url: '',
  saveDir: '',
  filename: '',
  mirror: '',
});

const downloadTypeOptions = [
  { value: 'zip', label: '源码 ZIP' },
  { value: 'release', label: 'Release 文件' },
  { value: 'readme', label: 'README 文档' },
  { value: 'gitclone', label: 'git clone' },
];

const activeTaskCount = computed(() =>
  tasks.value.filter(t => t.status === 'downloading' || t.status === 'pending').length
);

const defaultFilename = computed(() => {
  if (!downloadTarget.value) return '';
  const { author, name } = downloadTarget.value;
  if (downloadForm.value.contentType === 'release') return `${name}-release`;
  if (downloadForm.value.contentType === 'readme') return `README_${name}.md`;
  return `${name}.zip`;
});

// 根据选中类型自动匹配下载 URL
function pickDownloadUrl() {
  if (!probeInfo.value) return '';
  const p = probeInfo.value;
  const c = downloadForm.value.contentType;
  if (c === 'gitclone') return p.clone_url;
  if (c === 'zip') return p.zip_url;
  if (c === 'readme') return p.readme_url;
  if (c === 'release') {
    const first = p.releases?.[0];
    return first ? first.browser_download_url : p.zip_url;
  }
  return p.zip_url;
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const n = Number(bytes);
  if (n >= 1024 * 1024 * 1024) return (n / 1024 / 1024 / 1024).toFixed(1) + ' GB';
  if (n >= 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + ' MB';
  if (n >= 1024) return (n / 1024).toFixed(1) + ' KB';
  return n + ' B';
}

function formatSpeed(bytes) {
  if (!bytes) return '';
  return formatBytes(bytes) + '/s';
}

function statusText(s) {
  return { pending: '等待中', downloading: '下载中', completed: '已完成', failed: '失败', cancelled: '已取消' }[s] || s;
}

function typeText(t) {
  return { zip: '源码 ZIP', release: 'Release', readme: 'README', gitclone: 'git clone' }[t] || t;
}

// ----- 下载弹窗 -----
async function openDownloadDialog(item) {
  downloadTarget.value = item;
  showDownloadDialog.value = true;
  showDownloader.value = false;
  probeLoading.value = true;
  probeInfo.value = null;
  downloadForm.value = { contentType: 'zip', url: '', saveDir: defaultDir.value, filename: '', mirror: '' };
  try {
    const res = await api.probeProject(item.author, item.name);
    probeInfo.value = res.data;
    downloadForm.value.url = res.data.zip_url;
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '探测项目内容失败');
    probeInfo.value = { author: item.author, repository: item.name, zip_url: `https://github.com/${item.author}/${item.name}/archive/refs/heads/main.zip` };
    downloadForm.value.url = `https://github.com/${item.author}/${item.name}/archive/refs/heads/main.zip`;
  } finally {
    probeLoading.value = false;
  }
}

function closeDownloadDialog() {
  showDownloadDialog.value = false;
  downloadTarget.value = null;
  probeInfo.value = null;
}

function closeDownloader() {
  showDownloader.value = false;
}

// 切换下载类型时自动填 URL 和文件名
function syncFormFromType() {
  downloadForm.value.url = pickDownloadUrl();
  downloadForm.value.filename = '';
}

async function handleStartDownload() {
  const item = downloadTarget.value;
  if (!item) return;
  const data = {
    author: item.author,
    repository: item.name,
    content_type: downloadForm.value.contentType,
    save_dir: downloadForm.value.saveDir || '',
    url: downloadForm.value.url || pickDownloadUrl(),
    filename: downloadForm.value.filename || defaultFilename.value,
    mirror: downloadForm.value.mirror || '',
  };
  if (!data.url) {
    ElMessage.warning('请填写下载链接');
    return;
  }
  try {
    await api.createDownload(data);
    ElMessage.success('已创建下载任务');
    closeDownloadDialog();
    showDownloader.value = true;
    loadTasks();
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建下载任务失败');
  }
}

// ----- 下载管理器 -----
async function loadTasks() {
  try {
    const res = await api.getDownloadTasks({ page: 1, page_size: 50 });
    tasks.value = res.data.items || [];
  } catch (e) {
    // 轮询失败静默
  }
}

async function handleCancel(id) {
  try {
    await api.cancelDownload(id);
    ElMessage.info('已取消任务');
    loadTasks();
  } catch (e) {
    ElMessage.error('取消失败');
  }
}

async function handleDeleteTask(id) {
  try {
    await api.deleteDownload(id);
    ElMessage.success('已删除任务');
    loadTasks();
  } catch (e) {
    ElMessage.error('删除失败');
  }
}

async function handleOpenDir(id) {
  try {
    await api.openDownloadDir(id);
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '打开目录失败');
  }
}

async function handleSelectDir() {
  const electronDialog = window.electronAPI?.dialog;
  if (!electronDialog) {
    ElMessage.info('请在桌面端（Electron）中使用——浏览器出于安全限制无法打开系统目录选择器');
    return;
  }
  try {
    const dir = await electronDialog.selectDirectory();
    if (dir) downloadForm.saveDir = dir;
  } catch (e) {
    ElMessage.error('选择目录失败');
  }
}

// ----- 轮询 -----
function startPolling() {
  stopPolling();
  pollTimer = setInterval(loadTasks, 1000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

// ----- 原有逻辑 -----
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

onMounted(async () => {
  try {
    const res = await api.getDefaultDownloadDir();
    defaultDir.value = res.data.default_dir || '';
  } catch (e) {
    defaultDir.value = '';
  }
  loadTasks();
  startPolling();
});

onBeforeUnmount(() => {
  stopPolling();
});
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

/* ---------- 下载相关样式 ---------- */
.download-modal {
  max-width: 480px;
}

.download-loading {
  margin: var(--space-4) 0;
  font-size: var(--font-size-sm);
  color: var(--fg-secondary);
}

.download-types {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin: var(--space-3) 0;
}

.dt-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  color: var(--fg-primary);
  cursor: pointer;
  transition: border-color var(--transition-fast);
}

.dt-item:hover:not(.disabled) {
  border-color: var(--fg-primary);
}

.dt-item.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.dt-item input {
  accent-color: var(--fg-primary);
}

.dt-label {
  font-weight: var(--font-weight-medium);
}

.dt-note {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  margin-bottom: var(--space-4);
}

.form-label {
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
}

.form-input {
  height: 36px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-background);
  color: var(--fg-primary);
  font-size: var(--font-size-sm);
  font-family: var(--geist-mono);
}

.form-input:focus {
  outline: none;
  border-color: var(--fg-primary);
}

.form-hint {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
  word-break: break-all;
}

.downloader-panel {
  position: relative;
  width: 90%;
  max-width: 560px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-background);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  padding: var(--space-5);
  overflow: hidden;
}

.downloader-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.downloader-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin: 0;
}

.close-x {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--fg-secondary);
  font-size: var(--font-size-lg);
  line-height: 1;
  cursor: pointer;
}

.close-x:hover {
  background: var(--bg-hover);
  color: var(--fg-primary);
}

.downloader-empty {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--fg-tertiary);
  font-size: var(--font-size-sm);
}

.downloader-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  overflow-y: auto;
}

.task-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--border-secondary);
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
}

.task-card.downloading {
  border-color: var(--fg-primary);
}

.task-card.failed {
  border-color: var(--error-light);
}

.task-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.task-repo {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  word-break: break-all;
}

.task-status {
  flex-shrink: 0;
  font-size: var(--font-size-xs);
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
}

.task-card.downloading .task-status {
  color: var(--fg-primary);
  background: rgba(0, 122, 255, 0.12);
}

.task-card.completed .task-status {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.12);
}

.task-card.failed .task-status {
  color: var(--error-light);
  background: rgba(220, 38, 38, 0.12);
}

.task-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.task-type {
  font-size: var(--font-size-xs);
  color: var(--fg-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xs);
  padding: 1px var(--space-2);
}

.task-file {
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
  word-break: break-all;
}

.task-progress-track {
  height: 6px;
  border-radius: 3px;
  background: var(--bg-background);
  overflow: hidden;
}

.task-progress-bar {
  height: 100%;
  border-radius: 3px;
  background: var(--fg-primary);
  transition: width 0.3s ease;
}

.task-card.failed .task-progress-bar {
  background: var(--error-light);
}

.task-bottom {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
}

.task-pct {
  margin-left: auto;
}

.task-error {
  font-size: var(--font-size-xs);
  color: var(--error-light);
  word-break: break-all;
}

.task-actions {
  display: flex;
  gap: var(--space-3);
}

.mono {
  font-family: var(--geist-mono);
}

.dir-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.dir-browse-btn {
  flex: 0 0 auto;
  padding: 0 14px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-secondary, var(--bg));
  color: var(--text-primary, inherit);
  font-size: var(--font-size-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 0.15s, color 0.15s;
}

.dir-browse-btn:hover {
  border-color: var(--primary-light);
  color: var(--primary-light);
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