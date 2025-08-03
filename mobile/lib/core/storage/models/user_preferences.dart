import 'package:hive/hive.dart';

part 'user_preferences.g.dart';

@HiveType(typeId: 0)
class UserPreferences extends HiveObject {
  @HiveField(0)
  final String userId;

  @HiveField(1)
  final String childName;

  @HiveField(2)
  final int age;

  @HiveField(3)
  final int gradeLevel;

  @HiveField(4)
  final String preferredLanguage;

  @HiveField(5)
  final String learningStyle;

  @HiveField(6)
  final List<String> favoriteSubjects;

  @HiveField(7)
  final Map<String, dynamic> difficultySettings;

  @HiveField(8)
  final bool soundEnabled;

  @HiveField(9)
  final bool notificationsEnabled;

  @HiveField(10)
  final bool parentalControlsEnabled;

  @HiveField(11)
  final DateTime lastUpdated;

  @HiveField(12)
  final Map<String, dynamic> customSettings;

  UserPreferences({
    required this.userId,
    required this.childName,
    required this.age,
    required this.gradeLevel,
    this.preferredLanguage = 'en',
    this.learningStyle = 'visual',
    this.favoriteSubjects = const [],
    this.difficultySettings = const {},
    this.soundEnabled = true,
    this.notificationsEnabled = true,
    this.parentalControlsEnabled = true,
    required this.lastUpdated,
    this.customSettings = const {},
  });

  UserPreferences copyWith({
    String? userId,
    String? childName,
    int? age,
    int? gradeLevel,
    String? preferredLanguage,
    String? learningStyle,
    List<String>? favoriteSubjects,
    Map<String, dynamic>? difficultySettings,
    bool? soundEnabled,
    bool? notificationsEnabled,
    bool? parentalControlsEnabled,
    DateTime? lastUpdated,
    Map<String, dynamic>? customSettings,
  }) {
    return UserPreferences(
      userId: userId ?? this.userId,
      childName: childName ?? this.childName,
      age: age ?? this.age,
      gradeLevel: gradeLevel ?? this.gradeLevel,
      preferredLanguage: preferredLanguage ?? this.preferredLanguage,
      learningStyle: learningStyle ?? this.learningStyle,
      favoriteSubjects: favoriteSubjects ?? this.favoriteSubjects,
      difficultySettings: difficultySettings ?? this.difficultySettings,
      soundEnabled: soundEnabled ?? this.soundEnabled,
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      parentalControlsEnabled: parentalControlsEnabled ?? this.parentalControlsEnabled,
      lastUpdated: lastUpdated ?? this.lastUpdated,
      customSettings: customSettings ?? this.customSettings,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'userId': userId,
      'childName': childName,
      'age': age,
      'gradeLevel': gradeLevel,
      'preferredLanguage': preferredLanguage,
      'learningStyle': learningStyle,
      'favoriteSubjects': favoriteSubjects,
      'difficultySettings': difficultySettings,
      'soundEnabled': soundEnabled,
      'notificationsEnabled': notificationsEnabled,
      'parentalControlsEnabled': parentalControlsEnabled,
      'lastUpdated': lastUpdated.toIso8601String(),
      'customSettings': customSettings,
    };
  }

  factory UserPreferences.fromJson(Map<String, dynamic> json) {
    return UserPreferences(
      userId: json['userId'] as String,
      childName: json['childName'] as String,
      age: json['age'] as int,
      gradeLevel: json['gradeLevel'] as int,
      preferredLanguage: json['preferredLanguage'] as String? ?? 'en',
      learningStyle: json['learningStyle'] as String? ?? 'visual',
      favoriteSubjects: List<String>.from(json['favoriteSubjects'] as List? ?? []),
      difficultySettings: Map<String, dynamic>.from(json['difficultySettings'] as Map? ?? {}),
      soundEnabled: json['soundEnabled'] as bool? ?? true,
      notificationsEnabled: json['notificationsEnabled'] as bool? ?? true,
      parentalControlsEnabled: json['parentalControlsEnabled'] as bool? ?? true,
      lastUpdated: DateTime.parse(json['lastUpdated'] as String),
      customSettings: Map<String, dynamic>.from(json['customSettings'] as Map? ?? {}),
    );
  }

  @override
  String toString() {
    return 'UserPreferences(userId: $userId, childName: $childName, age: $age, gradeLevel: $gradeLevel)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is UserPreferences &&
        other.userId == userId &&
        other.childName == childName &&
        other.age == age &&
        other.gradeLevel == gradeLevel &&
        other.preferredLanguage == preferredLanguage &&
        other.learningStyle == learningStyle;
  }

  @override
  int get hashCode {
    return userId.hashCode ^
        childName.hashCode ^
        age.hashCode ^
        gradeLevel.hashCode ^
        preferredLanguage.hashCode ^
        learningStyle.hashCode;
  }
}