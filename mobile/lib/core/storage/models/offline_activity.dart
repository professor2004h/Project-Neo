import 'package:hive/hive.dart';

part 'offline_activity.g.dart';

@HiveType(typeId: 2)
class OfflineActivity extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String userId;

  @HiveField(2)
  final String type; // question, exercise, chat, etc.

  @HiveField(3)
  final String subject;

  @HiveField(4)
  final Map<String, dynamic> activityData;

  @HiveField(5)
  final DateTime createdAt;

  @HiveField(6)
  final DateTime? completedAt;

  @HiveField(7)
  final bool isSynced;

  @HiveField(8)
  final Map<String, dynamic> performanceData;

  @HiveField(9)
  final List<String> attachments;

  @HiveField(10)
  final Map<String, dynamic> metadata;

  OfflineActivity({
    required this.id,
    required this.userId,
    required this.type,
    required this.subject,
    required this.activityData,
    required this.createdAt,
    this.completedAt,
    this.isSynced = false,
    this.performanceData = const {},
    this.attachments = const [],
    this.metadata = const {},
  });

  OfflineActivity copyWith({
    String? id,
    String? userId,
    String? type,
    String? subject,
    Map<String, dynamic>? activityData,
    DateTime? createdAt,
    DateTime? completedAt,
    bool? isSynced,
    Map<String, dynamic>? performanceData,
    List<String>? attachments,
    Map<String, dynamic>? metadata,
  }) {
    return OfflineActivity(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      type: type ?? this.type,
      subject: subject ?? this.subject,
      activityData: activityData ?? this.activityData,
      createdAt: createdAt ?? this.createdAt,
      completedAt: completedAt ?? this.completedAt,
      isSynced: isSynced ?? this.isSynced,
      performanceData: performanceData ?? this.performanceData,
      attachments: attachments ?? this.attachments,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Mark activity as completed
  OfflineActivity completed() {
    return copyWith(
      completedAt: DateTime.now(),
    );
  }

  /// Mark activity as synced
  OfflineActivity synced() {
    return copyWith(isSynced: true);
  }

  /// Check if activity is completed
  bool get isCompleted => completedAt != null;

  /// Get duration of activity (if completed)
  Duration? get duration {
    if (completedAt == null) return null;
    return completedAt!.difference(createdAt);
  }

  /// Check if activity needs sync
  bool get needsSync => !isSynced;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'userId': userId,
      'type': type,
      'subject': subject,
      'activityData': activityData,
      'createdAt': createdAt.toIso8601String(),
      'completedAt': completedAt?.toIso8601String(),
      'isSynced': isSynced,
      'performanceData': performanceData,
      'attachments': attachments,
      'metadata': metadata,
    };
  }

  factory OfflineActivity.fromJson(Map<String, dynamic> json) {
    return OfflineActivity(
      id: json['id'] as String,
      userId: json['userId'] as String,
      type: json['type'] as String,
      subject: json['subject'] as String,
      activityData: Map<String, dynamic>.from(json['activityData'] as Map),
      createdAt: DateTime.parse(json['createdAt'] as String),
      completedAt: json['completedAt'] != null 
          ? DateTime.parse(json['completedAt'] as String) 
          : null,
      isSynced: json['isSynced'] as bool? ?? false,
      performanceData: Map<String, dynamic>.from(json['performanceData'] as Map? ?? {}),
      attachments: List<String>.from(json['attachments'] as List? ?? []),
      metadata: Map<String, dynamic>.from(json['metadata'] as Map? ?? {}),
    );
  }

  @override
  String toString() {
    return 'OfflineActivity(id: $id, type: $type, subject: $subject, isCompleted: $isCompleted, isSynced: $isSynced)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is OfflineActivity &&
        other.id == id &&
        other.userId == userId &&
        other.type == type &&
        other.subject == subject;
  }

  @override
  int get hashCode {
    return id.hashCode ^ userId.hashCode ^ type.hashCode ^ subject.hashCode;
  }
}