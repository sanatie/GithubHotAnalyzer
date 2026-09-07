<template>
  <div class="settings">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">设置</h1>
        <p class="page-desc">配置大模型 API 参数</p>
      </div>
    </div>

    <div class="settings-card">
      <div v-if="loading" class="loading-row">
        <div class="spinner-sm" />
        <span>加载中...</span>
      </div>

      <div v-else class="form">
        <div class="form-item">
          <label class="form-label">API 地址</label>
          <input
            v-model="form.api_base_url"
            class="form-input"
            type="text"
            placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1"
          />
        </div>

        <div class="form-item">
          <label class="form-label">模型名称</label>
          <input
            v-model="form.model"
            class="form-input"
            type="text"
            placeholder="qwen-plus"
          />
        </div>

        <div class="form-item">
          <label class="form-label">API Key</label>
          <div class="input-with-btn">
            <input
              v-model="form.api_key"
              class="form-input"
              :type="showApiKey ? 'text' : 'password'"
              :placeholder="currentKeyMasked || '请输入 API Key'"
            />
            <button class="btn-ghost" type="button" @click="showApiKey = !showApiKey">
              {{ showApiKey ? '隐藏' : '显示' }}
            </button>
          </div>
          <p v-if="currentKeyMasked" class="form-hint">当前配置: {{ currentKeyMasked }}</p>
        </div>

        <!-- Collapsible Model Section -->
        <div class="model-section">
          <div class="model-header" @click="modelExpanded = !modelExpanded">
            <div class="model-header-left">
              <span class="section-label">主流大模型</span>
              <span v-if="selectedModelData" class="selected-tag">
                <span
                  class="model-logo-sm"
                  :style="{ background: selectedModelData.logoBg }"
                  v-html="selectedModelData.logo"
                />
                {{ selectedModelData.name }}
              </span>
            </div>
            <div class="model-header-right">
              <span v-if="selectedModelData" class="selected-url">{{ selectedModelData.model }}</span>
              <svg
                class="chevron"
                :class="{ expanded: modelExpanded }"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </div>
          </div>

          <!-- Summary bar (always visible) -->
          <div v-if="selectedModelData" class="summary-bar">
            <span
              class="model-logo"
              :style="{ background: selectedModelData.logoBg }"
              v-html="selectedModelData.logo"
            />
            <div class="summary-item">
              <span class="summary-label">厂商</span>
              <span class="summary-value">{{ selectedModelData.name }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">模型</span>
              <span class="summary-value mono">{{ selectedModelData.model }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">分类</span>
              <span class="summary-value">{{ selectedModelData.vendor === 'domestic' ? '国内' : '国外' }}</span>
            </div>
            <a
              :href="selectedModelData.keyUrl"
              target="_blank"
              rel="noopener"
              class="summary-link"
              @click.stop
            >
              获取密钥
            </a>
          </div>

          <!-- Collapsible content -->
          <transition name="collapse">
            <div v-if="modelExpanded" class="model-grid-wrap">
              <div class="model-grid">
                <div
                  v-for="m in models"
                  :key="m.key"
                  class="model-card"
                  :class="[m.vendor, { active: selectedModel === m.key }]"
                  @click="applyModel(m)"
                >
                  <div class="model-card-header">
                    <div class="model-card-title">
                      <span
                        class="model-logo"
                        :style="{ background: m.logoBg }"
                        v-html="m.logo"
                      />
                      <span class="model-name">{{ m.name }}</span>
                    </div>
                    <span class="vendor-tag" :class="m.vendor">
                      {{ m.vendor === 'domestic' ? '国内' : '国外' }}
                    </span>
                  </div>
                  <div class="model-card-desc">{{ m.model }}</div>
                  <div class="model-card-footer">
                    <a
                      :href="m.keyUrl"
                      target="_blank"
                      rel="noopener"
                      class="model-link"
                      @click.stop
                    >
                      获取密钥
                    </a>
                    <span
                      v-if="testResult && selectedModel === m.key"
                      class="status-dot"
                      :class="testResult.success ? 'ok' : 'fail'"
                    />
                  </div>
                </div>
              </div>
            </div>
          </transition>
        </div>

        <!-- Connection Test -->
        <div class="test-section">
          <div class="test-row">
            <button
              class="btn-test"
              :disabled="testing"
              @click="handleTest"
            >
              <span v-if="testing" class="test-spinner" />
              {{ testing ? '测试中...' : '测试连接' }}
            </button>
            <div v-if="testResult" class="test-result" :class="testResult.success ? 'success' : 'fail'">
              <div class="test-result-icon">
                <svg v-if="testResult.success" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="6" y1="6" x2="18" y2="18" stroke-linecap="round" />
                  <line x1="18" y1="6" x2="6" y2="18" stroke-linecap="round" />
                </svg>
              </div>
              <span class="test-result-text">{{ testResult.message }}</span>
              <span v-if="testResult.latency_ms" class="test-latency">{{ testResult.latency_ms }}ms</span>
            </div>
          </div>
        </div>

        <!-- Save -->
        <div class="form-actions">
          <button class="btn-primary" :disabled="saving" @click="handleSave">
            {{ saving ? '保存中...' : '保存设置' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api';
import deepseekLogo from '../assets/deepseek.webp';
import kimiLogo from '../assets/kimi.webp';
import zhipuLogo from '../assets/zhipu.webp';

const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const showApiKey = ref(false);
const currentKeyMasked = ref('');
const selectedModel = ref('');
const testResult = ref(null);
const modelExpanded = ref(false);

const form = ref({
  api_key: '',
  api_base_url: '',
  model: ''
});

const models = [
  {
    key: 'qwen',
    name: '通义千问',
    vendor: 'domestic',
    logoBg: '#FF6A00',
    logo: '<svg viewBox="0 0 24 24" fill="#fff"><path d="M3.996 4.517h5.291L8.01 6.324 4.153 7.506a1.668 1.668 0 0 0-1.165 1.601v5.786a1.668 1.668 0 0 0 1.165 1.6l3.857 1.183 1.277 1.807H3.996A3.996 3.996 0 0 1 0 15.487V8.513a3.996 3.996 0 0 1 3.996-3.996m16.008 0h-5.291l1.277 1.807 3.857 1.182c.715.227 1.17.889 1.165 1.601v5.786a1.668 1.668 0 0 1-1.165 1.6l-3.857 1.183-1.277 1.807h5.291A3.996 3.996 0 0 0 24 15.487V8.513a3.996 3.996 0 0 0-3.996-3.996m-4.007 8.345H8.002v-1.804h7.995Z"/></svg>',
    api_base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-plus',
    keyUrl: 'https://bailian.console.aliyun.com/cn-beijing/?source_channel=key_github&tab=app#/api-key',
  },
  {
    key: 'deepseek',
    name: 'DeepSeek',
    vendor: 'domestic',
    logoBg: '#ffffff',
    logo: `<img src="${deepseekLogo}" alt="DeepSeek" />`,
    api_base_url: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    keyUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    key: 'openai',
    name: 'OpenAI',
    vendor: 'international',
    logoBg: '#0d0d0d',
    logo: '<svg viewBox="0 0 24 24" fill="#fff"><path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/></svg>',
    api_base_url: 'https://api.openai.com/v1',
    model: 'gpt-3.5-turbo',
    keyUrl: 'https://platform.openai.com/api-keys',
  },
  {
    key: 'zhipu',
    name: '智谱 GLM',
    vendor: 'domestic',
    logoBg: '#ffffff',
    logo: `<img src="${zhipuLogo}" alt="智谱GLM" />`,
    api_base_url: 'https://open.bigmodel.cn/api/paas/v4',
    model: 'glm-4',
    keyUrl: 'https://open.bigmodel.cn/usercenter/apikeys',
  },
  {
    key: 'wenxin',
    name: '文心一言',
    vendor: 'domestic',
    logoBg: '#2932e1',
    logo: '<svg viewBox="0 0 24 24" fill="#fff"><path d="M9.154 0C7.71 0 6.54 1.658 6.54 3.707c0 2.051 1.171 3.71 2.615 3.71 1.446 0 2.614-1.659 2.614-3.71C11.768 1.658 10.6 0 9.154 0zm7.025.594C14.86.58 13.347 2.589 13.2 3.927c-.187 1.745.25 3.487 2.179 3.735 1.933.25 3.175-1.806 3.422-3.364.252-1.555-.995-3.364-2.362-3.674a1.218 1.218 0 0 0-.261-.03zM3.582 5.535a2.811 2.811 0 0 0-.156.008c-2.118.19-2.428 3.24-2.428 3.24-.287 1.41.686 4.425 3.297 3.864 2.617-.561 2.262-3.68 2.183-4.362-.125-1.018-1.292-2.773-2.896-2.75zm16.534 1.753c-2.308 0-2.617 2.119-2.617 3.616 0 1.43.121 3.425 2.988 3.362 2.867-.063 2.553-3.238 2.553-3.988 0-.745-.62-2.99-2.924-2.99zm-8.264 2.478c-1.424.014-2.708.925-3.323 1.947-1.118 1.868-2.863 3.05-3.112 3.363-.25.309-3.61 2.116-2.864 5.42.746 3.301 3.365 3.237 3.365 3.237s1.93.19 4.171-.31c2.24-.495 4.17.123 4.17.123s5.233 1.748 6.665-1.616c1.43-3.364-.808-5.109-.808-5.109s-2.99-2.306-4.736-4.798c-1.072-1.665-2.348-2.268-3.528-2.257zm-2.234 3.84l1.542.024v8.197H7.758c-1.47-.291-2.055-1.292-2.13-1.462-.072-.173-.488-.976-.268-2.343.635-2.049 2.447-2.196 2.447-2.196h1.81zm3.964 2.39v3.881c.096.413.612.488.612.488h1.614v-4.343h1.689v5.782h-3.915c-1.517-.39-1.59-1.465-1.59-1.465v-4.317zm-5.458 1.147c-.66.197-.978.708-1.05.928-.076.22-.247.78-.1 1.269.294 1.095 1.248 1.144 1.248 1.144h1.37v-3.34z"/></svg>',
    api_base_url: 'https://qianfan.basedata.com/v2',
    model: 'ernie-4.0',
    keyUrl: 'https://console.bce.baidu.com/qianfan',
  },
  {
    key: 'kimi',
    name: 'Kimi',
    vendor: 'domestic',
    logoBg: '#1a1a1a',
    logo: `<img src="${kimiLogo}" alt="Kimi" />`,
    api_base_url: 'https://api.moonshot.cn/v1',
    model: 'moonshot-v1-8k',
    keyUrl: 'https://platform.moonshot.cn/console/api-keys',
  },
  {
    key: 'xinghuo',
    name: '讯飞星火',
    vendor: 'domestic',
    logoBg: '#0066cc',
    logo: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3z" fill="#fff"/><circle cx="12" cy="10" r="1" fill="#0066cc"/></svg>',
    api_base_url: 'https://spark-api.xf-yun.com/v1',
    model: 'generalv3',
    keyUrl: 'https://console.xfyun.cn/services/bm4',
  },
  {
    key: 'hunyuan',
    name: '腾讯混元',
    vendor: 'domestic',
    logoBg: '#12b7f5',
    logo: '<svg viewBox="0 0 24 24" fill="#fff"><path d="M21.395 15.035a40 40 0 0 0-.803-2.264l-1.079-2.695c.001-.032.014-.562.014-.836C19.526 4.632 17.351 0 12 0S4.474 4.632 4.474 9.241c0 .274.013.804.014.836l-1.08 2.695a39 39 0 0 0-.802 2.264c-1.021 3.283-.69 4.643-.438 4.673.54.065 2.103-2.472 2.103-2.472 0 1.469.756 3.387 2.394 4.771-.612.188-1.363.479-1.845.835-.434.32-.379.646-.301.778.343.578 5.883.369 7.482.189 1.6.18 7.14.389 7.483-.189.078-.132.132-.458-.301-.778-.483-.356-1.233-.646-1.846-.836 1.637-1.384 2.393-3.302 2.393-4.771 0 0 1.563 2.537 2.103 2.472.251-.03.581-1.39-.438-4.673"/></svg>',
    api_base_url: 'https://api.hunyuan.cloud.tencent.com/v1',
    model: 'hunyuan-pro',
    keyUrl: 'https://console.cloud.tencent.com/hunyuan/api-key',
  },
  {
    key: 'doubao',
    name: '字节豆包',
    vendor: 'domestic',
    logoBg: '#000000',
    logo: '<svg viewBox="0 0 24 24" fill="#fff"><path d="M19.8772 1.4685L24 2.5326v18.9426l-4.1228 1.0563V1.4685zm-13.3481 9.428l4.115 1.0641v8.9786l-4.115 1.0642v-11.107zM0 2.572l4.115 1.0642v16.7354L0 21.428V2.572zm17.4553 5.6205v11.107l-4.1228-1.0642V9.2568l4.1228-1.0642z"/></svg>',
    api_base_url: 'https://ark.cn-beijing.volces.com/api/v3',
    model: 'doubao-pro-4k',
    keyUrl: 'https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey',
  },
];

const selectedModelData = computed(() => {
  return models.find(m => m.key === selectedModel.value) || null;
});

function detectModelByConfig(baseUrl, modelName) {
  for (const m of models) {
    if (m.api_base_url === baseUrl && m.model === modelName) {
      return m.key;
    }
  }
  return '';
}

async function loadConfig() {
  loading.value = true;
  try {
    const res = await api.getAIConfig();
    currentKeyMasked.value = res.api_key_masked;
    form.value.api_base_url = res.api_base_url;
    form.value.model = res.model;
    selectedModel.value = detectModelByConfig(res.api_base_url, res.model);
  } catch (e) {
    ElMessage.error('加载配置失败');
  } finally {
    loading.value = false;
  }
}

function applyModel(m) {
  form.value.api_base_url = m.api_base_url;
  form.value.model = m.model;
  selectedModel.value = m.key;
  testResult.value = null;
  modelExpanded.value = false;
}

async function handleSave() {
  if (!form.value.api_key.trim()) {
    ElMessage.warning('请输入 API Key');
    return;
  }
  if (!form.value.api_base_url.trim()) {
    ElMessage.warning('请输入 API 地址');
    return;
  }
  if (!form.value.model.trim()) {
    ElMessage.warning('请输入模型名称');
    return;
  }

  saving.value = true;
  try {
    const res = await api.updateAIConfig({
      api_key: form.value.api_key.trim(),
      api_base_url: form.value.api_base_url.trim(),
      model: form.value.model.trim()
    });
    currentKeyMasked.value = res.api_key_masked;
    form.value.api_key = '';
    ElMessage.success('设置保存成功');
  } catch (e) {
    ElMessage.error('保存失败，请重试');
  } finally {
    saving.value = false;
  }
}

async function handleTest() {
  if (!form.value) return;
  const apiKey = (form.value.api_key || '').trim();
  const baseUrl = (form.value.api_base_url || '').trim();
  const model = (form.value.model || '').trim();

  if (!baseUrl) {
    ElMessage.warning('请先填写 API 地址');
    return;
  }
  if (!model) {
    ElMessage.warning('请先填写模型名称');
    return;
  }

  let keyToTest = apiKey;
  if (!keyToTest) {
    if (!currentKeyMasked.value) {
      ElMessage.warning('请先输入 API Key');
      return;
    }
    keyToTest = 'use_saved';
  }

  testing.value = true;
  testResult.value = null;

  try {
    const res = await api.testAIConnection({
      api_key: keyToTest,
      api_base_url: baseUrl,
      model: model,
    });
    testResult.value = res;
  } catch (e) {
    testResult.value = {
      success: false,
      message: e.response?.data?.detail || e.message || '连接测试请求失败',
      latency_ms: 0,
    };
  } finally {
    testing.value = false;
  }
}

onMounted(() => {
  loadConfig();
});
</script>

<style scoped>
.settings {
  max-width: 720px;
}

.page-header {
  margin-bottom: var(--space-6);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.page-desc {
  font-size: var(--font-size-sm);
  color: var(--fg-tertiary);
  margin: 0;
}

.settings-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  padding: var(--space-6);
}

.loading-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8) 0;
  color: var(--fg-tertiary);
  font-size: var(--font-size-sm);
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-strong);
  border-top-color: var(--fg-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--fg-primary);
}

.form-input {
  height: 40px;
  padding: 0 var(--space-3);
  background: var(--bg-background);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  color: var(--fg-primary);
  font-size: var(--font-size-sm);
  font-family: var(--geist-mono);
  outline: none;
  transition: border-color var(--transition-fast);
}

.form-input:focus {
  border-color: var(--fg-primary);
}

.form-input::placeholder {
  color: var(--fg-tertiary);
}

.input-with-btn {
  display: flex;
  gap: var(--space-2);
}

.input-with-btn .form-input {
  flex: 1;
}

.btn-ghost {
  height: 40px;
  padding: 0 var(--space-3);
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  color: var(--fg-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-ghost:hover {
  background: var(--bg-hover);
  color: var(--fg-primary);
}

.form-hint {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  margin: 0;
  font-family: var(--geist-mono);
}

/* Model Section */
.model-section {
  padding-top: var(--space-2);
  border-top: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.model-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: var(--space-2) 0;
  user-select: none;
  transition: opacity var(--transition-fast);
}

.model-header:hover {
  opacity: 0.7;
}

.model-header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.model-header-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.section-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--fg-primary);
}

.selected-tag {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: var(--fg-secondary);
}

.selected-url {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
}

.chevron {
  color: var(--fg-tertiary);
  transition: transform 0.25s ease;
}

.chevron.expanded {
  transform: rotate(180deg);
}

/* Model logo */
.model-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  overflow: hidden;
}

.model-logo svg {
  width: 18px;
  height: 18px;
}

.model-logo img {
  width: 18px;
  height: 18px;
  object-fit: contain;
  display: block;
}

.model-logo-sm {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  flex-shrink: 0;
  overflow: hidden;
}

.model-logo-sm svg {
  width: 14px;
  height: 14px;
}

.model-logo-sm img {
  width: 14px;
  height: 14px;
  object-fit: contain;
  display: block;
}

/* Vendor dot removed, replaced by model-logo */

/* Summary bar */
.summary-bar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-background);
  border-radius: var(--radius);
  border-left: 3px solid var(--border-strong);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-label {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  line-height: 1;
}

.summary-value {
  font-size: var(--font-size-sm);
  color: var(--fg-primary);
  font-weight: var(--font-weight-medium);
  line-height: 1.2;
}

.summary-value.mono {
  font-family: var(--geist-mono);
  font-size: var(--font-size-xs);
}

.summary-link {
  margin-left: auto;
  font-size: var(--font-size-xs);
  color: var(--accent-blue);
  text-decoration: none;
  white-space: nowrap;
}

.summary-link:hover {
  opacity: 0.8;
}

/* Collapse animation */
.model-grid-wrap {
  overflow: hidden;
}

.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  max-height: 600px;
  opacity: 1;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

/* Model grid */
.model-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
  padding-top: var(--space-2);
}

.model-card {
  border: 1px solid var(--border-default);
  border-left: 3px solid var(--border-default);
  border-radius: var(--radius);
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.model-card.domestic {
  border-left-color: #3b82f6;
}

.model-card.international {
  border-left-color: #8b5cf6;
}

.model-card:hover {
  border-color: var(--border-strong);
  background: var(--bg-hover);
}

.model-card.active {
  border-color: var(--fg-primary);
  border-left-width: 3px;
  background: var(--bg-hover);
}

.model-card.active.domestic {
  border-left-color: #3b82f6;
}

.model-card.active.international {
  border-left-color: #8b5cf6;
}

.model-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.model-card-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.model-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--fg-primary);
}

.vendor-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
}

.vendor-tag.domestic {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}

.vendor-tag.international {
  background: rgba(139, 92, 246, 0.12);
  color: #8b5cf6;
}

.model-card-desc {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
}

.model-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.model-link {
  font-size: var(--font-size-xs);
  color: var(--accent-blue);
  text-decoration: none;
}

.model-link:hover {
  opacity: 0.8;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.ok {
  background: #16a34a;
  box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.2);
}

.status-dot.fail {
  background: #dc2626;
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2);
}

/* Test Section */
.test-section {
  padding-top: var(--space-2);
  border-top: 1px solid var(--border-default);
}

.test-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.btn-test {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius);
  color: var(--fg-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-test:hover:not(:disabled) {
  border-color: var(--fg-primary);
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid var(--border-strong);
  border-top-color: var(--fg-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.test-result {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
}

.test-result.success {
  color: #16a34a;
}

.test-result.fail {
  color: #dc2626;
}

.test-result-icon {
  display: flex;
  align-items: center;
}

.test-result-text {
  line-height: 1.4;
}

.test-latency {
  font-size: var(--font-size-xs);
  color: var(--fg-tertiary);
  font-family: var(--geist-mono);
  white-space: nowrap;
}

/* Save */
.form-actions {
  padding-top: var(--space-2);
  border-top: 1px solid var(--border-default);
}

.btn-primary {
  height: 40px;
  padding: 0 var(--space-5);
  background: var(--fg-primary);
  border: 1px solid var(--fg-primary);
  border-radius: var(--radius);
  color: var(--bg-background);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .model-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .model-grid {
    grid-template-columns: 1fr;
  }
}
</style>
