/**
 * Results Page - 4-tab view: Timeline / Categories / Issues / Best picks
 */
const ResultsPage = (() => {
  let _data = null;
  let _activeTab = 'timeline';
  let _taskId = null;
  let _page = 1;
  let _totalPages = 1;

  function esc(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  async function render(params) {
    _taskId = params.taskId;

    setTimeout(async () => {
      try {
        _page = 1;
        _data = await API.getOrganizeResults(_taskId, _page);
        _totalPages = _data.total_pages || 1;
        renderTabContent();
      } catch (err) {
        const body = document.getElementById('results-body');
        if (body) {
          const msg = document.createElement('div');
          msg.className = 'empty-state';
          msg.textContent = '加载失败: ' + err.message;
          body.innerHTML = '';
          body.appendChild(msg);
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

  async function handleExport(path) {
    try {
      await API.downloadZip(path);
    } catch (err) {
      App.toast('导出失败: ' + err.message);
    }
  }

  async function handleMarkBest(photoId, groupId) {
    try {
      await API.markBest(photoId, _taskId);
      // update local data
      const groups = _data.similarity_groups || [];
      for (const g of groups) {
        if (g.group_id === groupId) {
          for (const item of g.photos) {
            const p = item.photo || item;
            if (item.analysis) {
              item.analysis.is_best_in_group = (p.id === photoId);
            }
          }
          g.best_photo_id = photoId;
          break;
        }
      }
      renderTabContent();
    } catch (err) {
      App.toast('操作失败: ' + err.message);
    }
  }

  // expose for inline onclick
  window._ResultsMarkBest = handleMarkBest;
  window._ResultsExport = handleExport;

  async function loadMore() {
    if (_page >= _totalPages) return;
    try {
      _page++;
      const more = await API.getOrganizeResults(_taskId, _page);
      // Merge timeline, categories, similarity_groups, invalid_photos
      _data.timeline = [...(_data.timeline || []), ...(more.timeline || [])];
      _data.categories = [...(_data.categories || []), ...(more.categories || [])];
      _data.similarity_groups = [...(_data.similarity_groups || []), ...(more.similarity_groups || [])];
      _data.invalid_photos = [...(_data.invalid_photos || []), ...(more.invalid_photos || [])];
      _totalPages = more.total_pages || _totalPages;
      renderTabContent();
    } catch (err) {
      App.toast('加载更多失败: ' + err.message);
    }
  }

  window._ResultsLoadMore = loadMore;

  function _paginationBar() {
    if (_page >= _totalPages) return '';
    return `<div style="text-align:center;padding:16px">
      <button class="export-btn" style="padding:10px 24px" onclick="_ResultsLoadMore()">加载更多 (${_page}/${_totalPages})</button>
    </div>`;
  }

  function renderTimeline() {
    const groups = _data.timeline || [];
    if (groups.length === 0) {
      return '<div class="empty-state"><p>暂无时间线数据</p></div>';
    }
    return groups.map(g => `
      <div class="timeline-group">
        <div class="timeline-date">
          <span>${esc(g.date)}</span>
          <button class="export-btn" onclick="_ResultsExport('/export/by-date/${esc(_taskId)}?date=${esc(g.date)}')">导出</button>
        </div>
        <div class="photo-grid">
          ${g.photos.map(p => `
            <div class="photo-grid-item">
              <img src="${esc(photoThumb(p))}" alt="${esc(photoName(p))}" loading="lazy">
            </div>
          `).join('')}
        </div>
      </div>
    `).join('') + _paginationBar();
  }

  function renderCategories() {
    const cats = _data.categories || [];
    if (cats.length === 0) {
      return '<div class="empty-state"><p>暂无分类数据</p></div>';
    }
    return cats.map(c => `
      <div class="category-group">
        <div class="category-header">
          <span class="category-name">${esc(c.category)}${c.sub_category ? ' / ' + esc(c.sub_category) : ''}</span>
          <span class="category-count">${esc(c.count)} 张</span>
          <button class="export-btn" onclick="_ResultsExport('/export/by-category/${esc(_taskId)}?category=${encodeURIComponent(c.category)}')">导出</button>
        </div>
        <div class="photo-grid">
          ${c.photos.map(p => `
            <div class="photo-grid-item">
              <img src="${esc(photoThumb(p))}" alt="${esc(photoName(p))}" loading="lazy">
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
      if (a.is_invalid) tags.push(`<span class="issue-tag invalid">${esc(a.invalid_reason || '无效')}</span>`);
      return `
        <div class="issue-card">
          <img src="${esc(photoThumb(p))}" alt="${esc(photoName(p))}">
          <div class="issue-info">
            <div class="issue-filename">${esc(photoName(p))}</div>
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
    const exportAllBtn = `
      <div style="padding:12px 16px">
        <button class="export-btn" style="width:100%;padding:10px" onclick="_ResultsExport('/export/best/${esc(_taskId)}')">导出全部最佳照片</button>
      </div>
    `;
    const groupsHtml = groups.map(g => `
      <div class="similarity-group">
        <div class="similarity-header">相似组 · ${esc(g.photos.length)} 张照片</div>
        <div class="similarity-photos">
          ${g.photos.map(item => {
            const p = item.photo || item;
            const isBest = (item.analysis && item.analysis.is_best_in_group) ||
                           (p.id === g.best_photo_id);
            return `
              <div class="similarity-photo ${isBest ? '' : 'selectable'}" ${!isBest ? `onclick="_ResultsMarkBest('${esc(p.id)}', '${esc(g.group_id)}')" title="点击设为最佳"` : ''}>
                <img src="${esc(photoThumb(p))}" alt="${esc(photoName(p))}">
                ${isBest ? '<div class="best-badge">BEST</div>' : ''}
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `).join('');
    return exportAllBtn + groupsHtml;
  }

  function destroy() {
    _data = null;
    _activeTab = 'timeline';
    _taskId = null;
    _page = 1;
    _totalPages = 1;
  }

  return { render, switchTab, destroy };
})();
