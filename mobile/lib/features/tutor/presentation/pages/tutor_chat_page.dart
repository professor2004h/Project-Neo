import 'package:flutter/material.dart';

/// Tutor chat page for AI interactions
class TutorChatPage extends StatelessWidget {
  final String? initialSubject;
  final String? initialTopic;

  const TutorChatPage({
    super.key,
    this.initialSubject,
    this.initialTopic,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(initialSubject != null 
            ? '$initialSubject Tutor' 
            : 'AI Tutor'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.chat_bubble, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text(
              'AI Tutor Chat',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            if (initialSubject != null)
              Text(
                'Subject: $initialSubject',
                style: const TextStyle(fontSize: 16, color: Colors.grey),
              ),
            if (initialTopic != null)
              Text(
                'Topic: $initialTopic',
                style: const TextStyle(fontSize: 16, color: Colors.grey),
              ),
            const SizedBox(height: 8),
            const Text(
              'Coming soon!',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}