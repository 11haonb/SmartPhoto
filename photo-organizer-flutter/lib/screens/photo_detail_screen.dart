import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:photo_organizer/models/models.dart';
import 'package:photo_organizer/services/api_service.dart';
import 'package:photo_organizer/widgets/quality_badge.dart';

class PhotoDetailScreen extends StatefulWidget {
  final String photoId;

  const PhotoDetailScreen({super.key, required this.photoId});

  @override
  State<PhotoDetailScreen> createState() => _PhotoDetailScreenState();
}

class _PhotoDetailScreenState extends State<PhotoDetailScreen> {
  PhotoDetailModel? _detail;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  Future<void> _loadDetail() async {
    try {
      final api = context.read<ApiService>();
      final detail = await api.getPhotoDetail(widget.photoId);
      if (mounted) {
        setState(() {
          _detail = detail;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _categoryLabel(String? category) {
    const labels = {
      'person': '人物',
      'landscape': '风景',
      'food': '美食',
      'document': '文档',
      'screenshot': '截图',
      'other': '其他',
    };
    return labels[category] ?? category ?? '未知';
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_detail == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: Text('加载失败')),
      );
    }

    final photo = _detail!.photo;
    final analysis = _detail!.analysis;

    return Scaffold(
      appBar: AppBar(
        title: Text(photo.originalFilename),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            onPressed: () async {
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('删除照片'),
                  content: const Text('确定要删除这张照片吗？'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('取消'),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('删除', style: TextStyle(color: Colors.red)),
                    ),
                  ],
                ),
              );
              if (confirmed == true && mounted) {
                final api = context.read<ApiService>();
                await api.deletePhoto(widget.photoId);
                if (mounted) context.pop();
              }
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Photo
            AspectRatio(
              aspectRatio: (photo.width ?? 4) / (photo.height ?? 3),
              child: photo.compressedUrl != null
                  ? Image.network(photo.compressedUrl!, fit: BoxFit.contain)
                  : photo.thumbnailUrl != null
                      ? Image.network(photo.thumbnailUrl!, fit: BoxFit.contain)
                      : Container(
                          color: Colors.grey.shade300,
                          child: const Icon(Icons.image, size: 64),
                        ),
            ),

            // Quality badges
            if (analysis != null)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    if (analysis.isBestInGroup)
                      const QualityBadge(label: '最佳照片', color: Colors.amber),
                    if (analysis.isBlurry)
                      const QualityBadge(label: '模糊', color: Colors.red),
                    if (analysis.isOverexposed)
                      const QualityBadge(label: '过曝', color: Colors.orange),
                    if (analysis.isUnderexposed)
                      const QualityBadge(label: '欠曝', color: Colors.blue),
                    if (analysis.isScreenshot)
                      const QualityBadge(label: '截图', color: const Color(0xFF0891B2)),
                  ],
                ),
              ),

            // Info sections
            _InfoSection(title: '基本信息', items: [
              _InfoRow('文件名', photo.originalFilename),
              _InfoRow('尺寸', '${photo.width ?? "-"} × ${photo.height ?? "-"}'),
              _InfoRow('大小', _formatFileSize(photo.fileSize)),
              _InfoRow('格式', photo.mimeType),
              if (photo.takenAt != null)
                _InfoRow('拍摄时间', photo.takenAt.toString().substring(0, 19)),
              if (photo.cameraModel != null)
                _InfoRow('相机', photo.cameraModel!),
              if (photo.gpsLatitude != null)
                _InfoRow('位置', '${photo.gpsLatitude!.toStringAsFixed(4)}, ${photo.gpsLongitude?.toStringAsFixed(4)}'),
            ]),

            if (analysis != null)
              _InfoSection(title: 'AI 分析', items: [
                _InfoRow('分类', _categoryLabel(analysis.category)),
                if (analysis.subCategory != null)
                  _InfoRow('子分类', analysis.subCategory!),
                if (analysis.confidence != null)
                  _InfoRow('置信度', '${(analysis.confidence! * 100).toInt()}%'),
                if (analysis.qualityScore != null)
                  _InfoRow('质量评分', '${(analysis.qualityScore! * 100).toInt()}/100'),
                if (analysis.similarityGroup != null)
                  _InfoRow('相似组', analysis.similarityGroup!),
              ]),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  String _formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / 1024 / 1024).toStringAsFixed(1)} MB';
  }
}

class _InfoSection extends StatelessWidget {
  final String title;
  final List<_InfoRow> items;

  const _InfoSection({required this.title, required this.items});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),
              ...items.map((item) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        SizedBox(
                          width: 80,
                          child: Text(
                            item.label,
                            style: TextStyle(color: Colors.grey.shade600),
                          ),
                        ),
                        Expanded(child: Text(item.value)),
                      ],
                    ),
                  )),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoRow {
  final String label;
  final String value;
  const _InfoRow(this.label, this.value);
}
