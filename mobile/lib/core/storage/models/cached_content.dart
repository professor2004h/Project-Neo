import 'package:hive/hive.dart';

part 'cached_content.g.dart';

@HiveType(typeId: 1)
class CachedContent extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  final String type; // lesson, exercise, explanation, etc.

  @HiveField(2)
  final String subject;

  @HiveField(3)
  final int gradeLevel;

  @HiveField(4)
  final String title;

  @HiveField(5)
  final Map<String, dynamic> content;

  @HiveField(6)
  final DateTime cachedAt;

  @HiveField(7)
  final DateTime? expiresAt;

  @HiveField(8)
  final int accessCount;

  @HiveField(9)
  final DateTime lastAccessed;

  @HiveField(10)
  final List<String> tags;

  @HiveField(11)
  final Map<String, dynamic> metadata;

  CachedContent({
    required this.id,
    required this.type,
    required this.subject,
    required this.gradeLevel,
    required this.title,
    required this.content,
    required this.cachedAt,
    this.expiresAt,
    this.accessCount = 0,
    required this.lastAccessed,
    this.tags = const [],
    this.metadata = const {},
  });

  CachedContent copyWith({
    String? id,
    String? type,
    String? subject,
    int? gradeLevel,
    String? title,
    Map<String, dynamic>? content,
    DateTime? cachedAt,
    DateTime? expiresAt,
    int? accessCount,
    DateTime? lastAccessed,
    List<String>? tags,
    Map<String, dynamic>? metadata,
  }) {
    return CachedContent(
      id: id ?? this.id,
      type: type ?? this.type,
      subject: subject ?? this.subject,
      gradeLevel: gradeLevel ?? this.gradeLevel,
      title: title ?? this.title,
      content: content ?? this.content,
      cachedAt: cachedAt ?? this.cachedAt,
      expiresAt: expiresAt ?? this.expiresAt,
      accessCount: accessCount ?? this.accessCount,
      lastAccessed: lastAccessed ?? this.lastAccessed,
      tags: tags ?? this.tags,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Check if content is expired
  bool get isExpired {
    if (expiresAt == null) return false;
    return DateTime.now().isAfter(expiresAt!);
  }

  /// Check if content is fresh (cached within last hour)
  bool get isFresh {
    final oneHourAgo = DateTime.now().subtract(const Duration(hours: 1));
    return cachedAt.isAfter(oneHourAgo);
  }

  /// Increment access count and update last accessed time
  CachedContent accessed() {
    return copyWith(
      accessCount: accessCount + 1,
      lastAccessed: DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type,
      'subject': subject,
      'gradeLevel': gradeLevel,
      'title': title,
      'content': content,
      'cachedAt': cachedAt.toIso8601String(),
      'expiresAt': expiresAt?.toIso8601String(),
      'accessCount': accessCount,
      'lastAccessed': lastAccessed.toIso8601String(),
      'tags': tags,
      'metadata': metadata,
    };
  }

  factory CachedContent.fromJson(Map<String, dynamic> json) {
    return CachedContent(
      id: json['id'] as String,
      type: json['type'] as String,
      subject: json['subject'] as String,
      gradeLevel: json['gradeLevel'] as int,
      title: json['title'] as String,
      content: Map<String, dynamic>.from(json['content'] as Map),
      cachedAt: DateTime.parse(json['cachedAt'] as String),
      expiresAt: json['expiresAt'] != null 
          ? DateTime.parse(json['expiresAt'] as String) 
          : null,
      accessCount: json['accessCount'] as int? ?? 0,
      lastAccessed: DateTime.parse(json['lastAccessed'] as String),
      tags: List<String>.from(json['tags'] as List? ?? []),
      metadata: Map<String, dynamic>.from(json['metadata'] as Map? ?? {}),
    );
  }

  @override
  String toString() {
    return 'CachedContent(id: $id, type: $type, subject: $subject, title: $title)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is CachedContent &&
        other.id == id &&
        other.type == type &&
        other.subject == subject &&
        other.gradeLevel == gradeLevel;
  }

  @override
  int get hashCode {
    return id.hashCode ^ type.hashCode ^ subject.hashCode ^ gradeLevel.hashCode;
  }
}