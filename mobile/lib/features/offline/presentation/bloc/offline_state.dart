part of 'offline_bloc.dart';

/// Base class for offline states
abstract class OfflineState extends Equatable {
  const OfflineState();

  @override
  List<Object?> get props => [];
}

/// Initial offline state
class OfflineInitial extends OfflineState {
  const OfflineInitial();
}

/// State when offline functionality is ready
class OfflineReady extends OfflineState {
  final bool isOnline;
  final int pendingSyncItems;

  const OfflineReady({
    required this.isOnline,
    required this.pendingSyncItems,
  });

  @override
  List<Object> get props => [isOnline, pendingSyncItems];
}

/// State when connectivity changes
class OfflineStateChanged extends OfflineState {
  final bool isOnline;
  final bool wasOnline;

  const OfflineStateChanged({
    required this.isOnline,
    required this.wasOnline,
  });

  @override
  List<Object> get props => [isOnline, wasOnline];
}

/// State when data is successfully cached
class OfflineDataCachedSuccess extends OfflineState {
  final String contentId;
  final bool isOnline;

  const OfflineDataCachedSuccess({
    required this.contentId,
    required this.isOnline,
  });

  @override
  List<Object> get props => [contentId, isOnline];
}

/// State when sync is in progress
class OfflineSyncInProgress extends OfflineState {
  const OfflineSyncInProgress();
}

/// State showing sync progress
class OfflineSyncProgress extends OfflineState {
  final int totalItems;
  final int syncedItems;
  final bool isOnline;

  const OfflineSyncProgress({
    required this.totalItems,
    required this.syncedItems,
    required this.isOnline,
  });

  double get progress => totalItems > 0 ? syncedItems / totalItems : 0.0;

  @override
  List<Object> get props => [totalItems, syncedItems, isOnline];
}

/// State when sync is completed successfully
class OfflineSyncCompleted extends OfflineState {
  final int syncedItems;
  final bool isOnline;

  const OfflineSyncCompleted({
    required this.syncedItems,
    required this.isOnline,
  });

  @override
  List<Object> get props => [syncedItems, isOnline];
}

/// State when sync is partially completed (some items failed)
class OfflineSyncPartiallyCompleted extends OfflineState {
  final int syncedItems;
  final List<String> failedItems;
  final bool isOnline;

  const OfflineSyncPartiallyCompleted({
    required this.syncedItems,
    required this.failedItems,
    required this.isOnline,
  });

  @override
  List<Object> get props => [syncedItems, failedItems, isOnline];
}

/// State when sync queue is updated
class OfflineQueueUpdated extends OfflineState {
  final int queueSize;
  final bool isOnline;

  const OfflineQueueUpdated({
    required this.queueSize,
    required this.isOnline,
  });

  @override
  List<Object> get props => [queueSize, isOnline];
}

/// State when an error occurs
class OfflineError extends OfflineState {
  final String message;

  const OfflineError(this.message);

  @override
  List<Object> get props => [message];
}