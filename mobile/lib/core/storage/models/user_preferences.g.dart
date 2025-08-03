// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_preferences.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class UserPreferencesAdapter extends TypeAdapter<UserPreferences> {
  @override
  final int typeId = 0;

  @override
  UserPreferences read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return UserPreferences(
      userId: fields[0] as String,
      childName: fields[1] as String,
      age: fields[2] as int,
      gradeLevel: fields[3] as int,
      preferredLanguage: fields[4] as String,
      learningStyle: fields[5] as String,
      favoriteSubjects: (fields[6] as List).cast<String>(),
      difficultySettings: (fields[7] as Map).cast<String, dynamic>(),
      soundEnabled: fields[8] as bool,
      notificationsEnabled: fields[9] as bool,
      parentalControlsEnabled: fields[10] as bool,
      lastUpdated: fields[11] as DateTime,
      customSettings: (fields[12] as Map).cast<String, dynamic>(),
    );
  }

  @override
  void write(BinaryWriter writer, UserPreferences obj) {
    writer
      ..writeByte(13)
      ..writeByte(0)
      ..write(obj.userId)
      ..writeByte(1)
      ..write(obj.childName)
      ..writeByte(2)
      ..write(obj.age)
      ..writeByte(3)
      ..write(obj.gradeLevel)
      ..writeByte(4)
      ..write(obj.preferredLanguage)
      ..writeByte(5)
      ..write(obj.learningStyle)
      ..writeByte(6)
      ..write(obj.favoriteSubjects)
      ..writeByte(7)
      ..write(obj.difficultySettings)
      ..writeByte(8)
      ..write(obj.soundEnabled)
      ..writeByte(9)
      ..write(obj.notificationsEnabled)
      ..writeByte(10)
      ..write(obj.parentalControlsEnabled)
      ..writeByte(11)
      ..write(obj.lastUpdated)
      ..writeByte(12)
      ..write(obj.customSettings);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserPreferencesAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}