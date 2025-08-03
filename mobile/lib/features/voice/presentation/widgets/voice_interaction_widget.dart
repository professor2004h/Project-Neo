import 'package:flutter/material.dart';
import 'dart:async';
import '../../domain/services/voice_service.dart';
import '../../domain/models/voice_interaction.dart';

/// Voice interaction widget with speech-to-text and text-to-speech
class VoiceInteractionWidget extends StatefulWidget {
  final Function(String text)? onSpeechResult;
  final Function(String message)? onSendMessage;
  final bool autoSpeak;
  final String? responseText;

  const VoiceInteractionWidget({
    super.key,
    this.onSpeechResult,
    this.onSendMessage,
    this.autoSpeak = true,
    this.responseText,
  });

  @override
  State<VoiceInteractionWidget> createState() => _VoiceInteractionWidgetState();
}

class _VoiceInteractionWidgetState extends State<VoiceInteractionWidget>
    with TickerProviderStateMixin {
  final VoiceService _voiceService = VoiceService();
  late AnimationController _pulseController;
  late AnimationController _waveController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _waveAnimation;

  bool _isInitialized = false;
  bool _isListening = false;
  bool _isSpeaking = false;
  String _currentText = '';
  String _errorMessage = '';
  
  StreamSubscription<SpeechResult>? _speechSubscription;
  StreamSubscription<bool>? _listeningSubscription;
  StreamSubscription<bool>? _speakingSubscription;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _initializeVoiceService();
  }

  @override
  void dispose() {
    _speechSubscription?.cancel();
    _listeningSubscription?.cancel();
    _speakingSubscription?.cancel();
    _pulseController.dispose();
    _waveController.dispose();
    _voiceService.dispose();
    super.dispose();
  }

  void _initializeAnimations() {
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    
    _waveController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );

    _pulseAnimation = Tween<double>(
      begin: 1.0,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));

    _waveAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _waveController,
      curve: Curves.easeInOut,
    ));
  }

  Future<void> _initializeVoiceService() async {
    try {
      final success = await _voiceService.initialize();
      
      if (success) {
        setState(() {
          _isInitialized = true;
        });

        // Set up stream subscriptions
        _speechSubscription = _voiceService.speechStream.listen(_onSpeechResult);
        _listeningSubscription = _voiceService.listeningStream.listen(_onListeningChanged);
        _speakingSubscription = _voiceService.speakingStream.listen(_onSpeakingChanged);
      } else {
        setState(() {
          _errorMessage = 'Failed to initialize voice service';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Voice service error: $e';
      });
    }
  }

  void _onSpeechResult(SpeechResult result) {
    setState(() {
      _currentText = result.text;
    });

    if (result.isComplete && result.text.isNotEmpty) {
      widget.onSpeechResult?.call(result.text);
    }
  }

  void _onListeningChanged(bool isListening) {
    setState(() {
      _isListening = isListening;
    });

    if (isListening) {
      _pulseController.repeat(reverse: true);
      _waveController.repeat();
    } else {
      _pulseController.stop();
      _waveController.stop();
    }
  }

  void _onSpeakingChanged(bool isSpeaking) {
    setState(() {
      _isSpeaking = isSpeaking;
    });

    if (isSpeaking) {
      _waveController.repeat();
    } else {
      _waveController.stop();
    }
  }

  Future<void> _startListening() async {
    if (!_isInitialized) return;

    try {
      await _voiceService.startListening();
      setState(() {
        _currentText = '';
        _errorMessage = '';
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to start listening: $e';
      });
    }
  }

  Future<void> _stopListening() async {
    if (!_isInitialized) return;

    try {
      await _voiceService.stopListening();
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to stop listening: $e';
      });
    }
  }

  Future<void> _speak(String text) async {
    if (!_isInitialized || text.isEmpty) return;

    try {
      final request = TTSRequest(
        text: text,
        language: 'en-US',
        rate: 0.5,
        pitch: 1.0,
        volume: 1.0,
      );
      
      await _voiceService.speak(request);
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to speak: $e';
      });
    }
  }

  Future<void> _stopSpeaking() async {
    if (!_isInitialized) return;

    try {
      await _voiceService.stopSpeaking();
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to stop speaking: $e';
      });
    }
  }

  @override
  void didUpdateWidget(VoiceInteractionWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    // Auto-speak response text if it changed
    if (widget.autoSpeak &&
        widget.responseText != null &&
        widget.responseText != oldWidget.responseText &&
        widget.responseText!.isNotEmpty) {
      _speak(widget.responseText!);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return _buildInitializingWidget();
    }

    if (_errorMessage.isNotEmpty) {
      return _buildErrorWidget();
    }

    return _buildVoiceWidget();
  }

  Widget _buildInitializingWidget() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('Initializing voice service...'),
        ],
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Center(
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
            _errorMessage,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _errorMessage = '';
              });
              _initializeVoiceService();
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceWidget() {
    return Column(
      children: [
        // Voice visualization
        Expanded(
          child: Center(
            child: _buildVoiceVisualization(),
          ),
        ),
        
        // Current text display
        if (_currentText.isNotEmpty)
          Container(
            margin: const EdgeInsets.all(16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'You said:',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  _currentText,
                  style: const TextStyle(fontSize: 16),
                ),
              ],
            ),
          ),
        
        // Controls
        Container(
          padding: const EdgeInsets.all(16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Stop speaking button
              if (_isSpeaking)
                FloatingActionButton(
                  heroTag: 'stop_speaking',
                  onPressed: _stopSpeaking,
                  backgroundColor: Colors.red.shade100,
                  child: const Icon(Icons.stop, color: Colors.red),
                ),
              
              // Main voice button
              FloatingActionButton.large(
                heroTag: 'voice_main',
                onPressed: _isListening ? _stopListening : _startListening,
                backgroundColor: _isListening
                    ? Colors.red.shade400
                    : Theme.of(context).primaryColor,
                child: Icon(
                  _isListening ? Icons.stop : Icons.mic,
                  size: 32,
                  color: Colors.white,
                ),
              ),
              
              // Send text button
              if (_currentText.isNotEmpty && !_isListening)
                FloatingActionButton(
                  heroTag: 'send_text',
                  onPressed: () {
                    widget.onSendMessage?.call(_currentText);
                    setState(() {
                      _currentText = '';
                    });
                  },
                  backgroundColor: Colors.green.shade400,
                  child: const Icon(Icons.send, color: Colors.white),
                ),
            ],
          ),
        ),
        
        // Status text
        Container(
          padding: const EdgeInsets.only(bottom: 16),
          child: Text(
            _getStatusText(),
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade600,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildVoiceVisualization() {
    if (_isListening) {
      return AnimatedBuilder(
        animation: Listenable.merge([_pulseController, _waveController]),
        builder: (context, child) {
          return Transform.scale(
            scale: _pulseAnimation.value,
            child: Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Theme.of(context).primaryColor.withOpacity(0.3),
                border: Border.all(
                  color: Theme.of(context).primaryColor,
                  width: 3,
                ),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Animated waves
                  ...List.generate(3, (index) {
                    return AnimatedBuilder(
                      animation: _waveController,
                      builder: (context, child) {
                        final delay = index * 0.3;
                        final animationValue = (_waveAnimation.value + delay) % 1.0;
                        return Container(
                          width: 120 * (0.5 + animationValue * 0.5),
                          height: 120 * (0.5 + animationValue * 0.5),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: Theme.of(context).primaryColor.withOpacity(
                                1.0 - animationValue,
                              ),
                              width: 2,
                            ),
                          ),
                        );
                      },
                    );
                  }),
                  // Microphone icon
                  const Icon(
                    Icons.mic,
                    size: 48,
                    color: Colors.white,
                  ),
                ],
              ),
            ),
          );
        },
      );
    } else if (_isSpeaking) {
      return AnimatedBuilder(
        animation: _waveController,
        builder: (context, child) {
          return Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.blue.shade400,
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Speaking waves
                ...List.generate(4, (index) {
                  final delay = index * 0.2;
                  final animationValue = (_waveAnimation.value + delay) % 1.0;
                  return Container(
                    width: 120 * (0.3 + animationValue * 0.7),
                    height: 120 * (0.3 + animationValue * 0.7),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.blue.withOpacity(1.0 - animationValue),
                        width: 2,
                      ),
                    ),
                  );
                }),
                // Speaker icon
                const Icon(
                  Icons.volume_up,
                  size: 48,
                  color: Colors.white,
                ),
              ],
            ),
          );
        },
      );
    } else {
      return Container(
        width: 120,
        height: 120,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.grey.shade300,
        ),
        child: const Icon(
          Icons.mic_none,
          size: 48,
          color: Colors.grey,
        ),
      );
    }
  }

  String _getStatusText() {
    if (_isListening) {
      return 'Listening... Tap to stop';
    } else if (_isSpeaking) {
      return 'Speaking... Tap to stop';
    } else if (_currentText.isNotEmpty) {
      return 'Tap send to submit or mic to continue';
    } else {
      return 'Tap the microphone to start speaking';
    }
  }
}