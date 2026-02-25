/**
 * SmartPhoto App - Router, Settings page, and Tab bar
 */
const App = (() => {
  let _currentPage = null;
  let _currentParams = {};

  function init() {
    if (API.isLoggedIn()) {
      navigate('home');
    } else {
      navigate('login');
    }
  }

  function navigate(page, params) {
    // Destroy previous page
    if (_currentPage && typeof window[_currentPage + 'Page'] !== 'undefined') {
      const mod = getPageModule(_currentPage);
      if (mod && mod.destroy) mod.destroy();
    }

    _currentPage = page;
    _currentParams = params || {};

    const app = document.getElementById('app');
    const mod = getPageModule(page);
    if (mod) {
      const html = mod.render(_currentParams);
      if (html instanceof Promise) {
        html.then(h => { app.innerHTML = h; }).catch(err => {
          app.innerHTML = `<div class="empty-state"><p>页面加载失败</p></div>`;
          console.error('Page render error:', err);
        });
      } else {
        app.innerHTML = html;
      }
    }
  }

  function getPageModule(page) {
    switch (page) {
      case 'login': return AuthPage;
      case 'home': return HomePage;
      case 'album': return AlbumPage;
      case 'organize': return OrganizePage;
      case 'results': return ResultsPage;
      case 'settings': return SettingsPage;
      default: return null;
    }
  }

  function toast(msg) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    document.getElementById('app').appendChild(el);
    setTimeout(() => el.remove(), 2500);
  }

  function renderTabBar(active) {
    return `
      <div class="tab-bar">
        <button class="tab-item ${active === 'home' ? 'active' : ''}" onclick="App.navigate('home')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          <span>首页</span>
        </button>
        <button class="tab-item ${active === 'album' ? 'active' : ''}" onclick="App.navigate('album')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
          <span>相册</span>
        </button>
        <button class="tab-item ${active === 'settings' ? 'active' : ''}" onclick="App.navigate('settings')">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.488.488 0 00-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 00-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
          <span>设置</span>
        </button>
      </div>
    `;
  }

  function logout() {
    API.clearAuth();
    navigate('login');
  }

  return { init, navigate, toast, renderTabBar, logout };
})();


/**
 * Home Page
 */
const HomePage = (() => {
  function render() {
    return `
      <div class="page">
        <div class="page-header">
          <h1>SmartPhoto</h1>
          <p>AI 智能照片整理助手</p>
        </div>
        <div class="page-body">
          <div class="home-hero">
            <div class="home-hero-icon">
              <svg viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
            </div>
            <h2>智能整理你的照片</h2>
            <p>上传照片，AI 自动分析分类、检测问题、挑选最佳</p>
          </div>

          <div class="feature-list">
            <div class="feature-item">
              <div class="feature-icon" style="background:#e8eaff;color:#667eea">⏱</div>
              <div>
                <h3>EXIF 时间线</h3>
                <p>自动按拍摄时间排列</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon" style="background:#fff3e0;color:#ff9800">🏷</div>
              <div>
                <h3>智能分类</h3>
                <p>人物、风景、美食、文档...自动归类</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon" style="background:#e8f5e9;color:#4caf50">🔍</div>
              <div>
                <h3>问题检测</h3>
                <p>模糊、过曝、欠曝、截图一键发现</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon" style="background:#fce4ec;color:#e91e63">⭐</div>
              <div>
                <h3>最佳挑选</h3>
                <p>相似照片自动分组，推荐保留最佳</p>
              </div>
            </div>
          </div>

          <button class="primary-btn" onclick="App.navigate('album')">选择照片开始整理</button>
        </div>
        ${App.renderTabBar('home')}
      </div>
    `;
  }

  return { render };
})();


/**
 * Settings Page
 */
const SettingsPage = (() => {
  let _providers = [];
  let _selectedProvider = 'local';
  let _apiKey = '';

  async function render() {
    setTimeout(loadData, 100);

    return `
      <div class="page">
        <div class="page-header">
          <h1>设置</h1>
          <p>配置 AI 分析引擎</p>
        </div>
        <div class="page-body" id="settings-body">
          <div style="text-align:center;padding:40px"><div class="spinner"></div></div>
        </div>
        ${App.renderTabBar('settings')}
      </div>
    `;
  }

  async function loadData() {
    try {
      const [providers, settings] = await Promise.all([
        API.getAIProviders(),
        API.getSettings().catch(() => null),
      ]);
      _providers = providers;
      if (settings && settings.ai_config) {
        _selectedProvider = settings.ai_config.provider;
      }
      renderContent();
    } catch (err) {
      const body = document.getElementById('settings-body');
      if (body) {
        body.innerHTML = `<div class="empty-state"><p>加载失败: ${err.message}</p></div>`;
      }
    }
  }

  function renderContent() {
    const body = document.getElementById('settings-body');
    if (!body) return;

    const needsKey = _providers.find(p => p.provider === _selectedProvider);
    const showKeyInput = needsKey && needsKey.requires_api_key;

    body.innerHTML = `
      <div class="settings-section">
        <h3>AI 分析引擎</h3>
        <div class="provider-list">
          ${_providers.map(p => `
            <div class="provider-card ${_selectedProvider === p.provider ? 'selected' : ''}"
                 onclick="SettingsPage.selectProvider('${p.provider}')">
              <div class="provider-card-icon" style="background:${providerColor(p.provider)}">
                ${providerEmoji(p.provider)}
              </div>
              <div class="provider-card-info">
                <h4>${p.name}</h4>
                <p>${p.description}</p>
                ${p.free_tier ? `<p style="color:#4caf50;font-size:10px">${p.free_tier}</p>` : ''}
              </div>
              <div class="provider-card-check">
                ${_selectedProvider === p.provider ? '✓' : ''}
              </div>
            </div>
          `).join('')}
        </div>

        ${showKeyInput ? `
          <div class="api-key-input">
            <label>API Key</label>
            <input type="password" id="api-key-input" placeholder="请输入 API Key" value="${_apiKey}">
          </div>
        ` : ''}

        <button class="save-btn" onclick="SettingsPage.save()">保存设置</button>
      </div>

      <div class="settings-section">
        <h3>账号</h3>
        <div class="settings-card">
          <div class="settings-item" onclick="App.logout()">
            <div class="settings-item-left">
              <div class="settings-item-icon" style="background:#fce4ec;color:#e91e63">🚪</div>
              <span class="settings-item-label">退出登录</span>
            </div>
            <span class="settings-item-value">→</span>
          </div>
        </div>
      </div>
    `;
  }

  function providerColor(provider) {
    const colors = {
      local: '#e8f5e9', huggingface: '#fff8e1',
      tongyi: '#e3f2fd', claude: '#f3e5f5',
    };
    return colors[provider] || '#f5f5f5';
  }

  function providerEmoji(provider) {
    const emojis = {
      local: '💻', huggingface: '🤗',
      tongyi: '🧠', claude: '🤖',
    };
    return emojis[provider] || '⚙';
  }

  function selectProvider(provider) {
    _selectedProvider = provider;
    renderContent();
  }

  async function save() {
    const keyInput = document.getElementById('api-key-input');
    const apiKey = keyInput ? keyInput.value.trim() : null;

    try {
      await API.updateSettings({
        provider: _selectedProvider,
        api_key: apiKey || null,
        model: null,
      });
      App.toast('设置已保存');
    } catch (err) {
      App.toast('保存失败: ' + err.message);
    }
  }

  function destroy() {
    _providers = [];
    _selectedProvider = 'local';
    _apiKey = '';
  }

  return { render, selectProvider, save, destroy };
})();


// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
