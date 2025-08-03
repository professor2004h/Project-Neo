part of 'navigation_bloc.dart';

/// Base class for navigation events
abstract class NavigationEvent extends Equatable {
  const NavigationEvent();

  @override
  List<Object?> get props => [];
}

/// Event fired when user changes tabs in bottom navigation
class NavigationTabChanged extends NavigationEvent {
  final String route;

  const NavigationTabChanged(this.route);

  @override
  List<Object> get props => [route];
}

/// Event fired when tutor chat is opened
class NavigationTutorChatOpened extends NavigationEvent {
  final String? subject;
  final String? topic;

  const NavigationTutorChatOpened({this.subject, this.topic});

  @override
  List<Object?> get props => [subject, topic];
}

/// Event fired when back button is pressed
class NavigationBackPressed extends NavigationEvent {
  final String currentRoute;

  const NavigationBackPressed(this.currentRoute);

  @override
  List<Object> get props => [currentRoute];
}

/// Event fired when deep link is handled
class NavigationDeepLinkHandled extends NavigationEvent {
  final String deepLink;
  final Map<String, String> parameters;

  const NavigationDeepLinkHandled({
    required this.deepLink,
    this.parameters = const {},
  });

  @override
  List<Object> get props => [deepLink, parameters];
}