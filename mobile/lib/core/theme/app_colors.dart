import 'package:flutter/material.dart';

/// Application color palette designed for child-friendly interface
class AppColors {
  // Primary Colors
  static const Color primary = Color(0xFF2196F3); // Friendly blue
  static const Color primaryLight = Color(0xFF64B5F6);
  static const Color primaryDark = Color(0xFF1976D2);
  
  // Secondary/Accent Colors
  static const Color accent = Color(0xFF4CAF50); // Encouraging green
  static const Color accentLight = Color(0xFF81C784);
  static const Color accentDark = Color(0xFF388E3C);
  
  // Background Colors
  static const Color backgroundPrimary = Color(0xFFF8F9FA);
  static const Color backgroundSecondary = Color(0xFFF1F3F4);
  static const Color backgroundTertiary = Color(0xFFE8F0FE);
  
  // Text Colors
  static const Color textPrimary = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
  static const Color textTertiary = Color(0xFF9E9E9E);
  static const Color textOnPrimary = Colors.white;
  
  // Status Colors
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFF9800);
  static const Color error = Color(0xFFF44336);
  static const Color info = Color(0xFF2196F3);
  
  // Subject-specific Colors
  static const Color mathematics = Color(0xFF9C27B0); // Purple
  static const Color english = Color(0xFF3F51B5); // Indigo
  static const Color science = Color(0xFF009688); // Teal
  
  // Gamification Colors
  static const Color gold = Color(0xFFFFD700);
  static const Color silver = Color(0xFFC0C0C0);
  static const Color bronze = Color(0xFFCD7F32);
  
  // Achievement Colors
  static const Color achievementBronze = Color(0xFFCD7F32);
  static const Color achievementSilver = Color(0xFFC0C0C0);
  static const Color achievementGold = Color(0xFFFFD700);
  static const Color achievementPlatinum = Color(0xFFE5E4E2);
  
  // Progress Colors
  static const Color progressBeginner = Color(0xFFE3F2FD);
  static const Color progressIntermediate = Color(0xFFBBDEFB);
  static const Color progressAdvanced = Color(0xFF90CAF9);
  static const Color progressMastery = Color(0xFF42A5F5);
  
  // Difficulty Level Colors
  static const Color difficultyEasy = Color(0xFF4CAF50);
  static const Color difficultyMedium = Color(0xFFFF9800);
  static const Color difficultyHard = Color(0xFFF44336);
  
  // Safety and Child-friendly Colors
  static const Color childSafe = Color(0xFF4CAF50);
  static const Color parentalControl = Color(0xFF9C27B0);
  static const Color offline = Color(0xFF607D8B);
  
  // Gradient Colors
  static const List<Color> primaryGradient = [
    Color(0xFF2196F3),
    Color(0xFF21CBF3),
  ];
  
  static const List<Color> successGradient = [
    Color(0xFF4CAF50),
    Color(0xFF8BC34A),
  ];
  
  static const List<Color> warningGradient = [
    Color(0xFFFF9800),
    Color(0xFFFFC107),
  ];
  
  // Helper methods
  static Color getSubjectColor(String subject) {
    switch (subject.toLowerCase()) {
      case 'mathematics':
      case 'math':
        return mathematics;
      case 'english':
      case 'esl':
        return english;
      case 'science':
        return science;
      default:
        return primary;
    }
  }
  
  static Color getDifficultyColor(int difficulty) {
    switch (difficulty) {
      case 1:
        return difficultyEasy;
      case 2:
        return difficultyMedium;
      case 3:
        return difficultyHard;
      default:
        return difficultyMedium;
    }
  }
  
  static Color getProgressColor(double progress) {
    if (progress < 0.25) return progressBeginner;
    if (progress < 0.5) return progressIntermediate;
    if (progress < 0.75) return progressAdvanced;
    return progressMastery;
  }
}