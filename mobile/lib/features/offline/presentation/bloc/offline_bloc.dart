import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/storage/local_storage.dart';
import '../../../../core/utils/logger.dart';

part 'offline_event.dart';
part 'offline_state.dart';

/// BLoC for managing offline functionality and connectivity
class OfflineBloc extends Bloc<OfflineEvent, OfflineState> {
  final Connectivity _connectivity = Connectivity();
  StreamSubscription<ConnectivityResult>? _connectivitySubscription;
  bool _isOnline = true;

  OfflineBloc() : super(const OfflineInitial()) {
    on<OfflineInitialized>(_onInitialized);
    on<OfflineConnectivityChanged>(_onConnectivityChanged);
    on<OfflineDataCached>(_onDataCached);
    on<OfflineDataSyncRequested>(_onDataSyncRequested);
    on<OfflineQueueProcessed>(_onQueueProcessed);
  }

  void _onInitialized(OfflineInitialized event, Emitter<OfflineState> emit) async {
    try {
      // Check initial connectivity
      final connectivityResult = await _connectivity.checkConnectivity();
      _isOnline = connectivityResult != ConnectivityResult.none;

      // Listen to connectivity changes
      _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
        (ConnectivityResult result) {
          add(OfflineConnectivityChanged(result != ConnectivityResult.none));
        },
      );

      // Get sync queue size
      final syncQueue = LocalStorage.getSyncQueue();
      final pendingItems = syncQueue.length;

      AppLogger.info('Offline bloc initialized - Online: $_isOnline, Pending sync: $pendingItems');

      emit(OfflineReady(
        isOnline: _isOnline,
        pendingSyncItems: pendingItems,
      ));

      // If online and have pending items, trigger sync
      if (_isOnline && pendingItems > 0) {
        add(const OfflineDataSyncRequested());
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to initialize offline bloc', error: e, stackTrace: stackTrace);
      emit(const OfflineError('Failed to initialize offline functionality'));
    }
  }

  void _onConnectivityChanged(OfflineConnectivityChanged event, Emitter<OfflineState> emit) async {
    final wasOnline = _isOnline;
    _isOnline = event.isOnline;

    AppLogger.info('Connectivity changed: ${_isOnline ? 'Online' : 'Offline'}');

    emit(OfflineStateChanged(
      isOnline: _isOnline,
      wasOnline: wasOnline,
    ));

    // If came back online, check for pending sync items
    if (_isOnline && !wasOnline) {
      final syncQueue = LocalStorage.getSyncQueue();
      if (syncQueue.isNotEmpty) {
        add(const OfflineDataSyncRequested());
      }
    }
  }

  void _onDataCached(OfflineDataCached event, Emitter<OfflineState> emit) async {
    try {
      await LocalStorage.cacheContent(event.content);
      
      AppLogger.info('Data cached successfully: ${event.content.id}');
      
      emit(OfflineDataCachedSuccess(
        contentId: event.content.id,
        isOnline: _isOnline,
      ));
    } catch (e, stackTrace) {
      AppLogger.error('Failed to cache data', error: e, stackTrace: stackTrace);
      emit(const OfflineError('Failed to cache data for offline use'));
    }
  }

  void _onDataSyncRequested(OfflineDataSyncRequested event, Emitter<OfflineState> emit) async {
    if (!_isOnline) {
      AppLogger.warning('Sync requested but device is offline');
      return;
    }

    try {
      emit(const OfflineSyncInProgress());

      final syncQueue = LocalStorage.getSyncQueue();
      final totalItems = syncQueue.length;

      if (totalItems == 0) {
        emit(OfflineSyncCompleted(
          syncedItems: 0,
          isOnline: _isOnline,
        ));
        return;
      }

      AppLogger.info('Starting sync of $totalItems items');

      int syncedCount = 0;
      final failedItems = <String>[];

      // Process sync queue items
      for (final entry in syncQueue.entries) {
        try {
          // Here you would call your API service to sync the data
          // For now, we'll simulate the sync process
          await _simulateSync(entry.key, entry.value);
          
          await LocalStorage.removeFromSyncQueue(entry.key);
          syncedCount++;
          
          // Emit progress update
          emit(OfflineSyncProgress(
            totalItems: totalItems,
            syncedItems: syncedCount,
            isOnline: _isOnline,
          ));
        } catch (e) {
          AppLogger.error('Failed to sync item: ${entry.key}', error: e);
          failedItems.add(entry.key);
        }
      }

      if (failedItems.isEmpty) {
        AppLogger.info('Sync completed successfully: $syncedCount items');
        emit(OfflineSyncCompleted(
          syncedItems: syncedCount,
          isOnline: _isOnline,
        ));
      } else {
        AppLogger.warning('Sync completed with errors: ${failedItems.length} failed');
        emit(OfflineSyncPartiallyCompleted(
          syncedItems: syncedCount,
          failedItems: failedItems,
          isOnline: _isOnline,
        ));
      }
    } catch (e, stackTrace) {
      AppLogger.error('Sync process failed', error: e, stackTrace: stackTrace);
      emit(const OfflineError('Failed to sync offline data'));
    }
  }

  void _onQueueProcessed(OfflineQueueProcessed event, Emitter<OfflineState> emit) async {
    try {
      await LocalStorage.addToSyncQueue(event.itemId, event.data);
      
      AppLogger.info('Item added to sync queue: ${event.itemId}');
      
      emit(OfflineQueueUpdated(
        queueSize: LocalStorage.getSyncQueue().length,
        isOnline: _isOnline,
      ));

      // If online, trigger immediate sync
      if (_isOnline) {
        add(const OfflineDataSyncRequested());
      }
    } catch (e, stackTrace) {
      AppLogger.error('Failed to add item to sync queue', error: e, stackTrace: stackTrace);
      emit(const OfflineError('Failed to queue data for sync'));
    }
  }

  /// Simulate sync process (replace with actual API calls)
  Future<void> _simulateSync(String itemId, Map<String, dynamic> data) async {
    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 500));
    
    // Here you would make actual API calls to sync the data
    // For example:
    // await apiService.syncActivity(data);
    // await apiService.syncProgress(data);
    // etc.
  }

  @override
  Future<void> close() {
    _connectivitySubscription?.cancel();
    return super.close();
  }
}