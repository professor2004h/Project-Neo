import 'package:logger/logger.dart';

/// Application logger utility
class AppLogger {
  static late Logger _logger;
  static bool _initialized = false;

  /// Initialize the logger
  static void init({Level level = Level.info}) {
    if (_initialized) return;

    _logger = Logger(
      printer: PrettyPrinter(
        methodCount: 2,
        errorMethodCount: 8,
        lineLength: 120,
        colors: true,
        printEmojis: true,
        printTime: true,
      ),
      level: level,
    );

    _initialized = true;
    info('Logger initialized');
  }

  /// Log debug message
  static void debug(String message, {Object? error, StackTrace? stackTrace}) {
    if (!_initialized) init();
    _logger.d(message, error: error, stackTrace: stackTrace);
  }

  /// Log info message
  static void info(String message, {Object? error, StackTrace? stackTrace}) {
    if (!_initialized) init();
    _logger.i(message, error: error, stackTrace: stackTrace);
  }

  /// Log warning message
  static void warning(String message, {Object? error, StackTrace? stackTrace}) {
    if (!_initialized) init();
    _logger.w(message, error: error, stackTrace: stackTrace);
  }

  /// Log error message
  static void error(String message, {Object? error, StackTrace? stackTrace}) {
    if (!_initialized) init();
    _logger.e(message, error: error, stackTrace: stackTrace);
  }

  /// Log fatal message
  static void fatal(String message, {Object? error, StackTrace? stackTrace}) {
    if (!_initialized) init();
    _logger.f(message, error: error, stackTrace: stackTrace);
  }

  /// Log trace message
  static void trace(String message, {Object? error, StackTrace? stackTrace}) {
    if (!_initialized) init();
    _logger.t(message, error: error, stackTrace: stackTrace);
  }
}