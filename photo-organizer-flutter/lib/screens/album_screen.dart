import 'dart:io';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:photo_organizer/services/api_service.dart';
import 'package:photo_organizer/widgets/photo_grid.dart';

class AlbumScreen extends StatefulWidget {
  const AlbumScreen({super.key});

  @override
  State<AlbumScreen> createState() => _AlbumScreenState();
}

class _AlbumScreenState extends State<AlbumScreen> {
  final List<XFile> _selectedPhotos = [];
  bool _uploading = false;
  double _uploadProgress = 0;
  int _uploadedCount = 0;

  Future<void> _pickPhotos() async {
    final picker = ImagePicker();
    final images = await picker.pickMultiImage(
      imageQuality: 90,
      maxWidth: 4096,
      maxHeight: 4096,
    );

    if (images.isNotEmpty) {
      setState(() {
        _selectedPhotos.addAll(images);
      });
    }
  }

  void _removePhoto(int index) {
    setState(() {
      _selectedPhotos.removeAt(index);
    });
  }

  Future<void> _startUploadAndOrganize() async {
    if (_selectedPhotos.isEmpty) return;

    setState(() {
      _uploading = true;
      _uploadProgress = 0;
      _uploadedCount = 0;
    });

    try {
      final api = context.read<ApiService>();

      // Create batch
      final batch = await api.createBatch(_selectedPhotos.length);
      final batchId = batch['id'] as String;

      // Upload photos with retry
      for (int i = 0; i < _selectedPhotos.length; i++) {
        final file = File(_selectedPhotos[i].path);
        int retries = 0;

        while (retries < 3) {
          try {
            await api.uploadPhoto(
              batchId,
              file,
              onProgress: (sent, total) {
                if (mounted) {
                  setState(() {
                    _uploadProgress =
                        (i + sent / total) / _selectedPhotos.length;
                  });
                }
              },
            );
            break;
          } catch (e) {
            retries++;
            if (retries >= 3) rethrow;
            await Future.delayed(
              Duration(milliseconds: 1000 * retries),
            );
          }
        }

        setState(() {
          _uploadedCount = i + 1;
          _uploadProgress = (i + 1) / _selectedPhotos.length;
        });
      }

      // Start organizing
      final result = await api.startOrganize(batchId);
      final taskId = result['task_id'] as String;

      if (mounted) {
        context.go('/organize/$taskId');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('上传失败: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _uploading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('选择照片'),
        actions: [
          if (_selectedPhotos.isNotEmpty && !_uploading)
            TextButton.icon(
              onPressed: _pickPhotos,
              icon: const Icon(Icons.add),
              label: const Text('继续添加'),
            ),
        ],
      ),
      body: _selectedPhotos.isEmpty
          ? _buildEmptyState()
          : _uploading
              ? _buildUploadProgress()
              : _buildPhotoGrid(),
      floatingActionButton: _selectedPhotos.isNotEmpty && !_uploading
          ? FloatingActionButton.extended(
              onPressed: _startUploadAndOrganize,
              icon: const Icon(Icons.auto_fix_high),
              label: Text('整理 ${_selectedPhotos.length} 张照片'),
            )
          : null,
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.add_photo_alternate_outlined,
            size: 80,
            color: Colors.grey.shade400,
          ),
          const SizedBox(height: 16),
          Text(
            '从相册中选择要整理的照片',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _pickPhotos,
            icon: const Icon(Icons.photo_library),
            label: const Text('选择照片'),
          ),
        ],
      ),
    );
  }

  Widget _buildUploadProgress() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 120,
              height: 120,
              child: CircularProgressIndicator(
                value: _uploadProgress,
                strokeWidth: 8,
                backgroundColor: Colors.grey.shade200,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              '${(_uploadProgress * 100).toInt()}%',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              '正在上传 $_uploadedCount / ${_selectedPhotos.length}',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 4),
            Text(
              '请勿关闭应用',
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPhotoGrid() {
    return PhotoGrid(
      photos: _selectedPhotos.map((xf) => xf.path).toList(),
      isLocalPaths: true,
      onRemove: _removePhoto,
    );
  }
}
