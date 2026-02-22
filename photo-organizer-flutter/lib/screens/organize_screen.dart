import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:photo_organizer/models/models.dart';
import 'package:photo_organizer/services/api_service.dart';

class OrganizeScreen extends StatefulWidget {
  final String taskId;

  const OrganizeScreen({super.key, required this.taskId});

  @override
  State<OrganizeScreen> createState() => _OrganizeScreenState();
}

class _OrganizeScreenState extends State<OrganizeScreen> {
  Timer? _pollTimer;
  ProcessingTaskModel? _task;
  bool _error = false;

  static const _stageLabels = {
    1: 'EXIF 提取',
    2: '质量分析',
    3: '图片分类',
    4: '相似度分组',
    5: '最佳挑选',
  };

  @override
  void initState() {
    super.initState();
    _startPolling();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _startPolling() {
    _poll();
    _pollTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _poll(),
    );
  }

  Future<void> _poll() async {
    try {
      final api = context.read<ApiService>();
      final task = await api.getOrganizeStatus(widget.taskId);

      if (mounted) {
        setState(() {
          _task = task;
          _error = false;
        });

        if (task.status == 'completed') {
          _pollTimer?.cancel();
          await Future.delayed(const Duration(milliseconds: 500));
          if (mounted) context.go('/results/${widget.taskId}');
        } else if (task.status == 'failed') {
          _pollTimer?.cancel();
        }
      }
    } catch (e) {
      if (mounted) setState(() => _error = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('整理中'),
        automaticallyImplyLeading: false,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 40),
            // Progress circle
            Center(
              child: SizedBox(
                width: 160,
                height: 160,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 160,
                      height: 160,
                      child: CircularProgressIndicator(
                        value: (_task?.progressPercent ?? 0) / 100,
                        strokeWidth: 10,
                        backgroundColor: Colors.grey.shade200,
                      ),
                    ),
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '${_task?.progressPercent ?? 0}%',
                          style: theme.textTheme.headlineLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (_task?.currentStageName != null)
                          Text(
                            _task!.currentStageName!,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: Colors.grey,
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 40),
            // Stage progress
            ...List.generate(5, (index) {
              final stage = index + 1;
              final currentStage = _task?.currentStage ?? 0;
              final isActive = stage == currentStage;
              final isDone = stage < currentStage;

              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  children: [
                    _StageIndicator(
                      isDone: isDone,
                      isActive: isActive,
                      stage: stage,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _stageLabels[stage] ?? '',
                        style: TextStyle(
                          fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                          color: isDone
                              ? Colors.green
                              : isActive
                                  ? theme.colorScheme.primary
                                  : Colors.grey,
                        ),
                      ),
                    ),
                    if (isActive && _task != null)
                      Text(
                        '${_task!.photosProcessed}/${_task!.photosTotal}',
                        style: TextStyle(
                          color: Colors.grey.shade600,
                          fontSize: 13,
                        ),
                      ),
                    if (isDone)
                      const Icon(Icons.check, color: Colors.green, size: 20),
                  ],
                ),
              );
            }),
            const Spacer(),
            if (_task?.status == 'failed') ...[
              Card(
                color: Colors.red.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Icon(Icons.error_outline, color: Colors.red, size: 32),
                      const SizedBox(height: 8),
                      Text(
                        '整理失败',
                        style: TextStyle(
                          color: Colors.red.shade700,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (_task?.errorMessage != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          _task!.errorMessage!,
                          style: TextStyle(color: Colors.red.shade600, fontSize: 13),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.go('/album'),
                child: const Text('返回重试'),
              ),
            ],
            if (_error)
              const Text(
                '网络连接异常，正在重试...',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.orange),
              ),
          ],
        ),
      ),
    );
  }
}

class _StageIndicator extends StatelessWidget {
  final bool isDone;
  final bool isActive;
  final int stage;

  const _StageIndicator({
    required this.isDone,
    required this.isActive,
    required this.stage,
  });

  @override
  Widget build(BuildContext context) {
    if (isDone) {
      return Container(
        width: 28,
        height: 28,
        decoration: const BoxDecoration(
          color: Colors.green,
          shape: BoxShape.circle,
        ),
        child: const Icon(Icons.check, color: Colors.white, size: 16),
      );
    }

    return Container(
      width: 28,
      height: 28,
      decoration: BoxDecoration(
        color: isActive
            ? Theme.of(context).colorScheme.primary
            : Colors.grey.shade300,
        shape: BoxShape.circle,
      ),
      child: Center(
        child: isActive
            ? const SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : Text(
                '$stage',
                style: TextStyle(
                  color: isActive ? Colors.white : Colors.grey.shade600,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
      ),
    );
  }
}
