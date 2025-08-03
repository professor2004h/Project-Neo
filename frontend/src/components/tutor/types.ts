// Types for tutor interface components

export interface TutorMessage {
  id: string;
  content: string;
  sender: 'user' | 'tutor';
  timestamp: Date;
  type: 'text' | 'voice' | 'image';
  metadata?: {
    topic_id?: string;
    difficulty_level?: number;
    learning_objective?: string;
    cambridge_code?: string;
  };
}

export interface TutorSession {
  session_id: string;
  user_id: string;
  started_at: Date;
  ended_at?: Date;
  messages: TutorMessage[];
  context: {
    current_topic?: string;
    grade_level?: number;
    subject?: 'math' | 'esl' | 'science';
    learning_style?: 'visual' | 'auditory' | 'kinesthetic';
  };
}

export interface ProgressData {
  user_id: string;
  subject: 'math' | 'esl' | 'science';
  topics: TopicProgress[];
  overall_score: number;
  last_updated: Date;
}

export interface TopicProgress {
  topic_id: string;
  topic_name: string;
  cambridge_code: string;
  skill_level: number; // 0-1
  confidence_score: number; // 0-1
  last_practiced: Date;
  mastery_indicators: {
    understanding: number;
    application: number;
    retention: number;
  };
  improvement_areas: string[];
}

export interface LearningActivityData {
  activity_id: string;
  topic_id: string;
  activity_type: 'practice' | 'assessment' | 'explanation' | 'game';
  title: string;
  description: string;
  difficulty_level: number;
  estimated_duration: number; // minutes
  completion_status: 'not_started' | 'in_progress' | 'completed';
  score?: number;
}

export interface ChatInputProps {
  onSendMessage: (message: string, type?: 'text' | 'voice') => void;
  disabled?: boolean;
  placeholder?: string;
  supportVoice?: boolean;
}

export interface ProgressVisualizationProps {
  data: ProgressData;
  timeframe?: 'week' | 'month' | 'term';
  showDetails?: boolean;
}

export interface TutorInterfaceProps {
  userId: string;
  gradeLevel: number;
  subject: 'math' | 'esl' | 'science';
  onSessionEnd?: (session: TutorSession) => void;
}