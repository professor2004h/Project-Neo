import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/auth/presentation/pages/parent_setup_page.dart';
import '../../features/home/presentation/pages/home_page.dart';
import '../../features/learning/presentation/pages/learning_page.dart';
import '../../features/progress/presentation/pages/progress_page.dart';
import '../../features/settings/presentation/pages/settings_page.dart';
import '../../features/tutor/presentation/pages/tutor_chat_page.dart';
import '../widgets/child_safe_scaffold.dart';
import 'route_names.dart';

class AppRouter {
  static final GoRouter router = GoRouter(
    initialLocation: RouteNames.splash,
    debugLogDiagnostics: true,
    redirect: _handleRedirect,
    routes: [
      // Splash/Loading Route
      GoRoute(
        path: RouteNames.splash,
        name: 'splash',
        builder: (context, state) => const SplashPage(),
      ),
      
      // Authentication Routes
      GoRoute(
        path: RouteNames.login,
        name: 'login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: RouteNames.parentSetup,
        name: 'parent_setup',
        builder: (context, state) => const ParentSetupPage(),
      ),
      
      // Main App Shell with Bottom Navigation
      ShellRoute(
        builder: (context, state, child) {
          return ChildSafeScaffold(
            currentPath: state.uri.path,
            child: child,
          );
        },
        routes: [
          // Home Tab
          GoRoute(
            path: RouteNames.home,
            name: 'home',
            builder: (context, state) => const HomePage(),
            routes: [
              GoRoute(
                path: 'tutor',
                name: 'tutor_chat',
                builder: (context, state) {
                  final subject = state.uri.queryParameters['subject'];
                  final topic = state.uri.queryParameters['topic'];
                  return TutorChatPage(
                    initialSubject: subject,
                    initialTopic: topic,
                  );
                },
              ),
            ],
          ),
          
          // Learning Tab
          GoRoute(
            path: RouteNames.learning,
            name: 'learning',
            builder: (context, state) => const LearningPage(),
            routes: [
              GoRoute(
                path: 'activity/:activityId',
                name: 'learning_activity',
                builder: (context, state) {
                  final activityId = state.pathParameters['activityId']!;
                  return LearningActivityPage(activityId: activityId);
                },
              ),
            ],
          ),
          
          // Progress Tab
          GoRoute(
            path: RouteNames.progress,
            name: 'progress',
            builder: (context, state) => const ProgressPage(),
          ),
          
          // Settings Tab
          GoRoute(
            path: RouteNames.settings,
            name: 'settings',
            builder: (context, state) => const SettingsPage(),
            routes: [
              GoRoute(
                path: 'parent',
                name: 'parent_settings',
                builder: (context, state) => const ParentSettingsPage(),
              ),
            ],
          ),
        ],
      ),
    ],
  );

  static String? _handleRedirect(BuildContext context, GoRouterState state) {
    final authBloc = context.read<AuthBloc>();
    final authState = authBloc.state;
    
    final isOnAuthPage = [
      RouteNames.login,
      RouteNames.parentSetup,
      RouteNames.splash,
    ].contains(state.matchedLocation);
    
    // Show splash while checking authentication
    if (authState is AuthInitial || authState is AuthLoading) {
      return RouteNames.splash;
    }
    
    // Redirect to login if not authenticated
    if (authState is AuthUnauthenticated && !isOnAuthPage) {
      return RouteNames.login;
    }
    
    // Redirect to parent setup if first time
    if (authState is AuthAuthenticated && 
        authState.requiresSetup && 
        state.matchedLocation != RouteNames.parentSetup) {
      return RouteNames.parentSetup;
    }
    
    // Redirect to home if authenticated and on auth page
    if (authState is AuthAuthenticated && 
        !authState.requiresSetup && 
        isOnAuthPage) {
      return RouteNames.home;
    }
    
    return null; // No redirect needed
  }
}

/// Splash page shown during app initialization
class SplashPage extends StatelessWidget {
  const SplashPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).primaryColor,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // App logo/icon
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: const Icon(
                Icons.school,
                size: 60,
                color: Color(0xFF2196F3),
              ),
            ),
            const SizedBox(height: 32),
            const Text(
              'Cambridge AI Tutor',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Learning made fun and safe',
              style: TextStyle(
                fontSize: 16,
                color: Colors.white70,
              ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          ],
        ),
      ),
    );
  }
}