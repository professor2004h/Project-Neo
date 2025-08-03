import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/storage/local_storage.dart';
import '../../../../core/utils/logger.dart';

part 'auth_event.dart';
part 'auth_state.dart';

/// BLoC for managing authentication state
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc() : super(const AuthInitial()) {
    on<AuthCheckRequested>(_onCheckRequested);
    on<AuthLoginRequested>(_onLoginRequested);
    on<AuthLogoutRequested>(_onLogoutRequested);
    on<AuthParentSetupCompleted>(_onParentSetupCompleted);
    on<AuthChildProfileSelected>(_onChildProfileSelected);
  }

  void _onCheckRequested(AuthCheckRequested event, Emitter<AuthState> emit) async {
    try {
      emit(const AuthLoading());

      // Check for stored user preferences (simulating auth check)
      final userPreferences = LocalStorage.getUserPreferences();
      
      if (userPreferences != null) {
        AppLogger.info('User found in local storage: ${userPreferences.userId}');
        
        // Check if user needs to complete setup
        final requiresSetup = userPreferences.childName.isEmpty || 
                             userPreferences.age == 0;
        
        emit(AuthAuthenticated(
          userId: userPreferences.userId,
          childName: userPreferences.childName,
          requiresSetup: requiresSetup,
          userPreferences: userPreferences,
        ));
      } else {
        AppLogger.info('No user found in local storage');
        emit(const AuthUnauthenticated());
      }
    } catch (e, stackTrace) {
      AppLogger.error('Auth check failed', error: e, stackTrace: stackTrace);
      emit(const AuthError('Failed to check authentication status'));
    }
  }

  void _onLoginRequested(AuthLoginRequested event, Emitter<AuthState> emit) async {
    try {
      emit(const AuthLoading());

      // Simulate login process
      await Future.delayed(const Duration(seconds: 2));

      // For demo purposes, create a mock user
      final userId = 'user_${DateTime.now().millisecondsSinceEpoch}';
      
      AppLogger.info('User logged in: $userId');
      
      emit(AuthAuthenticated(
        userId: userId,
        childName: '',
        requiresSetup: true,
        userPreferences: null,
      ));
    } catch (e, stackTrace) {
      AppLogger.error('Login failed', error: e, stackTrace: stackTrace);
      emit(const AuthError('Login failed. Please try again.'));
    }
  }

  void _onLogoutRequested(AuthLogoutRequested event, Emitter<AuthState> emit) async {
    try {
      emit(const AuthLoading());

      // Clear local storage
      await LocalStorage.clearAllData();
      
      AppLogger.info('User logged out');
      
      emit(const AuthUnauthenticated());
    } catch (e, stackTrace) {
      AppLogger.error('Logout failed', error: e, stackTrace: stackTrace);
      emit(const AuthError('Failed to logout'));
    }
  }

  void _onParentSetupCompleted(AuthParentSetupCompleted event, Emitter<AuthState> emit) async {
    try {
      final currentState = state;
      if (currentState is! AuthAuthenticated) {
        emit(const AuthError('Invalid state for setup completion'));
        return;
      }

      emit(const AuthLoading());

      // Save user preferences
      final userPreferences = event.userPreferences;
      await LocalStorage.saveUserPreferences(userPreferences);

      AppLogger.info('Parent setup completed for user: ${userPreferences.userId}');

      emit(AuthAuthenticated(
        userId: userPreferences.userId,
        childName: userPreferences.childName,
        requiresSetup: false,
        userPreferences: userPreferences,
      ));
    } catch (e, stackTrace) {
      AppLogger.error('Parent setup completion failed', error: e, stackTrace: stackTrace);
      emit(const AuthError('Failed to complete setup'));
    }
  }

  void _onChildProfileSelected(AuthChildProfileSelected event, Emitter<AuthState> emit) async {
    try {
      final currentState = state;
      if (currentState is! AuthAuthenticated) {
        emit(const AuthError('Invalid state for profile selection'));
        return;
      }

      // Update current child profile
      final updatedPreferences = currentState.userPreferences?.copyWith(
        childName: event.childName,
        age: event.age,
        gradeLevel: event.gradeLevel,
        lastUpdated: DateTime.now(),
      );

      if (updatedPreferences != null) {
        await LocalStorage.saveUserPreferences(updatedPreferences);
      }

      AppLogger.info('Child profile selected: ${event.childName}');

      emit(currentState.copyWith(
        childName: event.childName,
        userPreferences: updatedPreferences,
      ));
    } catch (e, stackTrace) {
      AppLogger.error('Child profile selection failed', error: e, stackTrace: stackTrace);
      emit(const AuthError('Failed to select child profile'));
    }
  }
}