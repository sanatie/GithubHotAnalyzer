<template>
  <div class="loading-state" :class="[`loading-${type}`]">
    <template v-if="type === 'spinner'">
      <div class="spinner-wrapper">
        <div class="spinner"></div>
        <p v-if="message" class="message">{{ message }}</p>
      </div>
    </template>

    <template v-else-if="type === 'text'">
      <div class="text-wrapper">
        <span class="loading-dots">
          <span></span><span></span><span></span>
        </span>
        <p v-if="message" class="message">{{ message }}</p>
      </div>
    </template>

    <template v-else-if="type === 'skeleton'">
      <div class="skeleton-wrapper">
        <div v-for="i in skeletonCount" :key="i" class="skeleton-item">
          <div class="skeleton-avatar"></div>
          <div class="skeleton-content">
            <div class="skeleton-title"></div>
            <div class="skeleton-desc"></div>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="spinner-wrapper">
        <div class="spinner"></div>
        <p v-if="message" class="message">{{ message }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'spinner',
    validator: (val) => ['spinner', 'text', 'skeleton'].includes(val)
  },
  message: {
    type: String,
    default: ''
  },
  skeletonCount: {
    type: Number,
    default: 3
  }
});
</script>

<style scoped>
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 48px 24px;
}

.spinner-wrapper,
.text-wrapper {
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.message {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.loading-dots {
  display: inline-block;
}

.loading-dots span {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin: 0 4px;
  background: #409eff;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
.loading-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.skeleton-wrapper {
  width: 100%;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-title {
  height: 16px;
  width: 60%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-desc {
  height: 12px;
  width: 80%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
