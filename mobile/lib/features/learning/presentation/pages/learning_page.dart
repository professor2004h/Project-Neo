import 'package:flutter/material.dart';
import '../widgets/touch_learning_interface.dart';
import '../../camera/presentation/widgets/camera_capture_widget.dart';
import '../../camera/domain/models/homework_analysis.dart';
import '../../voice/presentation/widgets/voice_interaction_widget.dart';

/// Learning page with activities and exercises
class LearningPage extends StatefulWidget {
  const LearningPage({super.key});

  @override
  State<LearningPage> createState() => _LearningPageState();
}

class _LearningPageState extends State<LearningPage> {
  int _selectedIndex = 0;
  HomeworkAnalysis? _currentAnalysis;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Learning Activities'),
        actions: [
          IconButton(
            icon: const Icon(Icons.camera_alt),
            onPressed: () => _showCameraCapture(context),
            tooltip: 'Capture homework',
          ),
        ],
      ),
      body: IndexedStack(
        index: _selectedIndex,
        children: [
          _buildInteractiveLearning(),
          _buildVoiceInteraction(),
          _buildHomeworkAnalysis(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.touch_app),
            label: 'Interactive',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.mic),
            label: 'Voice',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.camera_alt),
            label: 'Homework',
          ),
        ],
      ),
    );
  }

  Widget _buildInteractiveLearning() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Interactive Learning',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          
          // Sample interactive cards
          InteractiveLearningCard(
            title: 'Mathematics - Fractions',
            content: 'Learn about fractions with interactive examples',
            image: const Icon(Icons.pie_chart, size: 48, color: Colors.blue),
            backgroundColor: Colors.blue.shade50,
            onSwipeLeft: () => _showMessage('Swiped left - Previous topic'),
            onSwipeRight: () => _showMessage('Swiped right - Next topic'),
            onTap: () => _showMessage('Tapped - Opening activity'),
          ),
          
          const SizedBox(height: 16),
          
          InteractiveLearningCard(
            title: 'English - Vocabulary',
            content: 'Build your vocabulary with fun word games',
            image: const Icon(Icons.spellcheck, size: 48, color: Colors.green),
            backgroundColor: Colors.green.shade50,
            isCompleted: true,
            onSwipeLeft: () => _showMessage('Swiped left - Previous topic'),
            onSwipeRight: () => _showMessage('Swiped right - Next topic'),
            onTap: () => _showMessage('Tapped - Opening activity'),
          ),
          
          const SizedBox(height: 16),
          
          InteractiveLearningCard(
            title: 'Science - Plants',
            content: 'Discover how plants grow and what they need',
            image: const Icon(Icons.local_florist, size: 48, color: Colors.orange),
            backgroundColor: Colors.orange.shade50,
            onSwipeLeft: () => _showMessage('Swiped left - Previous topic'),
            onSwipeRight: () => _showMessage('Swiped right - Next topic'),
            onTap: () => _showMessage('Tapped - Opening activity'),
          ),
          
          const SizedBox(height: 24),
          
          // Drag and drop example
          const Text(
            'Drag & Drop Exercise',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(
                child: Column(
                  children: [
                    const Text('Drag these:'),
                    const SizedBox(height: 8),
                    DraggableLearningElement(
                      id: 'apple',
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text('🍎 Apple'),
                      ),
                    ),
                    const SizedBox(height: 8),
                    DraggableLearningElement(
                      id: 'car',
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text('🚗 Car'),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  children: [
                    const Text('Drop here:'),
                    const SizedBox(height: 8),
                    LearningDropTarget(
                      id: 'food',
                      isCorrectTarget: true,
                      onAccept: (draggedId) => _showMessage('$draggedId dropped on food!'),
                      child: Container(
                        height: 80,
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.green.shade300),
                        ),
                        child: const Center(child: Text('🍽️ Food')),
                      ),
                    ),
                    const SizedBox(height: 8),
                    LearningDropTarget(
                      id: 'transport',
                      onAccept: (draggedId) => _showMessage('$draggedId dropped on transport!'),
                      child: Container(
                        height: 80,
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.blue.shade300),
                        ),
                        child: const Center(child: Text('🚌 Transport')),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceInteraction() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Voice Learning',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Ask questions or practice pronunciation',
            style: TextStyle(fontSize: 16, color: Colors.grey),
          ),
          const SizedBox(height: 16),
          
          Expanded(
            child: VoiceInteractionWidget(
              onSpeechResult: (text) {
                _showMessage('You said: $text');
                // Here you would typically send to AI tutor
              },
              onSendMessage: (message) {
                _showMessage('Sending: $message');
                // Here you would send to AI tutor and get response
              },
              responseText: 'Hello! I\'m your AI tutor. How can I help you today?',
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHomeworkAnalysis() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Homework Helper',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Take a photo of your homework for help',
            style: TextStyle(fontSize: 16, color: Colors.grey),
          ),
          const SizedBox(height: 16),
          
          Expanded(
            child: _currentAnalysis == null
                ? _buildHomeworkPrompt()
                : HomeworkAnalysisResultWidget(
                    analysis: _currentAnalysis!,
                    onRetake: () => _showCameraCapture(context),
                    onQuestionSelected: (question) {
                      _showMessage('Selected question: $question');
                      // Here you would open the question in the AI tutor
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildHomeworkPrompt() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.camera_alt,
            size: 64,
            color: Colors.grey,
          ),
          const SizedBox(height: 16),
          const Text(
            'No homework analyzed yet',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Tap the camera button to capture your homework',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16, color: Colors.grey),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => _showCameraCapture(context),
            icon: const Icon(Icons.camera_alt),
            label: const Text('Capture Homework'),
          ),
        ],
      ),
    );
  }

  void _showCameraCapture(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.9,
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: CameraCaptureWidget(
          onAnalysisComplete: (analysis) {
            Navigator.pop(context);
            setState(() {
              _currentAnalysis = analysis;
              _selectedIndex = 2; // Switch to homework tab
            });
          },
          onCancel: () => Navigator.pop(context),
        ),
      ),
    );
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 2),
      ),
    );
  }
}

/// Learning activity page
class LearningActivityPage extends StatelessWidget {
  final String activityId;

  const LearningActivityPage({
    super.key,
    required this.activityId,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Activity $activityId'),
      ),
      body: Center(
        child: Text('Activity ID: $activityId'),
      ),
    );
  }
}