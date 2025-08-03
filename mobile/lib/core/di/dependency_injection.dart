import 'package:get_it/get_it.dart';

import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/navigation/presentation/bloc/navigation_bloc.dart';
import '../../features/offline/presentation/bloc/offline_bloc.dart';
import '../../features/sync/presentation/bloc/sync_bloc.dart';
import '../utils/logger.dart';

final getIt = GetIt.instance;

/// Dependency injection setup for the application
class DependencyInjection {
  static Future<void> init() async {
    try {
      AppLogger.info('Initializing dependency injection');

      // Register BLoCs
      _registerBlocs();

      // Register Services (when implemented)
      // _registerServices();

      // Register Repositories (when implemented)
      // _registerRepositories();

      AppLogger.info('Dependency injection initialized successfully');
    } catch (e, stackTrace) {
      AppLogger.error('Failed to initialize dependency injection', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  static void _registerBlocs() {
    // Auth BLoC
    getIt.registerFactory<AuthBloc>(() => AuthBloc());

    // Navigation BLoC
    getIt.registerFactory<NavigationBloc>(() => NavigationBloc());

    // Offline BLoC
    getIt.registerFactory<OfflineBloc>(() => OfflineBloc());

    // Sync BLoC
    getIt.registerFactory<SyncBloc>(() => SyncBloc());

    AppLogger.info('BLoCs registered successfully');
  }

  // Future service registration
  // static void _registerServices() {
  //   // API Service
  //   getIt.registerLazySingleton<ApiService>(() => ApiService());
  //   
  //   // Tutor Service
  //   getIt.registerLazySingleton<TutorService>(() => TutorService());
  //   
  //   // Content Service
  //   getIt.registerLazySingleton<ContentService>(() => ContentService());
  //   
  //   // Progress Service
  //   getIt.registerLazySingleton<ProgressService>(() => ProgressService());
  //   
  //   AppLogger.info('Services registered successfully');
  // }

  // Future repository registration
  // static void _registerRepositories() {
  //   // User Repository
  //   getIt.registerLazySingleton<UserRepository>(() => UserRepository());
  //   
  //   // Content Repository
  //   getIt.registerLazySingleton<ContentRepository>(() => ContentRepository());
  //   
  //   // Progress Repository
  //   getIt.registerLazySingleton<ProgressRepository>(() => ProgressRepository());
  //   
  //   AppLogger.info('Repositories registered successfully');
  // }

  /// Reset all dependencies (useful for testing)
  static Future<void> reset() async {
    await getIt.reset();
    AppLogger.info('Dependency injection reset');
  }
}