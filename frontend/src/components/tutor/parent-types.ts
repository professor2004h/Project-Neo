// Types for parent dashboard components

export interface ChildProfile {
  child_id: string;
  parent_id: string;
  name: string;
  age: number;
  grade_level: number;
  learning_preferences: {
    learning_style: 'visual' | 'auditory' | 'kinesthetic';
    preferred_subjects: string[];
    difficulty_preference: 'easy' | 'medium' | 'challenging';
  };
  curriculum_progress: {
    math: number;
    esl: number;
    science: number;
  };
  safety_settings: {
    session_time_limit: number; // minutes
    content_filtering: 'strict' | 'moderate' | 'relaxed';
    voice_interaction_enabled: boolean;
    image_sharing_enabled: boolean;
  };
  created_at: Date;
}

export interface ParentInsight {
  insight_id: string;
  child_id: string;
  type: 'strength' | 'improvement' | 'suggestion' | 'achievement';
  title: string;
  description: string;
  action_items: string[];
  priority: 'low' | 'medium' | 'high';
  created_at: Date;
}

export interface WeeklyReport {
  report_id: string;
  child_id: string;
  week_start: Date;
  week_end: Date;
  total_study_time: number; // minutes
  sessions_completed: number;
  topics_practiced: string[];
  achievements: Achievement[];
  progress_summary: {
    overall_improvement: number;
    subject_breakdown: {
      math: { score: number; change: number };
      esl: { score: number; change: number };
      science: { score: number; change: number };
    };
  };
  parent_insights: ParentInsight[];
  recommendations: string[];
}

export interface Achievement {
  achievement_id: string;
  title: string;
  description: string;
  icon: string;
  earned_at: Date;
  category: 'progress' | 'consistency' | 'mastery' | 'effort';
}

export interface ParentalControl {
  control_id: string;
  child_id: string;
  setting_name: string;
  setting_value: any;
  description: string;
  category: 'safety' | 'time' | 'content' | 'privacy';
  updated_at: Date;
}

export interface StudySchedule {
  schedule_id: string;
  child_id: string;
  day_of_week: number; // 0-6
  start_time: string; // HH:mm
  duration: number; // minutes
  subjects: string[];
  is_active: boolean;
}

export interface ParentDashboardData {
  children: ChildProfile[];
  selected_child?: ChildProfile;
  weekly_reports: WeeklyReport[];
  recent_insights: ParentInsight[];
  upcoming_schedules: StudySchedule[];
  family_achievements: Achievement[];
}

export interface ParentDashboardProps {
  parentId: string;
  onChildSelect?: (child: ChildProfile) => void;
  onSettingsChange?: (settings: any) => void;
}

export interface ParentSettingsProps {
  childId: string;
  currentSettings: ParentalControl[];
  onSettingsUpdate: (settings: ParentalControl[]) => void;
}

export interface ReportViewerProps {
  report: WeeklyReport;
  showDetails?: boolean;
  onInsightAction?: (insight: ParentInsight, action: string) => void;
}