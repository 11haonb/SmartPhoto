import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:photo_organizer/models/models.dart';
import 'package:photo_organizer/services/api_service.dart';
import 'package:photo_organizer/services/auth_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  List<AIProviderModel> _providers = [];
  String _selectedProvider = 'local';
  bool _hasApiKey = false;
  String? _currentModel;
  final _apiKeyController = TextEditingController();
  final _modelController = TextEditingController();
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    _modelController.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    try {
      final api = context.read<ApiService>();
      final settings = await api.getSettings();
      final providers = await api.getAIProviders();

      if (mounted) {
        setState(() {
          _providers = providers;
          if (settings['ai_config'] != null) {
            _selectedProvider = settings['ai_config']['provider'];
            _hasApiKey = settings['ai_config']['has_api_key'] ?? false;
            _currentModel = settings['ai_config']['model'];
            if (_currentModel != null) {
              _modelController.text = _currentModel!;
            }
          }
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _saveSettings() async {
    setState(() => _saving = true);
    try {
      final api = context.read<ApiService>();
      final data = {
        'ai_config': {
          'provider': _selectedProvider,
          if (_apiKeyController.text.isNotEmpty)
            'api_key': _apiKeyController.text,
          if (_modelController.text.isNotEmpty) 'model': _modelController.text,
        },
      };
      await api.updateSettings(data);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('设置已保存')),
        );
        _apiKeyController.clear();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('保存失败: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('设置'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // AI Provider Selection
          Text(
            'AI 分析引擎',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 12),
          ..._providers.map((provider) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: RadioListTile<String>(
                  value: provider.provider,
                  groupValue: _selectedProvider,
                  onChanged: (value) {
                    if (value != null) {
                      setState(() => _selectedProvider = value);
                    }
                  },
                  title: Row(
                    children: [
                      Text(provider.name),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: _accuracyColor(provider.accuracy).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          provider.accuracy,
                          style: TextStyle(
                            fontSize: 11,
                            color: _accuracyColor(provider.accuracy),
                          ),
                        ),
                      ),
                    ],
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(provider.description, style: const TextStyle(fontSize: 13)),
                      if (provider.freeTier != null)
                        Text(
                          '免费额度: ${provider.freeTier}',
                          style: TextStyle(fontSize: 12, color: Colors.green.shade700),
                        ),
                    ],
                  ),
                ),
              )),

          // API Key input (if provider requires it)
          if (_providers.any((p) =>
              p.provider == _selectedProvider && p.requiresApiKey)) ...[
            const SizedBox(height: 16),
            TextField(
              controller: _apiKeyController,
              obscureText: true,
              decoration: InputDecoration(
                labelText: 'API Key',
                hintText: _hasApiKey ? '已配置 (留空不修改)' : '请输入 API Key',
                prefixIcon: const Icon(Icons.key),
                suffixIcon: _hasApiKey
                    ? const Icon(Icons.check_circle, color: Colors.green)
                    : null,
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _modelController,
              decoration: const InputDecoration(
                labelText: '模型名称 (可选)',
                hintText: '使用默认模型',
                prefixIcon: Icon(Icons.smart_toy),
              ),
            ),
          ],

          const SizedBox(height: 24),
          FilledButton(
            onPressed: _saving ? null : _saveSettings,
            child: _saving
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Text('保存设置'),
          ),

          const Divider(height: 48),

          // Logout
          OutlinedButton.icon(
            onPressed: () async {
              final auth = context.read<AuthService>();
              final api = context.read<ApiService>();
              await api.clearToken();
              await auth.logout();
              if (mounted) context.go('/login');
            },
            icon: const Icon(Icons.logout, color: Colors.red),
            label: const Text('退出登录', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  Color _accuracyColor(String accuracy) {
    switch (accuracy) {
      case '最高':
        return Colors.purple;
      case '高':
        return Colors.blue;
      case '中等':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
}
