/**
 * Auth Page - Phone + SMS code login
 */
const AuthPage = (() => {
  let _countdown = 0;
  let _timer = null;

  function render() {
    return `
      <div class="auth-page">
        <div class="auth-logo">
          <svg viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
        </div>
        <div class="auth-title">SmartPhoto</div>
        <div class="auth-subtitle">AI 智能照片整理助手</div>
        <div class="auth-form">
          <div class="input-group">
            <input type="tel" id="phone-input" placeholder="请输入手机号" maxlength="11">
          </div>
          <div class="input-group code-row">
            <input type="text" id="code-input" placeholder="验证码" maxlength="6">
            <button class="send-btn" id="send-code-btn" onclick="AuthPage.sendCode()">获取验证码</button>
          </div>
          <button class="login-btn" id="login-btn" onclick="AuthPage.login()">登 录</button>
        </div>
      </div>
    `;
  }

  async function sendCode() {
    const phone = document.getElementById('phone-input').value.trim();
    if (!/^1[3-9]\d{9}$/.test(phone)) {
      App.toast('请输入正确的手机号');
      return;
    }

    const btn = document.getElementById('send-code-btn');
    btn.disabled = true;

    try {
      await API.sendCode(phone);
      App.toast('验证码已发送 (开发模式: 888888)');
      startCountdown(btn);
    } catch (err) {
      App.toast(err.message);
      btn.disabled = false;
    }
  }

  function startCountdown(btn) {
    _countdown = 60;
    btn.textContent = `${_countdown}s`;
    _timer = setInterval(() => {
      _countdown--;
      if (_countdown <= 0) {
        clearInterval(_timer);
        btn.textContent = '获取验证码';
        btn.disabled = false;
      } else {
        btn.textContent = `${_countdown}s`;
      }
    }, 1000);
  }

  async function login() {
    const phone = document.getElementById('phone-input').value.trim();
    const code = document.getElementById('code-input').value.trim();

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      App.toast('请输入正确的手机号');
      return;
    }
    if (!code || code.length < 4) {
      App.toast('请输入验证码');
      return;
    }

    const btn = document.getElementById('login-btn');
    btn.disabled = true;
    btn.textContent = '登录中...';

    try {
      await API.login(phone, code);
      App.toast('登录成功');
      App.navigate('home');
    } catch (err) {
      App.toast(err.message);
      btn.disabled = false;
      btn.textContent = '登 录';
    }
  }

  function destroy() {
    if (_timer) clearInterval(_timer);
  }

  return { render, sendCode, login, destroy };
})();
