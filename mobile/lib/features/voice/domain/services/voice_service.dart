import 'dart:async';
import 'dart:io';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:permission_handler/permission_handler.dart';
import '../models/voice_interaction.dart';

/// Service for voice interactions (speech-to-text and text-to-speech)
class VoiceService {
  final SpeechToText _speechToText = SpeechToText();
  final FlutterTts _flutterTts = FlutterTts();
  
  bool _isInitialized = false;
  bool _isListening = false;
  bool _isSpeaking = false;
  
  final StreamController<SpeechResult> _speechController = StreamController<SpeechResult>.broadcast();
  final StreamController<bool> _listeningController = StreamController<bool>.broadcast();
  final StreamController<bool> _speakingController = StreamController<bool>.broadcast();

  /// Stream of speech recognition results
  Stream<SpeechResult> get speechStream => _speechController.stream;
  
  /// Stream of listening status
  Stream<bool> get listeningStream => _listeningController.stream;
  
  /// Stream of speaking status
  Stream<bool> get speakingStream => _speakingController.stream;

  /// Check if service is initialized
  bool get isInitialized => _isInitialized;
  
  /// Check if currently listening
  bool get isListening => _isListening;
  
  /// Check if currently speaking
  bool get isSpeaking => _isSpeaking;

  /// Initialize voice service
  Future<bool> initialize() async {
    try {
      // Request microphone permission
      final micPermission = await Permission.microphone.request();
      if (!micPermission.isGranted) {
        throw Exception('Microphone permission denied');
      }

      // Initialize speech-to-text
      final speechAvailable = await _speechToText.initialize(
        onError: _onSpeechError,
        onStatus: _onSpeechStatus,
      );

      if (!speechAvailable) {
        throw Exception('Speech recognition not available');
      }

      // Initialize text-to-speech
      await _initializeTTS();

      _isInitialized = true;
      return true;
    } catch (e) {
      print('Voice service initialization error: $e');
      return false;
    }
  }

  /// Initialize TTS settings
  Future<void> _initializeTTS() async {
    await _flutterTts.setLanguage('en-US');
    await _flutterTts.setSpeechRate(0.5);
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);

    // Set up TTS callbacks
    _flutterTts.setStartHandler(() {
      _isSpeaking = true;
      _speakingController.add(true);
    });

    _flutterTts.setCompletionHandler(() {
      _isSpeaking = false;
      _speakingController.add(false);
    });

    _flutterTts.setErrorHandler((msg) {
      _isSpeaking = false;
      _speakingController.add(false);
      print('TTS Error: $msg');
    });

    // Platform-specific settings
    if (Platform.isAndroid) {
      await _flutterTts.setEngine('com.google.android.tts');
    }
  }

  /// Start listening for speech
  Future<void> startListening({
    String localeId = 'en_US',
    Duration timeout = const Duration(seconds: 30),
  }) async {
    if (!_isInitialized) {
      throw Exception('Voice service not initialized');
    }

    if (_isListening) {
      await stopListening();
    }

    await _speechToText.listen(
      onResult: _onSpeechResult,
      localeId: localeId,
      listenFor: timeout,
      pauseFor: const Duration(seconds: 3),
      partialResults: true,
      cancelOnError: true,
    );

    _isListening = true;
    _listeningController.add(true);
  }

  /// Stop listening for speech
  Future<void> stopListening() async {
    if (_isListening) {
      await _speechToText.stop();
      _isListening = false;
      _listeningController.add(false);
    }
  }

  /// Speak text using TTS
  Future<void> speak(TTSRequest request) async {
    if (!_isInitialized) {
      throw Exception('Voice service not initialized');
    }

    if (_isSpeaking) {
      await stopSpeaking();
    }

    // Configure TTS settings
    await _flutterTts.setLanguage(request.language);
    await _flutterTts.setSpeechRate(request.rate);
    await _flutterTts.setPitch(request.pitch);
    await _flutterTts.setVolume(request.volume);

    // Speak the text
    await _flutterTts.speak(request.text);
  }

  /// Stop current speech
  Future<void> stopSpeaking() async {
    if (_isSpeaking) {
      await _flutterTts.stop();
      _isSpeaking = false;
      _speakingController.add(false);
    }
  }

  /// Get available speech recognition locales
  Future<List<LocaleName>> getAvailableLocales() async {
    if (!_isInitialized) return [];
    return await _speechToText.locales();
  }

  /// Get available TTS languages
  Future<List<dynamic>> getAvailableTTSLanguages() async {
    return await _flutterTts.getLanguages;
  }

  /// Handle speech recognition results
  void _onSpeechResult(result) {
    final speechResult = SpeechResult(
      text: result.recognizedWords,
      confidence: result.confidence,
      isComplete: result.finalResult,
      timestamp: DateTime.now(),
    );
    
    _speechController.add(speechResult);
  }

  /// Handle speech recognition errors
  void _onSpeechError(error) {
    print('Speech recognition error: $error');
    _isListening = false;
    _listeningController.add(false);
  }

  /// Handle speech recognition status changes
  void _onSpeechStatus(status) {
    print('Speech recognition status: $status');
    
    if (status == 'done' || status == 'notListening') {
      _isListening = false;
      _listeningController.add(false);
    }
  }

  /// Create a voice session
  VoiceSession createSession(String userId) {
    return VoiceSession(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      userId: userId,
      startedAt: DateTime.now(),
      status: VoiceSessionStatus.active,
    );
  }

  /// Add message to session
  VoiceSession addMessageToSession(
    VoiceSession session,
    VoiceMessageType type,
    String content, {
    String? audioPath,
    double? confidence,
  }) {
    final message = VoiceMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      sessionId: session.id,
      type: type,
      content: content,
      audioPath: audioPath,
      timestamp: DateTime.now(),
      confidence: confidence,
    );

    return session.copyWith(
      messages: [...session.messages, message],
    );
  }

  /// Dispose resources
  void dispose() {
    _speechController.close();
    _listeningController.close();
    _speakingController.close();
    _speechToText.cancel();
    _flutterTts.stop();
  }
}