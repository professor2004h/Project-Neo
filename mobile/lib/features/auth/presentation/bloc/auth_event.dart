part of 'auth_bloc.dart';

/// Base class for authentication events
abstract class AuthEvent extends Equatable {
  const AuthEvent();

  @override
  List<Object?> get props => [];
}

/// Event to check current authentication status
class AuthCheckRequested extends AuthEvent {
  const AuthCheckRequested();
}

/// Event to request login
class AuthLoginRequested extends AuthEvent {
  final String email;
  final String password;

  const AuthLoginRequested({
    required this.email,
    required this.password,
  });

  @override
  List<Object> get props => [email, password];
}

/// Event to request logout
class AuthLogoutRequested extends AuthEvent {
  const AuthLogoutRequested();
}

/// Event when parent setup is completed
class AuthParentSetupCompleted extends AuthEvent {
  final UserPreferences userPreferences;

  const AuthParentSetupCompleted(this.userPreferences);

  @override
  List<Object> get props => [userPreferences];
}

/// Event when child profile is selected
class AuthChildProfileSelected extends AuthEvent {
  final String childName;
  final int age;
  final int gradeLevel;

  const AuthChildProfileSelected({
    required this.childName,
    required this.age,
    required this.gradeLevel,
  });

  @override
  List<Object> get props => [childName, age, gradeLevel];
}