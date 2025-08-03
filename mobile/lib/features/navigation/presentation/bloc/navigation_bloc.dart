import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/utils/logger.dart';

part 'navigation_event.dart';
part 'navigation_state.dart';

/// BLoC for managing navigation state and child-safe navigation tracking
class NavigationBloc extends Bloc<NavigationEvent, NavigationState> {
  NavigationBloc() : super(const NavigationInitial()) {
    on<NavigationTabChanged>(_onTabChanged);
    on<NavigationTutorChatOpened>(_onTutorChatOpened);
    on<NavigationBackPressed>(_onBackPressed);
    on<NavigationDeepLinkHandled>(_onDeepLinkHandled);
  }

  void _onTabChanged(NavigationTabChanged event, Emitter<NavigationState> emit) {
    AppLogger.info('Navigation tab changed to: ${event.route}');
    
    emit(NavigationTabState(
      currentRoute: event.route,
      timestamp: DateTime.now(),
    ));
  }

  void _onTutorChatOpened(NavigationTutorChatOpened event, Emitter<NavigationState> emit) {
    AppLogger.info('Tutor chat opened');
    
    emit(NavigationTutorChatState(
      subject: event.subject,
      topic: event.topic,
      timestamp: DateTime.now(),
    ));
  }

  void _onBackPressed(NavigationBackPressed event, Emitter<NavigationState> emit) {
    AppLogger.info('Back navigation pressed from: ${event.currentRoute}');
    
    emit(NavigationBackState(
      previousRoute: event.currentRoute,
      timestamp: DateTime.now(),
    ));
  }

  void _onDeepLinkHandled(NavigationDeepLinkHandled event, Emitter<NavigationState> emit) {
    AppLogger.info('Deep link handled: ${event.deepLink}');
    
    emit(NavigationDeepLinkState(
      deepLink: event.deepLink,
      parameters: event.parameters,
      timestamp: DateTime.now(),
    ));
  }
}