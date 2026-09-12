import request from '../utils/request';

export default {
  analyzeRepo(data) {
    return request.post('/v1/analysis/repositories', data);
  },

  getReportList(params) {
    return request.get('/v1/analysis/reports', { params });
  },

  getReportDetail(reportId) {
    return request.get(`/v1/analysis/reports/${reportId}`);
  },

  deleteReport(reportId) {
    return request.delete(`/v1/analysis/reports/${reportId}`);
  },

  deleteReportsBatch(reportIds) {
    return request.post('/v1/analysis/reports/batch-delete', { report_ids: reportIds });
  },

  deleteAllReports() {
    return request.delete('/v1/analysis/reports');
  },

  getRepoList(params) {
    return request.get('/v1/repositories', { params });
  },

  getRepoById(repoId) {
    return request.get(`/v1/repositories/${repoId}`);
  },

  getRepoByFullName(fullName) {
    return request.get(`/v1/repositories/by-name/${fullName}`);
  },

  searchGitHubRepos(params) {
    return request.get('/v1/repositories/search', { params });
  },

  getTrending(params) {
    return request.get('/v1/trending', { params });
  },

  getFavorites(params) {
    return request.get('/v1/favorites', { params });
  },

  addFavorite(data) {
    return request.post('/v1/favorites', data);
  },

  batchAddFavorites(data) {
    return request.post('/v1/favorites/batch', data);
  },

  deleteFavorite(favId) {
    return request.delete(`/v1/favorites/${favId}`);
  },

  updateFavorite(favId, data) {
    return request.put(`/v1/favorites/${favId}`, data);
  },

  checkFavorite(repoId) {
    return request.get(`/v1/favorites/check/${repoId}`);
  },

  getAIConfig() {
    return request.get('/v1/settings/ai');
  },

  updateAIConfig(data) {
    return request.put('/v1/settings/ai', data);
  },

  testAIConnection(data) {
    return request.post('/v1/settings/ai/test', data);
  },

  securityCheck(reportId) {
    return request.post(`/v1/analysis/security-scan/${reportId}`);
  },

  chatRecommend(data) {
    return request.post('/v1/chat/recommend', data, { timeout: 60000 });
  },

  getChatHistory(params) {
    return request.get('/v1/chat/history', { params });
  },

  deleteChatHistory(recordId) {
    return request.delete(`/v1/chat/history/${recordId}`);
  },

  clearChatHistory() {
    return request.delete('/v1/chat/history');
  },

  probeProject(author, repository) {
    return request.get(`/v1/download/probe/${author}/${repository}`);
  },

  createDownload(data) {
    return request.post('/v1/download', data);
  },

  getDownloadTasks(params) {
    return request.get('/v1/download', { params });
  },

  cancelDownload(taskId) {
    return request.post(`/v1/download/${taskId}/cancel`);
  },

  deleteDownload(taskId) {
    return request.delete(`/v1/download/${taskId}`);
  },

  openDownloadDir(taskId) {
    return request.post(`/v1/download/${taskId}/open-dir`);
  },

  getDefaultDownloadDir() {
    return request.get('/v1/download/default-dir');
  }
};