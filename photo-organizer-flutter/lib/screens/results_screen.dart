import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:photo_organizer/models/models.dart';
import 'package:photo_organizer/services/api_service.dart';
import 'package:photo_organizer/widgets/photo_grid.dart';
import 'package:photo_organizer/widgets/quality_badge.dart';
import 'package:photo_organizer/widgets/category_tab.dart';

class ResultsScreen extends StatefulWidget {
  final String taskId;

  const ResultsScreen({super.key, required this.taskId});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  OrganizeResultsModel? _results;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadResults();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadResults() async {
    try {
      final api = context.read<ApiService>();
      final results = await api.getOrganizeResults(widget.taskId);
      if (mounted) {
        setState(() {
          _results = results;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('加载结果失败: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('整理结果'),
        leading: IconButton(
          icon: const Icon(Icons.home),
          onPressed: () => context.go('/'),
        ),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '时间线'),
            Tab(text: '分类'),
            Tab(text: '问题图'),
            Tab(text: '最佳'),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _results == null
              ? const Center(child: Text('无法加载结果'))
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildTimeline(),
                    _buildCategories(),
                    _buildInvalidPhotos(),
                    _buildBestPhotos(),
                  ],
                ),
    );
  }

  Widget _buildTimeline() {
    final timeline = _results!.timeline;
    if (timeline.isEmpty) {
      return const Center(child: Text('暂无照片'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: timeline.length,
      itemBuilder: (context, index) {
        final group = timeline[index];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(
                group.date,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ),
            PhotoGrid(
              photos: group.photos.map((p) => p.thumbnailUrl ?? '').toList(),
              isLocalPaths: false,
              shrinkWrap: true,
              onTap: (i) => context.go('/photo/${group.photos[i].id}'),
            ),
            const Divider(height: 24),
          ],
        );
      },
    );
  }

  Widget _buildCategories() {
    final categories = _results!.categories;
    if (categories.isEmpty) {
      return const Center(child: Text('暂无分类结果'));
    }

    return CategoryTab(
      categories: categories,
      onPhotoTap: (photoId) => context.go('/photo/$photoId'),
    );
  }

  Widget _buildInvalidPhotos() {
    final invalid = _results!.invalidPhotos;
    if (invalid.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle, size: 64, color: Colors.green.shade400),
            const SizedBox(height: 16),
            const Text('所有照片质量正常!'),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: invalid.length,
      itemBuilder: (context, index) {
        final detail = invalid[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            leading: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: detail.photo.thumbnailUrl != null
                  ? Image.network(
                      detail.photo.thumbnailUrl!,
                      width: 60,
                      height: 60,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      width: 60,
                      height: 60,
                      color: Colors.grey.shade300,
                      child: const Icon(Icons.image),
                    ),
            ),
            title: Text(detail.photo.originalFilename),
            subtitle: Wrap(
              spacing: 4,
              children: [
                if (detail.analysis?.isBlurry == true)
                  const QualityBadge(label: '模糊', color: Colors.red),
                if (detail.analysis?.isOverexposed == true)
                  const QualityBadge(label: '过曝', color: Colors.orange),
                if (detail.analysis?.isUnderexposed == true)
                  const QualityBadge(label: '欠曝', color: Colors.blue),
                if (detail.analysis?.isScreenshot == true)
                  const QualityBadge(label: '截图', color: Colors.purple),
              ],
            ),
            onTap: () => context.go('/photo/${detail.photo.id}'),
          ),
        );
      },
    );
  }

  Widget _buildBestPhotos() {
    final groups = _results!.similarityGroups;
    if (groups.isEmpty) {
      return const Center(child: Text('未发现相似照片组'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: groups.length,
      itemBuilder: (context, index) {
        final group = groups[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 16),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '相似组 ${index + 1} (${group.photos.length} 张)',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 100,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: group.photos.length,
                    itemBuilder: (context, pi) {
                      final photo = group.photos[pi];
                      final isBest = photo.photo.id == group.bestPhotoId;
                      return GestureDetector(
                        onTap: () => context.go('/photo/${photo.photo.id}'),
                        child: Container(
                          width: 100,
                          margin: const EdgeInsets.only(right: 8),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(8),
                            border: isBest
                                ? Border.all(color: Colors.amber, width: 3)
                                : null,
                          ),
                          child: Stack(
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(isBest ? 5 : 8),
                                child: photo.photo.thumbnailUrl != null
                                    ? Image.network(
                                        photo.photo.thumbnailUrl!,
                                        width: 100,
                                        height: 100,
                                        fit: BoxFit.cover,
                                      )
                                    : Container(
                                        color: Colors.grey.shade300,
                                        child: const Icon(Icons.image),
                                      ),
                              ),
                              if (isBest)
                                Positioned(
                                  top: 4,
                                  right: 4,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 6,
                                      vertical: 2,
                                    ),
                                    decoration: BoxDecoration(
                                      color: Colors.amber,
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: const Text(
                                      '最佳',
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
