import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:pin_code_fields/pin_code_fields.dart';
import 'package:provider/provider.dart';
import 'package:photo_organizer/services/api_service.dart';
import 'package:photo_organizer/services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  final _codeController = TextEditingController();
  bool _codeSent = false;
  bool _loading = false;
  int _countdown = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _checkExistingAuth();
  }

  Future<void> _checkExistingAuth() async {
    final auth = context.read<AuthService>();
    await auth.checkAuth();
    if (auth.isAuthenticated && mounted) {
      context.go('/');
    }
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _codeController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _sendCode() async {
    final phone = _phoneController.text.trim();
    if (phone.length != 11) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请输入正确的手机号')),
      );
      return;
    }

    setState(() => _loading = true);
    try {
      final api = context.read<ApiService>();
      await api.sendSmsCode(phone);
      setState(() {
        _codeSent = true;
        _countdown = 60;
      });
      _startCountdown();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('发送验证码失败: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _startCountdown() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown <= 1) {
        timer.cancel();
        if (mounted) setState(() => _countdown = 0);
      } else {
        if (mounted) setState(() => _countdown--);
      }
    });
  }

  Future<void> _login() async {
    final phone = _phoneController.text.trim();
    final code = _codeController.text.trim();

    if (code.length < 4) return;

    setState(() => _loading = true);
    try {
      final api = context.read<ApiService>();
      final result = await api.login(phone, code);

      final token = result['access_token'] as String;
      final userId = result['user_id'] as String;

      await api.saveToken(token);
      final auth = context.read<AuthService>();
      await auth.setAuth(token, userId);

      if (mounted) context.go('/');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('登录失败: 验证码错误或已过期')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 60),
              Icon(
                Icons.photo_library_rounded,
                size: 80,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 16),
              Text(
                '智能图片整理',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                '自动分类 · 筛选最佳 · 整理相册',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              TextField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                maxLength: 11,
                decoration: InputDecoration(
                  labelText: '手机号',
                  hintText: '请输入手机号',
                  prefixIcon: const Icon(Icons.phone_android),
                  counterText: '',
                  suffixIcon: TextButton(
                    onPressed: _countdown > 0 || _loading ? null : _sendCode,
                    child: Text(
                      _countdown > 0 ? '${_countdown}s' : '获取验证码',
                    ),
                  ),
                ),
              ),
              if (_codeSent) ...[
                const SizedBox(height: 24),
                Text(
                  '请输入验证码',
                  style: Theme.of(context).textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                PinCodeTextField(
                  appContext: context,
                  length: 6,
                  controller: _codeController,
                  keyboardType: TextInputType.number,
                  animationType: AnimationType.fade,
                  pinTheme: PinTheme(
                    shape: PinCodeFieldShape.box,
                    borderRadius: BorderRadius.circular(8),
                    fieldHeight: 48,
                    fieldWidth: 42,
                    activeFillColor: Colors.white,
                    inactiveFillColor: Colors.grey.shade100,
                    selectedFillColor: Colors.white,
                  ),
                  enableActiveFill: true,
                  onCompleted: (_) => _login(),
                  onChanged: (_) {},
                ),
              ],
              const Spacer(),
              if (_codeSent)
                ElevatedButton(
                  onPressed: _loading ? null : _login,
                  child: _loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('登录'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
