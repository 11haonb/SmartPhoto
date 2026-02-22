/**
 * SmartPhoto API Client
 * Wraps all backend API calls with auth token management
 */
const API = (() => {
  const BASE_URL = window.SMARTPHOTO_API_URL || 'http://localhost:28000/api/v1';
  let _token = localStorage.getItem('sp_token') || null;
  let _userId = localStorage.getItem('sp_user_id') || null;

  function setAuth(token, userId) {
    _token = token;
    _userId = userId;
    localStorage.setItem('sp_token', token);
    localStorage.setItem('sp_user_id', userId);
  }

  function clearAuth() {
    _token = null;
    _userId = null;
    localStorage.removeItem('sp_token');
    localStorage.removeItem('sp_user_id');
  }

  function isLoggedIn() {
    return Boolean(_token);
  }

  function getUserId() {
    return _userId;
  }

  function headers(extra) {
    const h = { ...extra };
    if (_token) {
      h['Authorization'] = `Bearer ${_token}`;
    }
    return h;
  }

  async function request(method, path, body, isFormData) {
    const opts = {
      method,
      headers: isFormData ? headers() : headers({ 'Content-Type': 'application/json' }),
    };
    if (body) {
      opts.body = isFormData ? body : JSON.stringify(body);
    }
    const res = await fetch(`${BASE_URL}${path}`, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || `Request failed: ${res.status}`);
    }
    return data;
  }

  // Auth
  async function sendCode(phone) {
    return request('POST', '/auth/send-code', { phone });
  }

  async function login(phone, code) {
    const data = await request('POST', '/auth/login', { phone, code });
    setAuth(data.access_token, data.user_id);
    return data;
  }

  // Photos
  async function createBatch(totalPhotos) {
    return request('POST', '/photos/batch', { total_photos: totalPhotos });
  }

  async function uploadPhoto(batchId, file) {
    const form = new FormData();
    form.append('batch_id', batchId);
    form.append('file', file);
    return request('POST', '/photos/upload', form, true);
  }

  async function getBatchPhotos(batchId) {
    return request('GET', `/photos/batch/${batchId}`);
  }

  async function getPhoto(photoId) {
    return request('GET', `/photos/${photoId}`);
  }

  // Organize
  async function startOrganize(batchId) {
    return request('POST', '/organize/start', { batch_id: batchId });
  }

  async function getOrganizeStatus(taskId) {
    return request('GET', `/organize/status/${taskId}`);
  }

  async function getOrganizeResults(taskId) {
    return request('GET', `/organize/results/${taskId}`);
  }

  // Settings
  async function getSettings() {
    return request('GET', '/settings');
  }

  async function updateSettings(aiConfig) {
    return request('PUT', '/settings', { ai_config: aiConfig });
  }

  async function getAIProviders() {
    return request('GET', '/settings/ai-providers');
  }

  return {
    setAuth,
    clearAuth,
    isLoggedIn,
    getUserId,
    sendCode,
    login,
    createBatch,
    uploadPhoto,
    getBatchPhotos,
    getPhoto,
    startOrganize,
    getOrganizeStatus,
    getOrganizeResults,
    getSettings,
    updateSettings,
    getAIProviders,
  };
})();
