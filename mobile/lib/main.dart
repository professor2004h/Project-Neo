import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'core/app.dart';
import 'core/di/dependency_injection.dart';
import 'core/storage/local_storage.dart';
import 'core/utils/logger.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize logging
  AppLogger.init();
  
  try {
    // Initialize Hive for local storage
    await Hive.initFlutter();
    await LocalStorage.init();
    
    // Initialize dependency injection
    await DependencyInjection.init();
    
    AppLogger.info('App initialization completed successfully');
    
    runApp(const CambridgeAITutorApp());
  } catch (e, stackTrace) {
    AppLogger.error('Failed to initialize app', error: e, stackTrace: stackTrace);
    runApp(const ErrorApp());
  }
}

/// Error app displayed when initialization fails
class ErrorApp extends StatelessWidget {
  const ErrorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Cambridge AI Tutor - Error',
      home: Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.red,
              ),
              const SizedBox(height: 16),
              const Text(
                'Failed to start the app',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Please restart the application',
                style: TextStyle(fontSize: 14),
              ),
            ],
          ),
        ),
      ),
    );
  }
}