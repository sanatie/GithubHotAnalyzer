<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-inner">
        <div class="brand" @click="$router.push('/')">
          <span class="brand-text">分析器</span>
        </div>
        <nav class="nav">
          <div class="nav-section">
            <div class="nav-label">概览</div>
            <router-link to="/" class="nav-item" exact-active-class="active">
              <span class="nav-dot" />
              <span class="nav-text">首页</span>
            </router-link>
            <router-link to="/trending" class="nav-item" active-class="active">
              <span class="nav-dot" />
              <span class="nav-text">排行榜</span>
            </router-link>
            <router-link to="/chat" class="nav-item" active-class="active">
              <span class="nav-dot" />
              <span class="nav-text">AI 推荐</span>
            </router-link>
            <router-link to="/cart" class="nav-item" active-class="active">
              <span class="nav-dot" />
              <span class="nav-text">推荐购物车</span>
              <span v-if="cartCount > 0" class="nav-badge">{{ cartCount }}</span>
            </router-link>
          </div>
          <div class="nav-section">
            <div class="nav-label">仓库</div>
            <router-link to="/history" class="nav-item" active-class="active">
              <span class="nav-dot" />
              <span class="nav-text">历史记录</span>
            </router-link>
            <router-link to="/favorites" class="nav-item" active-class="active">
              <span class="nav-dot" />
              <span class="nav-text">我的收藏</span>
            </router-link>
          </div>
          <div class="nav-section">
            <div class="nav-label">系统</div>
            <router-link to="/settings" class="nav-item" active-class="active">
              <span class="nav-dot" />
              <span class="nav-text">设置</span>
            </router-link>
          </div>
        </nav>
      </div>
      <div class="sidebar-footer">
        <div class="footer-item">
          <span class="footer-text">v1.0.0</span>
        </div>
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="topbar-left drag-region">
          <span class="breadcrumb">{{ currentPageTitle }}</span>
        </div>
        <div class="topbar-right">
          <div class="window-controls" v-if="isElectron">
            <button class="win-btn minimize" @click="minimizeWindow" title="最小化">
              <svg width="12" height="12" viewBox="0 0 12 12">
                <rect x="2" y="5.5" width="8" height="1" fill="currentColor" />
              </svg>
            </button>
            <button class="win-btn maximize" @click="toggleMaximize" :title="isMaximized ? '还原' : '最大化'">
              <svg v-if="!isMaximized" width="12" height="12" viewBox="0 0 12 12">
                <rect x="2.5" y="2.5" width="7" height="7" fill="none" stroke="currentColor" stroke-width="1" />
              </svg>
              <svg v-else width="12" height="12" viewBox="0 0 12 12">
                <path d="M3 2.5h4.5a.5.5 0 0 1 .5.5V7.5M9 5v4.5a.5.5 0 0 1-.5.5H4" fill="none" stroke="currentColor" stroke-width="1" />
              </svg>
            </button>
            <button class="win-btn close" @click="closeWindow" title="关闭">
              <svg width="12" height="12" viewBox="0 0 12 12">
                <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
              </svg>
            </button>
          </div>
        </div>
      </header>
      <div class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import useCart from '../stores/cart';

const route = useRoute();
const { cartCount } = useCart();

const isElectron = ref(false);
const isMaximized = ref(false);

const titleMap = {
  '/': '首页',
  '/trending': '排行榜',
  '/chat': 'AI 推荐',
  '/cart': '推荐购物车',
  '/history': '历史记录',
  '/favorites': '我的收藏',
  '/settings': '设置',
  '/analyze': '分析'
};

const currentPageTitle = computed(() => {
  return titleMap[route.path] || '首页';
});

const minimizeWindow = () => {
  if (window.electronAPI?.window) {
    window.electronAPI.window.minimize();
  }
};

const toggleMaximize = () => {
  if (window.electronAPI?.window) {
    window.electronAPI.window.toggleMaximize();
    setTimeout(async () => {
      if (window.electronAPI?.window) {
        isMaximized.value = await window.electronAPI.window.isMaximized();
      }
    }, 100);
  }
};

const closeWindow = () => {
  if (window.electronAPI?.window) {
    window.electronAPI.window.close();
  }
};

const updateMaximizedState = async () => {
  if (window.electronAPI?.window) {
    isMaximized.value = await window.electronAPI.window.isMaximized();
  }
};

onMounted(() => {
  isElectron.value = !!window.electronAPI;
  if (isElectron.value) {
    updateMaximizedState();
  }
});
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  background: var(--bg-background);
}

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  border-right: 1px solid var(--border-default);
  background: var(--bg-canvas);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-inner {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
}

.brand {
  padding: var(--space-2) var(--space-3) var(--space-6);
  cursor: pointer;
  user-select: none;
  -webkit-app-region: drag;
}

.brand-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  letter-spacing: -0.01em;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--fg-tertiary);
  padding: var(--space-2) var(--space-3);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
  color: var(--fg-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--fg-primary);
  opacity: 1;
}

.nav-item.active {
  background: var(--bg-secondary);
  color: var(--fg-primary);
}

.nav-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--border-strong);
  flex-shrink: 0;
  margin-left: 2px;
  margin-right: 6px;
}

.nav-item.active .nav-dot {
  background: var(--fg-primary);
}

.nav-text {
  flex: 1;
}

.nav-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--fg-primary);
  color: var(--bg-background);
  font-size: var(--font-size-xs);
  font-family: var(--geist-mono);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.sidebar-footer {
  border-top: 1px solid var(--border-default);
  padding: var(--space-3);
}

.footer-item {
  padding: var(--space-1) var(--space-3);
}

.footer-text {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
}

.main {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: var(--header-height);
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-background);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.breadcrumb {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--fg-primary);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.drag-region {
  -webkit-app-region: drag;
  flex: 1;
}

.window-controls {
  display: flex;
  align-items: center;
  height: 100%;
  -webkit-app-region: no-drag;
}

.win-btn {
  width: 46px;
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--fg-secondary);
  cursor: pointer;
  transition: background-color var(--transition-fast);
  padding: 0;
}

.win-btn:hover {
  background: var(--bg-hover);
  color: var(--fg-primary);
}

.win-btn.close:hover {
  background: #e7000b;
  color: #fff;
}

.content {
  flex: 1;
  padding: var(--space-6);
  min-width: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-base);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }

  .main {
    margin-left: 0;
  }

  .content {
    padding: var(--space-4);
  }
}
</style>
