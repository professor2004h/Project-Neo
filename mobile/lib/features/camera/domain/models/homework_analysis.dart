import 'package:equatable/equatable.dart';

/// Model for homework analysis results
class HomeworkAnalysis extends Equatable {
  final String id;
  final String imagePath;
  final String extractedText;
  final List<String> detectedQuestions;
  final String subject;
  final String gradeLevel;
  final DateTime analyzedAt;
  final Map<String, dynamic> metadata;

  const HomeworkAnalysis({
    required this.id,
    required this.imagePath,
    required this.extractedText,
    required this.detectedQuestions,
    required this.subject,
    required this.gradeLevel,
    required this.analyzedAt,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [
        id,
        imagePath,
        extractedText,
        detectedQuestions,
        subject,
        gradeLevel,
        analyzedAt,
        metadata,
      ];

  HomeworkAnalysis copyWith({
    String? id,
    String? imagePath,
    String? extractedText,
    List<String>? detectedQuestions,
    String? subject,
    String? gradeLevel,
    DateTime? analyzedAt,
    Map<String, dynamic>? metadata,
  }) {
    return HomeworkAnalysis(
      id: id ?? this.id,
      imagePath: imagePath ?? this.imagePath,
      extractedText: extractedText ?? this.extractedText,
      detectedQuestions: detectedQuestions ?? this.detectedQuestions,
      subject: subject ?? this.subject,
      gradeLevel: gradeLevel ?? this.gradeLevel,
      analyzedAt: analyzedAt ?? this.analyzedAt,
      metadata: metadata ?? this.metadata,
    );
  }
}

/// Camera capture result
class CaptureResult extends Equatable {
  final String imagePath;
  final DateTime capturedAt;
  final Map<String, dynamic> metadata;

  const CaptureResult({
    required this.imagePath,
    required this.capturedAt,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [imagePath, capturedAt, metadata];
}