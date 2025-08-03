part of 'sync_bloc.dart';

/// Base class for sync events
abstract class SyncEvent extends Equatable {
  const SyncEvent();

  @override
  List<Object?> get props => [];
}

/// Event to initialize sync functionality
class SyncInitialized extends SyncEvent {
  const SyncInitialized();
}

/// Event to request data synchronization
class SyncRequested extends SyncEvent {
  final bool isAutomatic;

  const SyncRequested({this.isAutomatic = false});

  @override
  List<Object> get props => [isAutomatic];
}

/// Event to update sync progress
class SyncProgressUpdated extends SyncEvent {
  final int totalItems;
  final int syncedItems;

  const SyncProgressUpdated({
    required this.totalItems,
    required this.syncedItems,
  });

  @override
  List<Object> get props => [totalItems, syncedItems];
}

/// Event to track activity for sync
class SyncActivityTracked extends SyncEvent {
  final OfflineActivity activity;

  const SyncActivityTracked(this.activity);

  @override
  List<Object> get props => [activity];
}

/// Event to resolve sync conflict
class SyncConflictResolved extends SyncEvent {
  final String conflictId;
  final ConflictResolution resolution;

  const SyncConflictResolved({
    required this.conflictId,
    required this.resolution,
  });

  @override
  List<Object> get props => [conflictId, resolution];
}

/// Enum for conflict resolution strategies
enum ConflictResolution {
  useLocal,
  useRemote,
  merge,
}