import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:photo_organizer/models/models.dart';

class PhotoComparison extends StatelessWidget {
  final List<PhotoDetailModel> photos;
  final String? bestPhotoId;

  const PhotoComparison({
    super.key,
    required this.photos,
    this.bestPhotoId,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 200,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        itemCount: photos.length,
        itemBuilder: (context, index) {
          final detail = photos[index];
          final isBest = detail.photo.id == bestPhotoId;
          final score = detail.analysis?.qualityScore;

          return Container(
            width: 160,
            margin: const EdgeInsets.symmetric(horizontal: 4),
            child: Column(
              children: [
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      border: isBest
                          ? Border.all(color: Colors.amber, width: 3)
                          : Border.all(color: Colors.grey.shade300),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(isBest ? 9 : 12),
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          detail.photo.thumbnailUrl != null
                              ? CachedNetworkImage(
                                  imageUrl: detail.photo.thumbnailUrl!,
                                  fit: BoxFit.cover,
                                )
                              : Container(
                                  color: Colors.grey.shade200,
                                  child: const Icon(Icons.image),
                                ),
                          if (isBest)
                            Positioned(
                              top: 8,
                              left: 8,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.amber,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.star, size: 14),
                                    SizedBox(width: 2),
                                    Text(
                                      '最佳',
                                      style: TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                if (score != null)
                  Text(
                    '质量: ${(score * 100).toInt()}/100',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                      fontWeight: isBest ? FontWeight.bold : FontWeight.normal,
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
