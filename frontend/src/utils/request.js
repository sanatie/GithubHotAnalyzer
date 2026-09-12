import axios from 'axios';
import { ElMessage } from 'element-plus';

const isElectron = window.navigator.userAgent.toLowerCase().includes('electron') || window.process?.versions?.electron;
const baseURL = 'http://127.0.0.1:8000/api';

const service = axios.create({
  baseURL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

service.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

service.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('响应错误:', error);

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试');
    } else if (error.code === 'ERR_NETWORK') {
      ElMessage.error('网络连接失败，请检查后端服务是否启动');
    } else if (error.response) {
      const { status, data } = error.response;
      const message = data?.detail || data?.message || `请求失败 (${status})`;

      switch (status) {
        case 400:
          ElMessage.error(message || '请求参数错误');
          break;
        case 401:
          ElMessage.error(message || '未授权，请重新登录');
          break;
        case 403:
          ElMessage.error(message || '没有访问权限');
          break;
        case 404:
          ElMessage.error(message || '资源不存在');
          break;
        case 500:
          ElMessage.error(message || '服务器内部错误');
          break;
        case 502:
          ElMessage.error(message || '网关错误，请稍后重试');
          break;
        default:
          ElMessage.error(message || `请求失败 (${status})`);
      }
    } else {
      ElMessage.error(error.message || '请求失败');
    }

    return Promise.reject(error);
  }
);

export default service;
