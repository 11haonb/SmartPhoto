class PhotoModel {
  final String id;
  final String originalFilename;
  final String? thumbnailUrl;
  final String? compressedUrl;
  final String mimeType;
  final int fileSize;
  final int? width;
  final int? height;
  final DateTime? takenAt;
  final String? cameraModel;
  final double? gpsLatitude;
  final double? gpsLongitude;
  final DateTime createdAt;

  const PhotoModel({
    required this.id,
    required this.originalFilename,
    this.thumbnailUrl,
    this.compressedUrl,
    required this.mimeType,
    required this.fileSize,
    this.width,
    this.height,
    this.takenAt,
    this.cameraModel,
    this.gpsLatitude,
    this.gpsLongitude,
    required this.createdAt,
  });

  factory PhotoModel.fromJson(Map<String, dynamic> json) {
    return PhotoModel(
      id: json['id'],
      originalFilename: json['original_filename'],
      thumbnailUrl: json['thumbnail_url'],
      compressedUrl: json['compressed_url'],
      mimeType: json['mime_type'],
      fileSize: json['file_size'],
      width: json['width'],
      height: json['height'],
      takenAt: json['taken_at'] != null ? DateTime.parse(json['taken_at']) : null,
      cameraModel: json['camera_model'],
      gpsLatitude: json['gps_latitude']?.toDouble(),
      gpsLongitude: json['gps_longitude']?.toDouble(),
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class PhotoAnalysisModel {
  final String photoId;
  final String? category;
  final String? subCategory;
  final double? confidence;
  final double? qualityScore;
  final bool isBlurry;
  final bool isOverexposed;
  final bool isUnderexposed;
  final bool isScreenshot;
  final bool isInvalid;
  final String? invalidReason;
  final String? similarityGroup;
  final bool isBestInGroup;

  const PhotoAnalysisModel({
    required this.photoId,
    this.category,
    this.subCategory,
    this.confidence,
    this.qualityScore,
    required this.isBlurry,
    required this.isOverexposed,
    required this.isUnderexposed,
    required this.isScreenshot,
    required this.isInvalid,
    this.invalidReason,
    this.similarityGroup,
    required this.isBestInGroup,
  });

  factory PhotoAnalysisModel.fromJson(Map<String, dynamic> json) {
    return PhotoAnalysisModel(
      photoId: json['photo_id'],
      category: json['category'],
      subCategory: json['sub_category'],
      confidence: json['confidence']?.toDouble(),
      qualityScore: json['quality_score']?.toDouble(),
      isBlurry: json['is_blurry'] ?? false,
      isOverexposed: json['is_overexposed'] ?? false,
      isUnderexposed: json['is_underexposed'] ?? false,
      isScreenshot: json['is_screenshot'] ?? false,
      isInvalid: json['is_invalid'] ?? false,
      invalidReason: json['invalid_reason'],
      similarityGroup: json['similarity_group'],
      isBestInGroup: json['is_best_in_group'] ?? false,
    );
  }
}

class ProcessingTaskModel {
  final String id;
  final String status;
  final int currentStage;
  final int totalStages;
  final String? currentStageName;
  final int progressPercent;
  final int photosProcessed;
  final int photosTotal;
  final String? errorMessage;

  const ProcessingTaskModel({
    required this.id,
    required this.status,
    required this.currentStage,
    required this.totalStages,
    this.currentStageName,
    required this.progressPercent,
    required this.photosProcessed,
    required this.photosTotal,
    this.errorMessage,
  });

  factory ProcessingTaskModel.fromJson(Map<String, dynamic> json) {
    return ProcessingTaskModel(
      id: json['id'],
      status: json['status'],
      currentStage: json['current_stage'],
      totalStages: json['total_stages'],
      currentStageName: json['current_stage_name'],
      progressPercent: json['progress_percent'],
      photosProcessed: json['photos_processed'],
      photosTotal: json['photos_total'],
      errorMessage: json['error_message'],
    );
  }
}

class OrganizeResultsModel {
  final String taskId;
  final List<TimelineGroup> timeline;
  final List<CategoryGroup> categories;
  final List<PhotoDetailModel> invalidPhotos;
  final List<SimilarityGroupModel> similarityGroups;

  const OrganizeResultsModel({
    required this.taskId,
    required this.timeline,
    required this.categories,
    required this.invalidPhotos,
    required this.similarityGroups,
  });

  factory OrganizeResultsModel.fromJson(Map<String, dynamic> json) {
    return OrganizeResultsModel(
      taskId: json['task_id'],
      timeline: (json['timeline'] as List)
          .map((e) => TimelineGroup.fromJson(e))
          .toList(),
      categories: (json['categories'] as List)
          .map((e) => CategoryGroup.fromJson(e))
          .toList(),
      invalidPhotos: (json['invalid_photos'] as List)
          .map((e) => PhotoDetailModel.fromJson(e))
          .toList(),
      similarityGroups: (json['similarity_groups'] as List)
          .map((e) => SimilarityGroupModel.fromJson(e))
          .toList(),
    );
  }
}

class TimelineGroup {
  final String date;
  final List<PhotoModel> photos;

  const TimelineGroup({required this.date, required this.photos});

  factory TimelineGroup.fromJson(Map<String, dynamic> json) {
    return TimelineGroup(
      date: json['date'],
      photos: (json['photos'] as List)
          .map((e) => PhotoModel.fromJson(e))
          .toList(),
    );
  }
}

class CategoryGroup {
  final String category;
  final String? subCategory;
  final int count;
  final List<PhotoModel> photos;

  const CategoryGroup({
    required this.category,
    this.subCategory,
    required this.count,
    required this.photos,
  });

  factory CategoryGroup.fromJson(Map<String, dynamic> json) {
    return CategoryGroup(
      category: json['category'],
      subCategory: json['sub_category'],
      count: json['count'],
      photos: (json['photos'] as List)
          .map((e) => PhotoModel.fromJson(e))
          .toList(),
    );
  }
}

class SimilarityGroupModel {
  final String groupId;
  final List<PhotoDetailModel> photos;
  final String? bestPhotoId;

  const SimilarityGroupModel({
    required this.groupId,
    required this.photos,
    this.bestPhotoId,
  });

  factory SimilarityGroupModel.fromJson(Map<String, dynamic> json) {
    return SimilarityGroupModel(
      groupId: json['group_id'],
      photos: (json['photos'] as List)
          .map((e) => PhotoDetailModel.fromJson(e))
          .toList(),
      bestPhotoId: json['best_photo_id'],
    );
  }
}

class PhotoDetailModel {
  final PhotoModel photo;
  final PhotoAnalysisModel? analysis;

  const PhotoDetailModel({required this.photo, this.analysis});

  factory PhotoDetailModel.fromJson(Map<String, dynamic> json) {
    return PhotoDetailModel(
      photo: PhotoModel.fromJson(json['photo']),
      analysis: json['analysis'] != null
          ? PhotoAnalysisModel.fromJson(json['analysis'])
          : null,
    );
  }
}

class AIProviderModel {
  final String provider;
  final String name;
  final String description;
  final bool requiresApiKey;
  final String? freeTier;
  final String accuracy;

  const AIProviderModel({
    required this.provider,
    required this.name,
    required this.description,
    required this.requiresApiKey,
    this.freeTier,
    required this.accuracy,
  });

  factory AIProviderModel.fromJson(Map<String, dynamic> json) {
    return AIProviderModel(
      provider: json['provider'],
      name: json['name'],
      description: json['description'],
      requiresApiKey: json['requires_api_key'],
      freeTier: json['free_tier'],
      accuracy: json['accuracy'],
    );
  }
}
