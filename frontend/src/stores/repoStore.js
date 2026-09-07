import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api';

export const useRepoStore = defineStore('repo', () => {
  const reports = ref([]);
  const favorites = ref([]);
  const currentReport = ref(null);
  const loading = ref(false);

  async function fetchReportList(params) {
    loading.value = true;
    try {
      const res = await api.getReportList(params);
      reports.value = res.data.items || [];
      return res.data;
    } finally {
      loading.value = false;
    }
  }

  async function analyzeRepo(data) {
    loading.value = true;
    try {
      const res = await api.analyzeRepo(data);
      return res.data;
    } finally {
      loading.value = false;
    }
  }

  async function fetchFavorites() {
    const res = await api.getFavorites();
    favorites.value = res.data.items || [];
  }

  async function addFavorite(repoData) {
    const res = await api.addFavorite(repoData);
    await fetchFavorites();
    return res.data;
  }

  async function deleteFavorite(favId) {
    await api.deleteFavorite(favId);
    await fetchFavorites();
  }

  return {
    reports,
    favorites,
    currentReport,
    loading,
    fetchReportList,
    analyzeRepo,
    fetchFavorites,
    addFavorite,
    deleteFavorite
  };
});
