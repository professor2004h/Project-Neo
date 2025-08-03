import 'dart:io';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../../domain/services/camera_service.dart';
import '../../domain/models/homework_analysis.dart';

/// Camera capture widget for homework photos
class CameraCaptureWidget extends StatefulWidget {
  final Function(HomeworkAnalysis)? onAnalysisComplete;
  final VoidCallback? onCancel;

  const CameraCaptureWidget({
    super.key,
    this.onAnalysisComplete,
    this.onCancel,
  });

  @override
  State<CameraCaptureWidget> createState() => _CameraCaptureWidgetState();
}

class _CameraCaptureWidgetState extends State<CameraCaptureWidget> {
  final CameraService _cameraService = CameraService();
  CameraController? _controller;
  bool _isInitialized = false;
  bool _isCapturing = false;
  bool _isAnalyzing = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  @override
  void dispose() {
    _controller?.dispose();
    _cameraService.dispose();
    super.dispose();
  }

  Future<void> _initializeCamera() async {
    try {
      await _cameraService.initialize();
      _controller = await _cameraService.initializeController();
      
      if (mounted) {
        setState(() {
          _isInitialized = true;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to initialize camera: $e';
      });
    }
  }

  Future<void> _captureAndAnalyze() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    setState(() {
      _isCapturing = true;
    });

    try {
      final result = await _cameraService.capturePhoto();
      
      setState(() {
        _isCapturing = false;
        _isAnalyzing = true;
      });

      final analysis = await _cameraService.analyzeHomework(result.imagePath);
      
      setState(() {
        _isAnalyzing = false;
      });

      widget.onAnalysisComplete?.call(analysis);
    } catch (e) {
      setState(() {
        _isCapturing = false;
        _isAnalyzing = false;
        _errorMessage = 'Failed to capture or analyze image: $e';
      });
    }
  }

  Future<void> _pickFromGallery() async {
    setState(() {
      _isAnalyzing = true;
    });

    try {
      final result = await _cameraService.pickFromGallery();
      
      if (result != null) {
        final analysis = await _cameraService.analyzeHomework(result.imagePath);
        
        setState(() {
          _isAnalyzing = false;
        });

        widget.onAnalysisComplete?.call(analysis);
      } else {
        setState(() {
          _isAnalyzing = false;
        });
      }
    } catch (e) {
      setState(() {
        _isAnalyzing = false;
        _errorMessage = 'Failed to analyze image: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_errorMessage != null) {
      return _buildErrorWidget();
    }

    if (!_isInitialized) {
      return _buildLoadingWidget();
    }

    if (_isAnalyzing) {
      return _buildAnalyzingWidget();
    }

    return _buildCameraWidget();
  }

  Widget _buildErrorWidget() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            size: 64,
            color: Colors.red,
          ),
          const SizedBox(height: 16),
          Text(
            _errorMessage!,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton(
                onPressed: () {
                  setState(() {
                    _errorMessage = null;
                  });
                  _initializeCamera();
                },
                child: const Text('Retry'),
              ),
              ElevatedButton(
                onPressed: _pickFromGallery,
                child: const Text('Pick from Gallery'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingWidget() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('Initializing camera...'),
        ],
      ),
    );
  }

  Widget _buildAnalyzingWidget() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text(
            'Analyzing homework...',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Text(
            'Please wait while we extract text and identify questions',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraWidget() {
    return Column(
      children: [
        // Camera preview
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade300, width: 2),
            ),
            margin: const EdgeInsets.all(16),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: CameraPreview(_controller!),
            ),
          ),
        ),
        
        // Instructions
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: const Text(
            'Position your homework clearly in the frame and tap capture',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        
        // Controls
        Container(
          padding: const EdgeInsets.all(16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Gallery button
              FloatingActionButton(
                heroTag: 'gallery',
                onPressed: _pickFromGallery,
                backgroundColor: Colors.grey.shade200,
                child: const Icon(Icons.photo_library, color: Colors.black87),
              ),
              
              // Capture button
              FloatingActionButton.large(
                heroTag: 'capture',
                onPressed: _isCapturing ? null : _captureAndAnalyze,
                backgroundColor: Theme.of(context).primaryColor,
                child: _isCapturing
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Icon(Icons.camera_alt, size: 32),
              ),
              
              // Cancel button
              FloatingActionButton(
                heroTag: 'cancel',
                onPressed: widget.onCancel,
                backgroundColor: Colors.red.shade100,
                child: const Icon(Icons.close, color: Colors.red),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Widget to display homework analysis results
class HomeworkAnalysisResultWidget extends StatelessWidget {
  final HomeworkAnalysis analysis;
  final VoidCallback? onRetake;
  final Function(String question)? onQuestionSelected;

  const HomeworkAnalysisResultWidget({
    super.key,
    required this.analysis,
    this.onRetake,
    this.onQuestionSelected,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 32),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Homework Analyzed!',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              IconButton(
                onPressed: onRetake,
                icon: const Icon(Icons.camera_alt),
                tooltip: 'Retake photo',
              ),
            ],
          ),
          
          const SizedBox(height: 16),
          
          // Image preview
          Container(
            height: 200,
            width: double.infinity,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.file(
                File(analysis.imagePath),
                fit: BoxFit.cover,
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Analysis info
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.subject, color: Colors.blue.shade600),
                      const SizedBox(width: 8),
                      Text(
                        'Subject: ${analysis.subject}',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.school, color: Colors.orange.shade600),
                      const SizedBox(width: 8),
                      Text(
                        'Level: ${analysis.gradeLevel}',
                        style: const TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.quiz, color: Colors.green.shade600),
                      const SizedBox(width: 8),
                      Text(
                        'Questions found: ${analysis.detectedQuestions.length}',
                        style: const TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Detected questions
          if (analysis.detectedQuestions.isNotEmpty) ...[
            const Text(
              'Detected Questions:',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            ...analysis.detectedQuestions.asMap().entries.map((entry) {
              final index = entry.key;
              final question = entry.value;
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Theme.of(context).primaryColor,
                    child: Text(
                      '${index + 1}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  title: Text(question),
                  trailing: const Icon(Icons.arrow_forward_ios),
                  onTap: () => onQuestionSelected?.call(question),
                ),
              );
            }).toList(),
          ],
          
          // Extracted text (collapsible)
          const SizedBox(height: 16),
          ExpansionTile(
            title: const Text(
              'Extracted Text',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            leading: const Icon(Icons.text_fields),
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                margin: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  analysis.extractedText.isEmpty
                      ? 'No text detected'
                      : analysis.extractedText,
                  style: const TextStyle(fontSize: 14),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ],
      ),
    );
  }
}