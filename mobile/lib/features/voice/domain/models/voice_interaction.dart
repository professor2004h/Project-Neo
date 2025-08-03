import 'package:equatable/equatable.dart';

/// Voice interaction session
class VoiceSession extends Equatable {
  final String id;
  final String userId;
  final DateTime startedAt;
  final DateTime? endedAt;
  final List<VoiceMessage> messages;
  final VoiceSessionStatus status;
  final Map<String, dynamic> metadata;

  const VoiceSession({
    required this.id,
    required this.userId,
    required this.startedAt,
    this.endedAt,
    this.messages = const [],
    this.status = VoiceSessionStatus.active,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [
        id,
        userId,
        startedAt,
        endedAt,
        messages,
        status,
        metadata,
      ];

  VoiceSession copyWith({
    String? id,
    String? userId,
    DateTime? startedAt,
    DateTime? endedAt,
    List<VoiceMessage>? messages,
    VoiceSessionStatus? status,
    Map<String, dynamic>? metadata,
  }) {
    return VoiceSession(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      startedAt: startedAt ?? this.startedAt,
      endedAt: endedAt ?? this.endedAt,
      messages: messages ?? this.messages,
      status: status ?? this.status,
      metadata: metadata ?? this.metadata,
    );
  }
}

/// Voice message in a session
class VoiceMessage extends Equatable {
  final String id;
  final String sessionId;
  final VoiceMessageType type;
  final String content;
  final String? audioPath;
  final DateTime timestamp;
  final double? confidence;
  final Map<String, dynamic> metadata;

  const VoiceMessage({
    required this.id,
    required this.sessionId,
    required this.type,
    required this.content,
    this.audioPath,
    required this.timestamp,
    this.confidence,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [
        id,
        sessionId,
        type,
        content,
        audioPath,
        timestamp,
        confidence,
        metadata,
      ];
}

/// Voice session status
enum VoiceSessionStatus {
  active,
  paused,
  completed,
  error,
}

/// Voice message type
enum VoiceMessageType {
  userSpeech,
  tutorResponse,
  systemMessage,
}

/// Speech recognition result
class SpeechResult extends Equatable {
  final String text;
  final double confidence;
  final bool isComplete;
  final DateTime timestamp;

  const SpeechResult({
    required this.text,
    required this.confidence,
    required this.isComplete,
    required this.timestamp,
  });

  @override
  List<Object?> get props => [text, confidence, isComplete, timestamp];
}

/// Text-to-speech request
class TTSRequest extends Equatable {
  final String text;
  final String language;
  final double rate;
  final double pitch;
  final double volume;

  const TTSRequest({
    required this.text,
    this.language = 'en-US',
    this.rate = 0.5,
    this.pitch = 1.0,
    this.volume = 1.0,
  });

  @override
  List<Object?> get props => [text, language, rate, pitch, volume];
}