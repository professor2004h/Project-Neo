/// Centralized route names for the application
class RouteNames {
  // Authentication routes
  static const String splash = '/';
  static const String login = '/login';
  static const String parentSetup = '/parent-setup';
  
  // Main app routes
  static const String home = '/home';
  static const String learning = '/learning';
  static const String progress = '/progress';
  static const String settings = '/settings';
  
  // Nested routes
  static const String tutorChat = '/home/tutor';
  static const String learningActivity = '/learning/activity';
  static const String parentSettings = '/settings/parent';
  
  // Utility methods
  static String learningActivityPath(String activityId) => 
      '/learning/activity/$activityId';
  
  static String tutorChatWithParams({String? subject, String? topic}) {
    final params = <String, String>{};
    if (subject != null) params['subject'] = subject;
    if (topic != null) params['topic'] = topic;
    
    if (params.isEmpty) return tutorChat;
    
    final query = params.entries
        .map((e) => '${e.key}=${Uri.encodeComponent(e.value)}')
        .join('&');
    
    return '$tutorChat?$query';
  }
}