import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('智能图片整理'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 20),
            Icon(
              Icons.auto_fix_high_rounded,
              size: 100,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              '让相册井井有条',
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              'AI 自动分析你的照片，按日期、场景分类，\n筛选模糊图片，挑选最佳照片',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: Colors.grey,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 40),
            _FeatureCard(
              icon: Icons.calendar_month,
              title: '按日期整理',
              description: '根据 EXIF 拍摄时间自动排列时间线',
              color: Colors.blue,
            ),
            const SizedBox(height: 12),
            _FeatureCard(
              icon: Icons.category,
              title: '智能分类',
              description: '人物、风景、美食、文档自动归类',
              color: Colors.green,
            ),
            const SizedBox(height: 12),
            _FeatureCard(
              icon: Icons.blur_on,
              title: '筛选问题图',
              description: '标记模糊、过曝、欠曝等质量问题',
              color: Colors.orange,
            ),
            const SizedBox(height: 12),
            _FeatureCard(
              icon: Icons.star,
              title: '挑选最佳',
              description: '从连拍/相似照片中自动选出最好的一张',
              color: Colors.purple,
            ),
            const SizedBox(height: 32),
            FilledButton.icon(
              onPressed: () => context.go('/album'),
              icon: const Icon(Icons.add_photo_alternate),
              label: const Text('选择照片开始整理'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                textStyle: const TextStyle(fontSize: 16),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;
  final Color color;

  const _FeatureCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withOpacity(0.1),
          child: Icon(icon, color: color),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(description),
      ),
    );
  }
}
