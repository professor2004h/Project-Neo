// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cached_content.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class CachedContentAdapter extends TypeAdapter<CachedContent> {
  @override
  final int typeId = 1;

  @override
  CachedContent read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return CachedContent(
      id: fields[0] as String,
      type: fields[1] as String,
      subject: fields[2] as String,
      gradeLevel: fields[3] as int,
      title: fields[4] as String,
      content: (fields[5] as Map).cast<String, dynamic>(),
      cachedAt: fields[6] as DateTime,
      expiresAt: fields[7] as DateTime?,
      accessCount: fields[8] as int,
      lastAccessed: fields[9] as DateTime,
      tags: (fields[10] as List).cast<String>(),
      metadata: (fields[11] as Map).cast<String, dynamic>(),
    );
  }

  @override
  void write(BinaryWriter writer, CachedContent obj) {
    writer
      ..writeByte(12)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.type)
      ..writeByte(2)
      ..write(obj.subject)
      ..writeByte(3)
      ..write(obj.gradeLevel)
      ..writeByte(4)
      ..write(obj.title)
      ..writeByte(5)
      ..write(obj.content)
      ..writeByte(6)
      ..write(obj.cachedAt)
      ..writeByte(7)
      ..write(obj.expiresAt)
      ..writeByte(8)
      ..write(obj.accessCount)
      ..writeByte(9)
      ..write(obj.lastAccessed)
      ..writeByte(10)
      ..write(obj.tags)
      ..writeByte(11)
      ..write(obj.metadata);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CachedContentAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}