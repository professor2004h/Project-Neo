part of 'sync_bloc.dart';

/// Base class for sync states
abstract class SyncState extends Equatable {
  const SyncState();

  @override
  List<Object?> get props => [];
}

/// Initial sync state
class SyncInitial extends SyncState {
  const SyncInitial();
}

/// State when sync is ready
class SyncReady extends SyncState {
  const SyncReady();
}

/// State when sync is in progress
class SyncInProgress extends SyncState {
  const SyncInProgress();
}

/// State showing sync progress
class SyncProgress extends SyncState {
  final int totalItems;
  final int syncedItems;

  const SyncProgress({
    required this.totalItems,
    required this.syncedItems,
  });

  double get progress => totalItems > 0 ? syncedItems / totalItems : 0.0;

  @override
  List<Object> get props => [totalItems, syncedItems];
}

/// State when sync is completed successfully
class SyncCompleted extends SyncState {
  final int syncedItems;
  final int conflictsResolved;
  final DateTime? lastSyncTime;

  const SyncCompleted({
    required this.syncedItems,
    required this.conflictsResolved,
    this.lastSyncTime,
  });

  @override
  List<Object?> get props => [syncedItems, conflictsResolved, lastSyncTime];
}

/// State when sync is partially completed
class SyncPartiallyCompleted extends SyncState {
  final int syncedItems;
  final List<String> failedItems;
  final int conflictsResolved;
  final DateTime? lastSyncTime;

  const SyncPartiallyCompleted({
    required this.syncedItems,
    required this.failedItems,
    required this.conflictsResolved,
    this.lastSyncTime,
  });

  @override
  List<Object?> get props => [syncedItems, failedItems, conflictsResolved, lastSyncTime];
}

/// State when activity is queued for sync
class SyncActivityQueued extends SyncState {
  final String activityId;
  final int queueSize;

  const SyncActivityQueued({
    required this.activityId,
    required this.queueSize,
  });

  @override
  List<Object> get props => [activityId, queueSize];
}

/// State when sync conflict is resolved
class SyncConflictResolvedState extends SyncState {
  final String conflictId;
  final ConflictResolution resolution;

  const SyncConflictResolvedState({
    required this.conflictId,
    required this.resolution,
  });

  @override
  List<Object> get props => [conflictId, resolution];
}

/// State when sync error occurs
class SyncError extends SyncState {
  final String message;

  const SyncError(this.message);

  @override
  List<Object> get props => [message];
}