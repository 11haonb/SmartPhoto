import 'package:flutter/material.dart';
import 'package:photo_organizer/models/models.dart';
import 'package:photo_organizer/widgets/photo_grid.dart';

class CategoryTab extends StatefulWidget {
  final List<CategoryGroup> categories;
  final void Function(String photoId) onPhotoTap;

  const CategoryTab({
    super.key,
    required this.categories,
    required this.onPhotoTap,
  });

  @override
  State<CategoryTab> createState() => _CategoryTabState();
}

class _CategoryTabState extends State<CategoryTab> {
  int _selectedIndex = 0;

  static const _categoryIcons = {
    'person': Icons.person,
    'landscape': Icons.landscape,
    'food': Icons.restaurant,
    'document': Icons.description,
    'screenshot': Icons.screenshot,
    'other': Icons.image,
  };

  static const _categoryLabels = {
    'person': '人物',
    'landscape': '风景',
    'food': '美食',
    'document': '文档',
    'screenshot': '截图',
    'other': '其他',
  };

  @override
  Widget build(BuildContext context) {
    if (widget.categories.isEmpty) {
      return const Center(child: Text('暂无分类结果'));
    }

    return Column(
      children: [
        // Category chips
        SizedBox(
          height: 48,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            itemCount: widget.categories.length,
            itemBuilder: (context, index) {
              final cat = widget.categories[index];
              final isSelected = index == _selectedIndex;
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: FilterChip(
                  selected: isSelected,
                  onSelected: (_) => setState(() => _selectedIndex = index),
                  avatar: Icon(
                    _categoryIcons[cat.category] ?? Icons.image,
                    size: 18,
                  ),
                  label: Text(
                    '${_categoryLabels[cat.category] ?? cat.category} (${cat.count})',
                  ),
                ),
              );
            },
          ),
        ),
        // Photo grid for selected category
        Expanded(
          child: PhotoGrid(
            photos: widget.categories[_selectedIndex].photos
                .map((p) => p.thumbnailUrl ?? '')
                .toList(),
            isLocalPaths: false,
            onTap: (i) => widget.onPhotoTap(
              widget.categories[_selectedIndex].photos[i].id,
            ),
          ),
        ),
      ],
    );
  }
}
