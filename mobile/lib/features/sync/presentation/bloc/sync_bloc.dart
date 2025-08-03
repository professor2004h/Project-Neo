import 'dart:async';

import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/storage/local_storage.dart';
import '../../../../core/utils/logger.dart';

part 'sync_event.dart';
part 'sync_state.dart';

/// BLoC for managing cross-platform data synchronization
class SyncBloc extends Bloc<SyncEvent, SyncState> {
  Timer? _periodicSyncTimer;

  SyncBloc() : super(const SyncInitial()) {
    on<SyncInitialized>(_onInitialized);
    on<SyncRequested>(_onSyncRequested);
    on<SyncProgressUpdated>(_onProgressUpdated);
    on<SyncActivityTracked>(_onActivityTracked);
    on<SyncConflictResolved>(_onConflictResolved);
  }

  void _onInitialized(SyncInitialized event, Emitter<SyncState> emit) async {
    try {
      AppLogger.info('Sync bloc initialized');
      
      // Start periodic sync (every 5 minutes when online)
      _periodicSyncTimer = Timer.periodic(
        const Duration(minutes: 5),
        (_) => add(const SyncRequested(isAutomatic: true)),
      );

      emit(const SyncReady());
    } catch (e, stackTrace) {
      AppLogger.error('Failed to initialize sync bloc', error: e, stackTrace: stackTrace);
      emit(const SyncError('Failed to initialize synchronization'));
    }
  }

  void _onSyncRequested(SyncRequested event, Emitter<SyncState> emit) async {
    try {
      if (state is SyncInProgress) {
        AppLogger.info('Sync already in progress, skipping request');
        return;
      }

      emit(const SyncInProgress());

      // Get items to sync
      final syncQueue = LocalStorage.getSyncQueue();
      final offlineActivities = LocalStorage.getOfflineActivities()
          .where((activity) => activity.needsSync)
          .toList();

      final totalItems = syncQueue.length + offlineActivities.length;

      if (totalItems == 0) {
        AppLogger.info('No items to sync');
        emit(const SyncCompleted(
          syncedItems: 0,
          conflictsResolved: 0,
          lastSyncTime: null,
        ));
        return;
      }

      AppLogger.info('Starting sync of $totalItems items (automatic: ${event.isAutomatic})');

      int syncedCount = 0;
      int conflictsResolved = 0;
      final List<String> failedItems = [];

      // Sync queue items
      for (final entry in syncQueue.entries) {
        try {
          await _syncQueueItem(entry.key, entry.value);
          await LocalStorage.removeFromSyncQueue(entry.key);
          syncedCount++;

          // Emit progress
          add(SyncProgressUpdated(
            totalItems: totalItems,
            syncedItems: syncedCount,
          ));
        } catch (e) {
          AppLogger.error('Failed to sync queue item: ${entry.key}', error: e);
          failedItems.add(entry.key);
        }
      }

      // Sync offline activities
      for (final activity in offlineActivities) {
        try {
          await _syncOfflineActivity(activity);
          final syncedActivity = activity.synced();
          await LocalStorage.saveOfflineActivity(syncedActivity);
          syncedCount++;

          // Emit progress
          add(SyncProgressUpdated(
            totalItems: totalItems,
            syncedItems: syncedCount,
          ));
        } catch (e) {
          AppLogger.error('Failed to sync activity: ${activity.id}', error: e);
          failedItems.add(activity.id);
        }
      }

      final lastSyncTime = DateTime.now();

      if (failedItems.isEmpty) {
        AppLogger.info('Sync completed successfully: $syncedCount items');
        emit(SyncCompleted(
          syncedItems: syncedCount,
          conflictsResolved: conflictsResolved,
          lastSyncTime: lastSyncTime,
        ));
      } else {
        AppLogger.warning('Sync completed with errors: ${failedItems.length} failed');
        emit(SyncPartiallyCompleted(
          syncedItems: syncedCount,
          failedItems: failedItems,
          conflictsResolved: conflictsResolved,
          lastSyncTime: lastSyncTime,
        ));
      }
    } catch (e, stackTrace) {
      AppLogger.error('Sync process failed', error: e, stackTrace: stackTrace);
      emit(const SyncError('Synchronization failed'));
    }
  }

  void _onProgressUpdated(SyncProgressUpdated event, Emitter<SyncState> emit) {
    emit(SyncProgress(
      totalItems: event.totalItems,
      syncedItems: event.syncedItems,
    ));
  }

  void _onActivityTracked(SyncActivityTracked event, Emitter<SyncState> emit) async {
    try {
      // Save activity for later sync
      await LocalStorage.saveOfflineActivity(event.activity);
      
      // Add to sync queue if online
      await LocalStorage.addToSyncQueue(
        event.activity.id,
        event.activity.toJson(),
      );

      AppLogger.info('Activity tracked for sync: ${event.activity.id}');
      
      emit(SyncActivityQueued(
        activityId: event.activity.id,
        queueSize: LocalStorage.getSyncQueue().length,
      ));
    } catch (e, stackTrace) {
      AppLogger.error('Failed to track activity for sync', error: e, stackTrace: stackTrace);
      emit(const SyncError('Failed to track activity'));
    }
  }

  void _onConflictResolved(SyncConflictResolved event, Emitter<SyncState> emit) async {
    try {
      // Handle conflict resolution based on strategy
      switch (event.resolution) {
        case ConflictResolution.useLocal:
          // Keep local version, mark as synced
          break;
        case ConflictResolution.useRemote:
          // Use remote version, update local
          break;
        case ConflictResolution.merge:
          // Merge both versions
          break;
      }

      AppLogger.info('Sync conflict resolved: ${event.conflictId}');
      
      emit(SyncConflictResolvedState(
        conflictId: event.conflictId,
        resolution: event.resolution,
      ));
    } catch (e, stackTrace) {
      AppLogger.error('Failed to resolve sync conflict', error: e, stackTrace: stackTrace);
      emit(const SyncError('Failed to resolve synchronization conflict'));
    }
  }

  /// Sync a queue item (simulate API call)
  Future<void> _syncQueueItem(String itemId, Map<String, dynamic> data) async {
    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 300));
    
    // Here you would make actual API calls
    // await apiService.syncData(itemId, data);
  }

  /// Sync an offline activity (simulate API call)
  Future<void> _syncOfflineActivity(OfflineActivity activity) async {
    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 500));
    
    // Here you would make actual API calls
    // await apiService.syncActivity(activity.toJson());
  }

  @override
  Future<void> close() {
    _periodicSyncTimer?.cancel();
    return super.close();
  }
}