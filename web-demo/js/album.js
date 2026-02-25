/**
 * Album Page - File selection, preview grid, upload progress
 */
const AlbumPage = (() => {
  let _selectedFiles = [];
  let _batchId = null;
  let _uploading = false;

  function render() {
    return `
      <div class="page">
        <div class="page-header">
          <h1>选择照片</h1>
          <p>支持 JPG、PNG、HEIC、WebP 格式</p>
        </div>
        <div class="page-body">
          <div class="upload-zone" id="upload-zone" onclick="document.getElementById('file-input').click()">
            <svg viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
            <p>点击选择照片</p>
            <p class="file-types">支持 JPG / PNG / HEIC / WebP，单张最大 10MB</p>
          </div>
          <input type="file" id="file-input" multiple accept="image/jpeg,image/png,image/heic,image/heif,image/webp" style="display:none" onchange="AlbumPage.onFilesSelected(this)">
          <div id="photo-preview-grid" class="photo-grid"></div>
          <div id="upload-progress-section" style="display:none">
            <div class="upload-progress">
              <div class="progress-bar-container">
                <div class="progress-bar" id="upload-bar" style="width:0%"></div>
              </div>
              <div class="progress-text" id="upload-text">准备上传...</div>
            </div>
          </div>
          <button class="primary-btn" id="upload-btn" style="display:none" onclick="AlbumPage.startUpload()">
            上传并开始整理
          </button>
        </div>
        ${App.renderTabBar('home')}
      </div>
    `;
  }

  const _ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/heic', 'image/heif', 'image/webp']);
  const _MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  function onFilesSelected(input) {
    const files = Array.from(input.files);
    if (files.length === 0) return;
    if (files.length > 100) {
      App.toast('最多选择100张照片');
      return;
    }

    const invalid = files.filter(f => !_ALLOWED_TYPES.has(f.type));
    if (invalid.length > 0) {
      App.toast(`不支持的文件类型: ${invalid.map(f => f.name).join(', ')}`);
      return;
    }

    const oversized = files.filter(f => f.size > _MAX_FILE_SIZE);
    if (oversized.length > 0) {
      App.toast(`文件过大 (最大10MB): ${oversized.map(f => f.name).join(', ')}`);
      return;
    }

    _selectedFiles = files;
    renderPreview();
    document.getElementById('upload-btn').style.display = 'block';
    document.getElementById('upload-zone').style.display = 'none';
  }

  function renderPreview() {
    const grid = document.getElementById('photo-preview-grid');
    grid.innerHTML = '';
    _selectedFiles.forEach((file, i) => {
      const url = URL.createObjectURL(file);
      grid.innerHTML += `
        <div class="photo-grid-item">
          <img src="${url}" alt="${file.name}">
          <button class="remove-btn" onclick="AlbumPage.removeFile(${i})">×</button>
        </div>
      `;
    });
  }

  function removeFile(index) {
    _selectedFiles = _selectedFiles.filter((_, i) => i !== index);
    if (_selectedFiles.length === 0) {
      document.getElementById('upload-btn').style.display = 'none';
      document.getElementById('upload-zone').style.display = '';
    }
    renderPreview();
  }

  async function startUpload() {
    if (_uploading || _selectedFiles.length === 0) return;
    _uploading = true;

    const btn = document.getElementById('upload-btn');
    btn.disabled = true;
    btn.textContent = '上传中...';

    const progressSection = document.getElementById('upload-progress-section');
    progressSection.style.display = 'block';

    try {
      const batch = await API.createBatch(_selectedFiles.length);
      _batchId = batch.id;

      let uploaded = 0;
      for (const file of _selectedFiles) {
        await API.uploadPhoto(_batchId, file);
        uploaded++;
        const pct = Math.round((uploaded / _selectedFiles.length) * 100);
        document.getElementById('upload-bar').style.width = pct + '%';
        document.getElementById('upload-text').textContent =
          `已上传 ${uploaded} / ${_selectedFiles.length} 张 (${pct}%)`;
      }

      App.toast('上传完成，开始整理...');
      const result = await API.startOrganize(_batchId);
      App.navigate('organize', { taskId: result.task_id, batchId: _batchId });
    } catch (err) {
      App.toast('上传失败: ' + err.message);
      btn.disabled = false;
      btn.textContent = '重新上传';
      _uploading = false;
    }
  }

  function destroy() {
    _selectedFiles = [];
    _batchId = null;
    _uploading = false;
  }

  return { render, onFilesSelected, removeFile, startUpload, destroy };
})();
