part of 'navigation_bloc.dart';

/// Base class for navigation states
abstract class NavigationState extends Equatable {
  const NavigationState();

  @override
  List<Object?> get props => [];
}

/// Initial navigation state
class NavigationInitial extends NavigationState {
  const NavigationInitial();
}

/// State when user changes tabs
class NavigationTabState extends NavigationState {
  final String currentRoute;
  final DateTime timestamp;

  const NavigationTabState({
    required this.currentRoute,
    required this.timestamp,
  });

  @override
  List<Object> get props => [currentRoute, timestamp];
}

/// State when tutor chat is opened
class NavigationTutorChatState extends NavigationState {
  final String? subject;
  final String? topic;
  final DateTime timestamp;

  const NavigationTutorChatState({
    this.subject,
    this.topic,
    required this.timestamp,
  });

  @override
  List<Object?> get props => [subject, topic, timestamp];
}

/// State when back navigation occurs
class NavigationBackState extends NavigationState {
  final String previousRoute;
  final DateTime timestamp;

  const NavigationBackState({
    required this.previousRoute,
    required this.timestamp,
  });

  @override
  List<Object> get props => [previousRoute, timestamp];
}

/// State when deep link is handled
class NavigationDeepLinkState extends NavigationState {
  final String deepLink;
  final Map<String, String> parameters;
  final DateTime timestamp;

  const NavigationDeepLinkState({
    required this.deepLink,
    required this.parameters,
    required this.timestamp,
  });

  @override
  List<Object> get props => [deepLink, parameters, timestamp];
}