import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/navigation/presentation/bloc/navigation_bloc.dart';
import '../navigation/route_names.dart';
import '../theme/app_colors.dart';

/// Child-friendly scaffold with bottom navigation and safety features
class ChildSafeScaffold extends StatelessWidget {
  final Widget child;
  final String currentPath;

  const ChildSafeScaffold({
    super.key,
    required this.child,
    required this.currentPath,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(child: child),
      bottomNavigationBar: _buildBottomNavigation(context),
      floatingActionButton: _buildFloatingActionButton(context),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }

  Widget _buildBottomNavigation(BuildContext context) {
    return BlocBuilder<NavigationBloc, NavigationState>(
      builder: (context, state) {
        final currentIndex = _getCurrentIndex();
        
        return Container(
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 10,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: BottomAppBar(
            shape: const CircularNotchedRectangle(),
            notchMargin: 8,
            color: Colors.white,
            elevation: 0,
            child: SizedBox(
              height: 60,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(
                    context,
                    icon: Icons.home_rounded,
                    label: 'Home',
                    index: 0,
                    isSelected: currentIndex == 0,
                    onTap: () => _navigateToTab(context, RouteNames.home),
                  ),
                  _buildNavItem(
                    context,
                    icon: Icons.book_rounded,
                    label: 'Learn',
                    index: 1,
                    isSelected: currentIndex == 1,
                    onTap: () => _navigateToTab(context, RouteNames.learning),
                  ),
                  const SizedBox(width: 40), // Space for FAB
                  _buildNavItem(
                    context,
                    icon: Icons.trending_up_rounded,
                    label: 'Progress',
                    index: 2,
                    isSelected: currentIndex == 2,
                    onTap: () => _navigateToTab(context, RouteNames.progress),
                  ),
                  _buildNavItem(
                    context,
                    icon: Icons.settings_rounded,
                    label: 'Settings',
                    index: 3,
                    isSelected: currentIndex == 3,
                    onTap: () => _navigateToTab(context, RouteNames.settings),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildNavItem(
    BuildContext context, {
    required IconData icon,
    required String label,
    required int index,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 24,
              color: isSelected 
                  ? AppColors.primary 
                  : AppColors.textSecondary,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                color: isSelected 
                    ? AppColors.primary 
                    : AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget? _buildFloatingActionButton(BuildContext context) {
    // Only show FAB on home and learning pages
    if (![RouteNames.home, RouteNames.learning].contains(_getBasePath())) {
      return null;
    }

    return FloatingActionButton(
      onPressed: () => _openTutorChat(context),
      backgroundColor: AppColors.accent,
      elevation: 4,
      child: const Icon(
        Icons.chat_bubble_rounded,
        color: Colors.white,
        size: 28,
      ),
    );
  }

  int _getCurrentIndex() {
    final basePath = _getBasePath();
    switch (basePath) {
      case RouteNames.home:
        return 0;
      case RouteNames.learning:
        return 1;
      case RouteNames.progress:
        return 2;
      case RouteNames.settings:
        return 3;
      default:
        return 0;
    }
  }

  String _getBasePath() {
    if (currentPath.startsWith(RouteNames.home)) return RouteNames.home;
    if (currentPath.startsWith(RouteNames.learning)) return RouteNames.learning;
    if (currentPath.startsWith(RouteNames.progress)) return RouteNames.progress;
    if (currentPath.startsWith(RouteNames.settings)) return RouteNames.settings;
    return RouteNames.home;
  }

  void _navigateToTab(BuildContext context, String route) {
    context.read<NavigationBloc>().add(NavigationTabChanged(route));
    // Use go instead of push to replace the current route
    context.go(route);
  }

  void _openTutorChat(BuildContext context) {
    context.read<NavigationBloc>().add(const NavigationTutorChatOpened());
    context.push(RouteNames.tutorChat);
  }
}