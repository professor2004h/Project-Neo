import 'dart:io';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import '../models/homework_analysis.dart';

/// Service for camera operations and image analysis
class CameraService {
  final ImagePicker _imagePicker = ImagePicker();
  final TextRecognizer _textRecognizer = TextRecognizer();
  
  List<CameraDescription>? _cameras;
  CameraController? _controller;

  /// Initialize camera service
  Future<void> initialize() async {
    _cameras = await availableCameras();
  }

  /// Get available cameras
  List<CameraDescription>? get cameras => _cameras;

  /// Initialize camera controller
  Future<CameraController?> initializeController({
    CameraDescription? camera,
    ResolutionPreset resolution = ResolutionPreset.high,
  }) async {
    if (_cameras == null || _cameras!.isEmpty) {
      throw Exception('No cameras available');
    }

    final selectedCamera = camera ?? _cameras!.first;
    _controller = CameraController(selectedCamera, resolution);
    
    await _controller!.initialize();
    return _controller;
  }

  /// Capture photo using camera
  Future<CaptureResult> capturePhoto() async {
    if (_controller == null || !_controller!.value.isInitialized) {
      throw Exception('Camera not initialized');
    }

    final XFile image = await _controller!.takePicture();
    
    return CaptureResult(
      imagePath: image.path,
      capturedAt: DateTime.now(),
      metadata: {
        'source': 'camera',
        'resolution': _controller!.value.previewSize?.toString(),
      },
    );
  }

  /// Pick image from gallery
  Future<CaptureResult?> pickFromGallery() async {
    final XFile? image = await _imagePicker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1920,
      maxHeight: 1080,
      imageQuality: 85,
    );

    if (image == null) return null;

    return CaptureResult(
      imagePath: image.path,
      capturedAt: DateTime.now(),
      metadata: {
        'source': 'gallery',
      },
    );
  }

  /// Extract text from image using ML Kit
  Future<String> extractTextFromImage(String imagePath) async {
    final inputImage = InputImage.fromFilePath(imagePath);
    final RecognizedText recognizedText = await _textRecognizer.processImage(inputImage);
    
    return recognizedText.text;
  }

  /// Analyze homework image
  Future<HomeworkAnalysis> analyzeHomework(String imagePath) async {
    final extractedText = await extractTextFromImage(imagePath);
    
    // Simple question detection (can be enhanced with ML)
    final questions = _detectQuestions(extractedText);
    final subject = _detectSubject(extractedText);
    final gradeLevel = _detectGradeLevel(extractedText);

    return HomeworkAnalysis(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      imagePath: imagePath,
      extractedText: extractedText,
      detectedQuestions: questions,
      subject: subject,
      gradeLevel: gradeLevel,
      analyzedAt: DateTime.now(),
      metadata: {
        'textLength': extractedText.length,
        'questionCount': questions.length,
      },
    );
  }

  /// Detect questions in text
  List<String> _detectQuestions(String text) {
    final questions = <String>[];
    final lines = text.split('\n');
    
    for (final line in lines) {
      final trimmed = line.trim();
      if (trimmed.isEmpty) continue;
      
      // Look for question patterns
      if (trimmed.contains('?') ||
          trimmed.toLowerCase().startsWith('what') ||
          trimmed.toLowerCase().startsWith('how') ||
          trimmed.toLowerCase().startsWith('why') ||
          trimmed.toLowerCase().startsWith('when') ||
          trimmed.toLowerCase().startsWith('where') ||
          trimmed.toLowerCase().startsWith('solve') ||
          trimmed.toLowerCase().startsWith('calculate') ||
          trimmed.toLowerCase().startsWith('find')) {
        questions.add(trimmed);
      }
    }
    
    return questions;
  }

  /// Detect subject from text content
  String _detectSubject(String text) {
    final lowerText = text.toLowerCase();
    
    // Math keywords
    if (lowerText.contains(RegExp(r'\b(add|subtract|multiply|divide|fraction|decimal|geometry|algebra)\b'))) {
      return 'Mathematics';
    }
    
    // Science keywords
    if (lowerText.contains(RegExp(r'\b(experiment|hypothesis|observe|plant|animal|energy|force)\b'))) {
      return 'Science';
    }
    
    // English/ESL keywords
    if (lowerText.contains(RegExp(r'\b(grammar|sentence|paragraph|story|vocabulary|spelling)\b'))) {
      return 'English';
    }
    
    return 'General';
  }

  /// Detect grade level from content complexity
  String _detectGradeLevel(String text) {
    final wordCount = text.split(' ').length;
    final avgWordLength = text.replaceAll(' ', '').length / text.split(' ').length;
    
    // Simple heuristic based on text complexity
    if (wordCount < 50 && avgWordLength < 5) {
      return 'Primary 1-2';
    } else if (wordCount < 100 && avgWordLength < 6) {
      return 'Primary 3-4';
    } else {
      return 'Primary 5-6';
    }
  }

  /// Dispose resources
  void dispose() {
    _controller?.dispose();
    _textRecognizer.close();
  }
}