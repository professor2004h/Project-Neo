import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../features/auth/presentation/bloc/auth_bloc.dart';
import '../features/navigation/presentation/bloc/navigation_bloc.dart';
import '../features/offline/presentation/bloc/offline_bloc.dart';
import '../features/sync/presentation/bloc/sync_bloc.dart';
import 'di/dependency_injection.dart';
import 'navigation/app_router.dart';
import 'theme/app_theme.dart';
import 'utils/logger.dart';

class CambridgeAITutorApp extends StatelessWidget {
  const CambridgeAITutorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<AuthBloc>(
          create: (context) => getIt<AuthBloc>()..add(const AuthCheckRequested()),
        ),
        BlocProvider<NavigationBloc>(
          create: (context) => getIt<NavigationBloc>(),
        ),
        BlocProvider<OfflineBloc>(
          create: (context) => getIt<OfflineBloc>()..add(const OfflineInitialized()),
        ),
        BlocProvider<SyncBloc>(
          create: (context) => getIt<SyncBloc>(),
        ),
      ],
      child: BlocListener<AuthBloc, AuthState>(
        listener: (context, state) {
          AppLogger.info('Auth state changed: ${state.runtimeType}');
        },
        child: MaterialApp.router(
          title: 'Cambridge AI Tutor',
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: ThemeMode.system,
          routerConfig: AppRouter.router,
          debugShowCheckedModeBanner: false,
          builder: (context, child) {
            return BlocListener<OfflineBloc, OfflineState>(
              listener: (context, state) {
                if (state is OfflineStateChanged) {
                  _showConnectivitySnackBar(context, state.isOnline);
                }
              },
              child: child ?? const SizedBox.shrink(),
            );
          },
        ),
      ),
    );
  }

  void _showConnectivitySnackBar(BuildContext context, bool isOnline) {
    final messenger = ScaffoldMessenger.of(context);
    messenger.hideCurrentSnackBar();
    
    messenger.showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              isOnline ? Icons.wifi : Icons.wifi_off,
              color: Colors.white,
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              isOnline ? 'Back online' : 'Offline mode',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ],
        ),
        backgroundColor: isOnline ? Colors.green : Colors.orange,
        duration: Duration(seconds: isOnline ? 2 : 4),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }
}