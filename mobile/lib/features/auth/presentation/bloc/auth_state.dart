part of 'auth_bloc.dart';

/// Base class for authentication states
abstract class AuthState extends Equatable {
  const AuthState();

  @override
  List<Object?> get props => [];
}

/// Initial authentication state
class AuthInitial extends AuthState {
  const AuthInitial();
}

/// Loading authentication state
class AuthLoading extends AuthState {
  const AuthLoading();
}

/// Authenticated state
class AuthAuthenticated extends AuthState {
  final String userId;
  final String childName;
  final bool requiresSetup;
  final UserPreferences? userPreferences;

  const AuthAuthenticated({
    required this.userId,
    required this.childName,
    required this.requiresSetup,
    this.userPreferences,
  });

  AuthAuthenticated copyWith({
    String? userId,
    String? childName,
    bool? requiresSetup,
    UserPreferences? userPreferences,
  }) {
    return AuthAuthenticated(
      userId: userId ?? this.userId,
      childName: childName ?? this.childName,
      requiresSetup: requiresSetup ?? this.requiresSetup,
      userPreferences: userPreferences ?? this.userPreferences,
    );
  }

  @override
  List<Object?> get props => [userId, childName, requiresSetup, userPreferences];
}

/// Unauthenticated state
class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated();
}

/// Authentication error state
class AuthError extends AuthState {
  final String message;

  const AuthError(this.message);

  @override
  List<Object> get props => [message];
}