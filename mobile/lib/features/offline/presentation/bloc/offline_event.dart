part of 'offline_bloc.dart';

/// Base class for offline events
abstract class OfflineEvent extends Equatable {
  const OfflineEvent();

  @override
  List<Object?> get props => [];
}

/// Event to initialize offline functionality
class OfflineInitialized extends OfflineEvent {
  const OfflineInitialized();
}

/// Event fired when connectivity changes
class OfflineConnectivityChanged extends OfflineEvent {
  final bool isOnline;

  const OfflineConnectivityChanged(this.isOnline);

  @override
  List<Object> get props => [isOnline];
}

/// Event to cache data for offline use
class OfflineDataCached extends OfflineEvent {
  final CachedContent content;

  const OfflineDataCached(this.content);

  @override
  List<Object> get props => [content];
}

/// Event to request sync of offline data
class OfflineDataSyncRequested extends OfflineEvent {
  const OfflineDataSyncRequested();
}

/// Event to add item to sync queue
class OfflineQueueProcessed extends OfflineEvent {
  final String itemId;
  final Map<String, dynamic> data;

  const OfflineQueueProcessed({
    required this.itemId,
    required this.data,
  });

  @override
  List<Object> get props => [itemId, data];
}