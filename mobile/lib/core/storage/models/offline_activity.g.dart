// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'offline_activity.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class OfflineActivityAdapter extends TypeAdapter<OfflineActivity> {
  @override
  final int typeId = 2;

  @override
  OfflineActivity read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return OfflineActivity(
      id: fields[0] as String,
      userId: fields[1] as String,
      type: fields[2] as String,
      subject: fields[3] as String,
      activityData: (fields[4] as Map).cast<String, dynamic>(),
      createdAt: fields[5] as DateTime,
      completedAt: fields[6] as DateTime?,
      isSynced: fields[7] as bool,
      performanceData: (fields[8] as Map).cast<String, dynamic>(),
      attachments: (fields[9] as List).cast<String>(),
      metadata: (fields[10] as Map).cast<String, dynamic>(),
    );
  }

  @override
  void write(BinaryWriter writer, OfflineActivity obj) {
    writer
      ..writeByte(11)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.userId)
      ..writeByte(2)
      ..write(obj.type)
      ..writeByte(3)
      ..write(obj.subject)
      ..writeByte(4)
      ..write(obj.activityData)
      ..writeByte(5)
      ..write(obj.createdAt)
      ..writeByte(6)
      ..write(obj.completedAt)
      ..writeByte(7)
      ..write(obj.isSynced)
      ..writeByte(8)
      ..write(obj.performanceData)
      ..writeByte(9)
      ..write(obj.attachments)
      ..writeByte(10)
      ..write(obj.metadata);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is OfflineActivityAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}