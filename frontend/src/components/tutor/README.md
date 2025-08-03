# Cambridge AI Tutor Components

This directory contains React components for the Cambridge AI Tutor interface, providing an interactive learning experience for primary school children following the Cambridge curriculum.

## Components Overview

### Main Interface Components

#### `TutorInterface`
The main container component that orchestrates the entire tutor experience.

**Props:**
- `userId: string` - Unique identifier for the student
- `gradeLevel: number` - Student's grade level (1-6)
- `subject: 'math' | 'esl' | 'science'` - Subject being studied
- `onSessionEnd?: (session: TutorSession) => void` - Callback when session ends

**Features:**
- Tabbed interface with Chat, Progress, Activities, and Skills views
- Session management and data loading
- Responsive design for various screen sizes

#### `TutorChat`
Interactive chat interface for AI tutor conversations.

**Props:**
- `session: TutorSession` - Current tutor session data
- `onSessionUpdate: (session: TutorSession) => void` - Session update callback
- `onSessionEnd: () => void` - Session end callback

**Features:**
- Real-time messaging with AI tutor
- Message history and context preservation
- Typing indicators and loading states
- Auto-scroll to latest messages

#### `TutorMessage`
Individual message component for chat display.

**Props:**
- `message: TutorMessage` - Message data
- `isOwn: boolean` - Whether message is from current user

**Features:**
- Different styling for user vs tutor messages
- Support for text, voice, and image message types
- Metadata badges for curriculum codes and topics
- Timestamp display

#### `TutorInput`
Input component for sending messages to the AI tutor.

**Props:**
- `onSendMessage: (message: string, type?: 'text' | 'voice') => void` - Message send callback
- `disabled?: boolean` - Whether input is disabled
- `placeholder?: string` - Input placeholder text
- `supportVoice?: boolean` - Whether voice input is supported

**Features:**
- Text input with auto-resize
- Voice recording support
- Image and file attachment buttons
- Quick action buttons for common requests
- Enter to send, Shift+Enter for new line

### Progress Visualization Components

#### `ProgressVisualization`
Comprehensive progress display with charts and detailed breakdowns.

**Props:**
- `data: ProgressData` - Student progress data
- `timeframe?: 'week' | 'month' | 'term'` - Time period for progress view
- `showDetails?: boolean` - Whether to show detailed breakdowns

**Features:**
- Overall progress summary
- Topics mastered count
- Interactive progress chart
- Detailed topic breakdowns with mastery indicators

#### `ProgressChart`
Interactive chart component for visualizing progress over time.

**Props:**
- `data: ProgressData` - Progress data for chart
- `timeframe: 'week' | 'month' | 'term'` - Chart time period

**Features:**
- SVG-based line chart with data points
- Responsive design
- Hover tooltips with detailed information
- Color-coded progress indicators

#### `SkillsOverview`
Detailed view of student skills across all topics.

**Props:**
- `topics: TopicProgress[]` - Array of topic progress data
- `subject: 'math' | 'esl' | 'science'` - Subject being viewed
- `gradeLevel: number` - Student's grade level

**Features:**
- Skills statistics overview
- Priority topics identification
- Mastery breakdown by topic
- Cambridge curriculum code mapping

#### `LearningActivity`
Interactive card component for learning activities.

**Props:**
- `activity: LearningActivityData` - Activity data
- `onStart: () => void` - Activity start callback
- `onComplete: (score: number) => void` - Activity completion callback

**Features:**
- Activity type icons and color coding
- Difficulty level indicators
- Progress tracking and scoring
- Achievement badges for high performance

## Usage Examples

### Basic Tutor Interface

```tsx
import { TutorInterface } from '@/components/tutor';

function MyTutorPage() {
  const handleSessionEnd = (session) => {
    console.log('Session ended:', session);
  };

  return (
    <TutorInterface
      userId="student123"
      gradeLevel={3}
      subject="math"
      onSessionEnd={handleSessionEnd}
    />
  );
}
```

### Standalone Chat Component

```tsx
import { TutorChat } from '@/components/tutor';

function ChatPage() {
  const [session, setSession] = useState(initialSession);

  return (
    <TutorChat
      session={session}
      onSessionUpdate={setSession}
      onSessionEnd={() => console.log('Chat ended')}
    />
  );
}
```

### Progress Display

```tsx
import { ProgressVisualization } from '@/components/tutor';

function ProgressPage({ progressData }) {
  return (
    <ProgressVisualization
      data={progressData}
      timeframe="week"
      showDetails={true}
    />
  );
}
```

## Responsive Design

All components are built with responsive design principles:

- **Mobile (< 768px)**: Single column layout, touch-friendly interactions
- **Tablet (768px - 1024px)**: Two-column layouts where appropriate
- **Desktop (> 1024px)**: Full multi-column layouts with optimal spacing

## Accessibility Features

- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes
- Focus management

## Testing

Components include comprehensive unit tests using Jest and React Testing Library:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

## Styling

Components use Tailwind CSS with the existing design system:

- Consistent color palette
- Responsive utilities
- Dark mode support
- Animation and transition effects

## Data Types

See `types.ts` for complete type definitions including:

- `TutorMessage` - Individual chat messages
- `TutorSession` - Complete chat sessions
- `ProgressData` - Student progress information
- `TopicProgress` - Individual topic progress
- `LearningActivityData` - Activity information

## Integration Notes

These components are designed to integrate with:

- Backend tutor API endpoints
- Real-time WebSocket connections
- Progress tracking systems
- Cambridge curriculum databases
- Voice recognition services
- File upload systems

## Future Enhancements

Planned improvements include:

- Real-time collaboration features
- Advanced voice interaction
- Augmented reality learning aids
- Offline mode support
- Multi-language support
- Advanced analytics dashboard