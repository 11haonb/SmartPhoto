/**
 * Results Page - 4-tab view: Timeline / Categories / Issues / Best picks
 */
const ResultsPage = (() => {
  let _data = null;
  let _activeTab = 'timeline';

  async function render(params) {
    const taskId = params.taskId;

    setTimeout(async () => {
      try {
        _data = await API.getOrganizeResults(taskId);
        renderTabContent();
      } catch (err) {
        const body = document.getElementById('results-body');
        if (body) {
          body.innerHTML = `<div class="empty-state"><p>加载失败: ${err.message}</p></div>`;
        }
      }
    }, 100);

    return `
      <div class="page" style="background:#f5f7fa">
        <div class="page-header">
          <h1>整理结果</h1>
          <p>AI 分析完成</p>
        </div>
        <div class="results-tabs">
          <button class="results-tab active" data-tab="timeline" onclick="ResultsPage.switchTab('timeline')">时间线</button>
          <button class="results-tab" data-tab="categories" onclick="ResultsPage.switchTab('categories')">分类</button>
          <button class="results-tab" data-tab="issues" onclick="ResultsPage.switchTab('issues')">问题图</button>
          <button class="results-tab" data-tab="best" onclick="ResultsPage.switchTab('best')">最佳照片</button>
        </div>
        <div class="results-body" id="results-body">
          <div style="text-align:center;padding:40px"><div class="spinner"></div><p style="margin-top:12px;color:#999">加载中...</p></div>
        </div>
        ${App.renderTabBar('home')}
      </div>
    `;
  }

  function switchTab(tab) {
    _activeTab = tab;
    document.querySelectorAll('.results-tab').forEach(el => {
      el.classList.toggle('active', el.dataset.tab === tab);
    });
    renderTabContent();
  }

  function renderTabContent() {
    const body = document.getElementById('results-body');
    if (!body || !_data) return;

    switch (_activeTab) {
      case 'timeline': body.innerHTML = renderTimeline(); break;
      case 'categories': body.innerHTML = renderCategories(); break;
      case 'issues': body.innerHTML = renderIssues(); break;
      case 'best': body.innerHTML = renderBest(); break;
    }
  }

  function photoThumb(photo) {
    if (photo.thumbnail_url) return photo.thumbnail_url;
    if (photo.photo && photo.photo.thumbnail_url) return photo.photo.thumbnail_url;
    return 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" fill="%23ddd"><rect width="100" height="100"/><text x="50" y="55" text-anchor="middle" fill="%23999" font-size="12">No Thumb</text></svg>');
  }

  function photoName(photo) {
    return photo.original_filename || (photo.photo && photo.photo.original_filename) || 'unknown';
  }

  function renderTimeline() {
    const groups = _data.timeline || [];
    if (groups.length === 0) {
      return '<div class="empty-state"><p>暂无时间线数据</p></div>';
    }
    return groups.map(g => `
      <div class="timeline-group">
        <div class="timeline-date">${g.date}</div>
        <div class="photo-grid">
          ${g.photos.map(p => `
            <div class="photo-grid-item">
              <img src="${photoThumb(p)}" alt="${photoName(p)}" loading="lazy">
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  function renderCategories() {
    const cats = _data.categories || [];
    if (cats.length === 0) {
      return '<div class="empty-state"><p>暂无分类数据</p></div>';
    }
    return cats.map(c => `
      <div class="category-group">
        <div class="category-header">
          <span class="category-name">${c.category}${c.sub_category ? ' / ' + c.sub_category : ''}</span>
          <span class="category-count">${c.count} 张</span>
        </div>
        <div class="photo-grid">
          ${c.photos.map(p => `
            <div class="photo-grid-item">
              <img src="${photoThumb(p)}" alt="${photoName(p)}" loading="lazy">
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  function renderIssues() {
    const photos = _data.invalid_photos || [];
    if (photos.length === 0) {
      return '<div class="empty-state"><p>没有检测到问题图片</p></div>';
    }
    return photos.map(item => {
      const p = item.photo || item;
      const a = item.analysis || {};
      const tags = [];
      if (a.is_blurry) tags.push('<span class="issue-tag blurry">模糊</span>');
      if (a.is_overexposed) tags.push('<span class="issue-tag overexposed">过曝</span>');
      if (a.is_underexposed) tags.push('<span class="issue-tag underexposed">欠曝</span>');
      if (a.is_screenshot) tags.push('<span class="issue-tag screenshot">截图</span>');
      if (a.is_invalid) tags.push(`<span class="issue-tag invalid">${a.invalid_reason || '无效'}</span>`);
      return `
        <div class="issue-card">
          <img src="${photoThumb(p)}" alt="${photoName(p)}">
          <div class="issue-info">
            <div class="issue-filename">${photoName(p)}</div>
            <div>${tags.join(' ')}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  function renderBest() {
    const groups = _data.similarity_groups || [];
    if (groups.length === 0) {
      return '<div class="empty-state"><p>暂无相似分组数据</p></div>';
    }
    return groups.map(g => `
      <div class="similarity-group">
        <div class="similarity-header">相似组 · ${g.photos.length} 张照片</div>
        <div class="similarity-photos">
          ${g.photos.map(item => {
            const p = item.photo || item;
            const isBest = (item.analysis && item.analysis.is_best_in_group) ||
                           (p.id === g.best_photo_id);
            return `
              <div class="similarity-photo ${isBest ? '' : 'dimmed'}">
                <img src="${photoThumb(p)}" alt="${photoName(p)}">
                ${isBest ? '<div class="best-badge">BEST</div>' : ''}
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `).join('');
  }

  function destroy() {
    _data = null;
    _activeTab = 'timeline';
  }

  return { render, switchTab, destroy };
})();
