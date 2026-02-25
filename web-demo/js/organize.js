/**
 * Organize Progress Page - 5-stage progress ring + polling
 */
const OrganizePage = (() => {
  let _timer = null;
  let _taskId = null;
  let _pollInterval = 3000;
  const _maxInterval = 30000;

  const STAGES = [
    { name: 'EXIF提取', desc: '读取拍摄时间、相机型号、GPS' },
    { name: '质量分析', desc: '检测模糊、曝光、截图' },
    { name: '图片分类', desc: '按内容自动归类' },
    { name: '相似分组', desc: '找出重复/相似照片' },
    { name: '最佳挑选', desc: '从每组选出最佳照片' },
  ];

  function render(params) {
    _taskId = params.taskId;

    const stagesHtml = STAGES.map((s, i) => `
      <div class="stage-item" id="stage-${i}">
        <div class="stage-icon pending" id="stage-icon-${i}">
          ${i + 1}
        </div>
        <div class="stage-info">
          <div class="stage-name">${s.name}</div>
          <div class="stage-detail" id="stage-detail-${i}">${s.desc}</div>
        </div>
      </div>
    `).join('');

    setTimeout(() => pollStatus(), 500);

    return `
      <div class="page">
        <div class="page-header">
          <h1>整理中</h1>
          <p>AI 正在分析您的照片，请稍候...</p>
        </div>
        <div class="page-body">
          <div class="progress-page">
            <div class="progress-circle-container">
              <svg class="progress-circle" viewBox="0 0 200 200">
                <defs>
                  <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#667eea"/>
                    <stop offset="100%" stop-color="#764ba2"/>
                  </linearGradient>
                </defs>
                <circle class="progress-circle-bg" cx="100" cy="100" r="85"/>
                <circle class="progress-circle-fill" id="progress-ring" cx="100" cy="100" r="85"
                  stroke-dasharray="534" stroke-dashoffset="534"/>
              </svg>
              <div class="progress-percent" id="progress-pct">0<span>%</span></div>
            </div>
            <div class="stage-list">
              ${stagesHtml}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  async function pollStatus() {
    if (!_taskId) return;

    try {
      const status = await API.getOrganizeStatus(_taskId);
      updateUI(status);
      _pollInterval = 3000; // reset on success

      if (status.status === 'completed') {
        App.toast('整理完成！');
        setTimeout(() => App.navigate('results', { taskId: _taskId }), 1000);
        return;
      }
      if (status.status === 'failed') {
        App.toast('整理失败: ' + (status.error_message || '未知错误'));
        return;
      }

      _timer = setTimeout(pollStatus, _pollInterval);
    } catch (err) {
      App.toast('查询进度失败: ' + err.message);
      // Exponential backoff on error, cap at maxInterval
      _pollInterval = Math.min(_pollInterval * 2, _maxInterval);
      _timer = setTimeout(pollStatus, _pollInterval);
    }
  }

  function updateUI(status) {
    // Update ring
    const pct = status.progress_percent || 0;
    const ring = document.getElementById('progress-ring');
    if (ring) {
      const circumference = 534;
      ring.setAttribute('stroke-dashoffset', circumference - (circumference * pct / 100));
    }
    const pctEl = document.getElementById('progress-pct');
    if (pctEl) pctEl.innerHTML = `${pct}<span>%</span>`;

    // Update stages
    const currentStage = status.current_stage || 0;
    for (let i = 0; i < STAGES.length; i++) {
      const icon = document.getElementById(`stage-icon-${i}`);
      const detail = document.getElementById(`stage-detail-${i}`);
      if (!icon) continue;

      icon.className = 'stage-icon';
      if (i + 1 < currentStage) {
        icon.classList.add('completed');
        icon.innerHTML = '✓';
        if (detail) detail.textContent = '已完成';
      } else if (i + 1 === currentStage) {
        if (status.status === 'failed') {
          icon.classList.add('failed');
          icon.innerHTML = '✕';
          if (detail) detail.textContent = status.error_message || '失败';
        } else {
          icon.classList.add('running');
          icon.innerHTML = `<div class="spinner" style="width:18px;height:18px;border-width:2px"></div>`;
          if (detail) {
            detail.textContent = status.photos_total > 0
              ? `处理中 ${status.photos_processed}/${status.photos_total}`
              : '处理中...';
          }
        }
      } else {
        icon.classList.add('pending');
        icon.innerHTML = `${i + 1}`;
        if (detail) detail.textContent = STAGES[i].desc;
      }
    }
  }

  function destroy() {
    if (_timer) clearTimeout(_timer);
    _timer = null;
    _taskId = null;
    _pollInterval = 3000;
  }

  return { render, destroy };
})();
