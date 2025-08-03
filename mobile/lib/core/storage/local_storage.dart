import 'package:hive_flutter/hive_flutter.dart';

import '../utils/logger.dart';
import 'models/cached_content.dart';
import 'models/offline_activity.dart';
import 'models/user_preferences.dart';

/// Local storage manager using Hive for offline-first architecture
class LocalStorage {
  static const String _userPreferencesBox = 'user_preferences';
  static const String _cachedContentBox = 'cached_content';
  static const String _offlineActivitiesBox = 'offline_activities';
  static const String _syncQueueBox = 'sync_queue';

  static late Box<UserPreferences> _userPreferencesBoxInstance;
  static late Box<CachedContent> _cachedContentBoxInstance;
  static late Box<OfflineActivity> _offlineActivitiesBoxInstance;
  static late Box<Map<String, dynamic>> _syncQueueBoxInstance;

  /// Initialize local storage
  static Future<void> init() async {
    try {
      // Register adapters
      Hive.registerAdapter(UserPreferencesAdapter());
      Hive.registerAdapter(CachedContentAdapter());
      Hive.registerAdapter(OfflineActivityAdapter());

      // Open boxes
      _userPreferencesBoxInstance = await Hive.openBox<UserPreferences>(_userPreferencesBox);
      _cachedContentBoxInstance = await Hive.openBox<CachedContent>(_cachedContentBox);
      _offlineActivitiesBoxInstance = await Hive.openBox<OfflineActivity>(_offlineActivitiesBox);
      _syncQueueBoxInstance = await Hive.openBox<Map<String, dynamic>>(_syncQueueBox);

      AppLogger.info('Local storage initialized successfully');
    } catch (e, stackTrace) {
      AppLogger.error('Failed to initialize local storage', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// User Preferences Storage
  static Future<void> saveUserPreferences(UserPreferences preferences) async {
    try {
      await _userPreferencesBoxInstance.put('current', preferences);
      AppLogger.info('User preferences saved');
    } catch (e) {
      AppLogger.error('Failed to save user preferences', error: e);
      rethrow;
    }
  }

  static UserPreferences? getUserPreferences() {
    try {
      return _userPreferencesBoxInstance.get('current');
    } catch (e) {
      AppLogger.error('Failed to get user preferences', error: e);
      return null;
    }
  }

  /// Cached Content Storage
  static Future<void> cacheContent(CachedContent content) async {
    try {
      await _cachedContentBoxInstance.put(content.id, content);
      AppLogger.info('Content cached: ${content.id}');
    } catch (e) {
      AppLogger.error('Failed to cache content', error: e);
      rethrow;
    }
  }

  static CachedContent? getCachedContent(String id) {
    try {
      return _cachedContentBoxInstance.get(id);
    } catch (e) {
      AppLogger.error('Failed to get cached content', error: e);
      return null;
    }
  }

  static List<CachedContent> getAllCachedContent() {
    try {
      return _cachedContentBoxInstance.values.toList();
    } catch (e) {
      AppLogger.error('Failed to get all cached content', error: e);
      return [];
    }
  }

  static Future<void> removeCachedContent(String id) async {
    try {
      await _cachedContentBoxInstance.delete(id);
      AppLogger.info('Cached content removed: $id');
    } catch (e) {
      AppLogger.error('Failed to remove cached content', error: e);
    }
  }

  /// Offline Activities Storage
  static Future<void> saveOfflineActivity(OfflineActivity activity) async {
    try {
      await _offlineActivitiesBoxInstance.put(activity.id, activity);
      AppLogger.info('Offline activity saved: ${activity.id}');
    } catch (e) {
      AppLogger.error('Failed to save offline activity', error: e);
      rethrow;
    }
  }

  static List<OfflineActivity> getOfflineActivities() {
    try {
      return _offlineActivitiesBoxInstance.values.toList();
    } catch (e) {
      AppLogger.error('Failed to get offline activities', error: e);
      return [];
    }
  }

  static Future<void> removeOfflineActivity(String id) async {
    try {
      await _offlineActivitiesBoxInstance.delete(id);
      AppLogger.info('Offline activity removed: $id');
    } catch (e) {
      AppLogger.error('Failed to remove offline activity', error: e);
    }
  }

  /// Sync Queue Storage
  static Future<void> addToSyncQueue(String id, Map<String, dynamic> data) async {
    try {
      await _syncQueueBoxInstance.put(id, data);
      AppLogger.info('Item added to sync queue: $id');
    } catch (e) {
      AppLogger.error('Failed to add to sync queue', error: e);
      rethrow;
    }
  }

  static Map<String, Map<String, dynamic>> getSyncQueue() {
    try {
      final Map<String, Map<String, dynamic>> queue = {};
      for (final key in _syncQueueBoxInstance.keys) {
        final value = _syncQueueBoxInstance.get(key);
        if (value != null) {
          queue[key.toString()] = value;
        }
      }
      return queue;
    } catch (e) {
      AppLogger.error('Failed to get sync queue', error: e);
      return {};
    }
  }

  static Future<void> removeFromSyncQueue(String id) async {
    try {
      await _syncQueueBoxInstance.delete(id);
      AppLogger.info('Item removed from sync queue: $id');
    } catch (e) {
      AppLogger.error('Failed to remove from sync queue', error: e);
    }
  }

  static Future<void> clearSyncQueue() async {
    try {
      await _syncQueueBoxInstance.clear();
      AppLogger.info('Sync queue cleared');
    } catch (e) {
      AppLogger.error('Failed to clear sync queue', error: e);
    }
  }

  /// Storage Management
  static Future<int> getStorageSize() async {
    try {
      int totalSize = 0;
      totalSize += _userPreferencesBoxInstance.length;
      totalSize += _cachedContentBoxInstance.length;
      totalSize += _offlineActivitiesBoxInstance.length;
      totalSize += _syncQueueBoxInstance.length;
      return totalSize;
    } catch (e) {
      AppLogger.error('Failed to get storage size', error: e);
      return 0;
    }
  }

  static Future<void> clearAllData() async {
    try {
      await _userPreferencesBoxInstance.clear();
      await _cachedContentBoxInstance.clear();
      await _offlineActivitiesBoxInstance.clear();
      await _syncQueueBoxInstance.clear();
      AppLogger.info('All local data cleared');
    } catch (e) {
      AppLogger.error('Failed to clear all data', error: e);
      rethrow;
    }
  }

  /// Cleanup old cached content
  static Future<void> cleanupOldContent({int maxAgeInDays = 7}) async {
    try {
      final cutoffDate = DateTime.now().subtract(Duration(days: maxAgeInDays));
      final keysToRemove = <String>[];

      for (final content in _cachedContentBoxInstance.values) {
        if (content.cachedAt.isBefore(cutoffDate)) {
          keysToRemove.add(content.id);
        }
      }

      for (final key in keysToRemove) {
        await _cachedContentBoxInstance.delete(key);
      }

      AppLogger.info('Cleaned up ${keysToRemove.length} old cached items');
    } catch (e) {
      AppLogger.error('Failed to cleanup old content', error: e);
    }
  }
}