# Cambridge AI Tutor Mobile App

A Flutter mobile application for the Cambridge AI Tutor platform, designed to provide safe and engaging learning experiences for primary school children.

## Features

### ✅ Implemented
- **Flutter App Architecture**: Clean architecture with BLoC state management
- **Child-Friendly Navigation**: Bottom navigation with floating action button
- **Offline-First Architecture**: Local data storage with Hive
- **Cross-Platform Sync**: Real-time synchronization across devices
- **Authentication System**: Parent login and child profile setup
- **State Management**: BLoC pattern for predictable state management
- **Local Storage**: Cached content, offline activities, and user preferences
- **Connectivity Monitoring**: Automatic online/offline detection
- **Child-Safe Design**: Age-appropriate UI with parental controls

### 🚧 Coming Soon
- AI Tutor Chat Interface
- Learning Activities and Exercises
- Progress Tracking and Analytics
- Voice Interaction Features
- Parent Dashboard
- Gamification Elements

## Architecture

### State Management
- **BLoC Pattern**: Used for all state management
- **Equatable**: For value equality in states and events
- **Dependency Injection**: GetIt for service location

### Local Storage
- **Hive**: NoSQL database for offline-first architecture
- **Cached Content**: Lessons, exercises, and explanations
- **Offline Activities**: User interactions stored locally
- **Sync Queue**: Pending operations for when online

### Navigation
- **GoRouter**: Declarative routing with deep link support
- **Child-Safe Routes**: Age-appropriate navigation patterns
- **Bottom Navigation**: Easy access to main features

## Project Structure

```
mobile/
├── lib/
│   ├── core/                    # Core functionality
│   │   ├── app.dart            # Main app widget
│   │   ├── di/                 # Dependency injection
│   │   ├── navigation/         # Routing configuration
│   │   ├── storage/            # Local storage models
│   │   ├── theme/              # App theming
│   │   ├── utils/              # Utilities and helpers
│   │   └── widgets/            # Reusable widgets
│   ├── features/               # Feature modules
│   │   ├── auth/               # Authentication
│   │   ├── home/               # Home screen
│   │   ├── learning/           # Learning activities
│   │   ├── navigation/         # Navigation state
│   │   ├── offline/            # Offline functionality
│   │   ├── progress/           # Progress tracking
│   │   ├── settings/           # App settings
│   │   ├── sync/               # Data synchronization
│   │   └── tutor/              # AI tutor chat
│   └── main.dart               # App entry point
├── test/                       # Unit and widget tests
├── android/                    # Android configuration
└── pubspec.yaml               # Dependencies
```

## Getting Started

### Prerequisites
- Flutter SDK (>=3.10.0)
- Dart SDK (>=3.0.0)
- Android Studio / VS Code
- Android SDK (for Android development)
- Xcode (for iOS development, macOS only)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mobile
   ```

2. **Install dependencies**
   ```bash
   flutter pub get
   ```

3. **Generate code**
   ```bash
   flutter packages pub run build_runner build
   ```

4. **Run the app**
   ```bash
   flutter run
   ```

### Testing

Run all tests:
```bash
flutter test
```

Run tests with coverage:
```bash
flutter test --coverage
```

## Key Components

### Authentication Flow
1. **Splash Screen**: App initialization and auth check
2. **Login Page**: Parent authentication
3. **Parent Setup**: Child profile configuration
4. **Main App**: Authenticated user experience

### Offline-First Architecture
- **Local Storage**: Hive database for offline data
- **Sync Queue**: Pending operations when offline
- **Connectivity Monitoring**: Automatic sync when online
- **Cached Content**: Lessons and exercises available offline

### Child Safety Features
- **Parental Controls**: Parent oversight of child activities
- **Age-Appropriate Content**: Content filtered by age/grade
- **Safe Navigation**: Child-friendly interface design
- **Data Privacy**: COPPA/GDPR compliant data handling

## State Management

### BLoC Pattern
Each feature has its own BLoC for state management:

- **AuthBloc**: User authentication and profile management
- **NavigationBloc**: App navigation and routing
- **OfflineBloc**: Offline functionality and connectivity
- **SyncBloc**: Cross-platform data synchronization

### Local Storage Models
- **UserPreferences**: Child profile and app settings
- **CachedContent**: Offline lessons and exercises
- **OfflineActivity**: User interactions and progress

## Design System

### Colors
- **Primary**: Child-friendly blue (#2196F3)
- **Accent**: Encouraging green (#4CAF50)
- **Subject Colors**: Mathematics (purple), English (indigo), Science (teal)

### Typography
- **Font Family**: Poppins (child-friendly, readable)
- **Sizes**: Responsive text scaling for different ages

### Components
- **Child-Safe Scaffold**: Bottom navigation with FAB
- **Rounded Corners**: Soft, friendly interface elements
- **Large Touch Targets**: Easy interaction for children

## Testing Strategy

### Unit Tests
- BLoC state management logic
- Local storage operations
- Utility functions and helpers

### Widget Tests
- UI component behavior
- Navigation flows
- User interaction handling

### Integration Tests
- End-to-end user workflows
- Cross-platform synchronization
- Offline/online transitions

## Performance Considerations

### Optimization
- **Lazy Loading**: Content loaded on demand
- **Image Caching**: Efficient image management
- **Memory Management**: Proper disposal of resources
- **Battery Optimization**: Efficient background processing

### Monitoring
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: App performance monitoring
- **User Analytics**: Child-safe usage analytics

## Security & Privacy

### Data Protection
- **Local Encryption**: Sensitive data encrypted at rest
- **Secure Transmission**: HTTPS for all API calls
- **Privacy Compliance**: COPPA and GDPR compliant

### Child Safety
- **Content Filtering**: Age-appropriate content only
- **Parental Oversight**: Parent monitoring capabilities
- **Safe Interactions**: Moderated AI responses

## Contributing

1. Follow Flutter/Dart style guidelines
2. Write tests for new features
3. Update documentation
4. Ensure child safety compliance
5. Test on multiple devices/screen sizes

## License

This project is part of the Cambridge AI Tutor platform. All rights reserved.