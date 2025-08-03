'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TutorChat } from './tutor-chat';
import { ProgressVisualization } from './progress-visualization';
import { LearningActivity } from './learning-activity';
import { SkillsOverview } from './skills-overview';
import { TutorInterfaceProps, TutorSession, ProgressData, LearningActivityData } from './types';
import { cn } from '@/lib/utils';

export function TutorInterface({ 
  userId, 
  gradeLevel, 
  subject, 
  onSessionEnd 
}: TutorInterfaceProps) {
  const [activeTab, setActiveTab] = useState('chat');
  const [currentSession, setCurrentSession] = useState<TutorSession | null>(null);
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [activities, setActivities] = useState<LearningActivityData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session and load data
  useEffect(() => {
    const initializeSession = async () => {
      try {
        setIsLoading(true);
        
        // Create new tutor session
        const session: TutorSession = {
          session_id: `session_${Date.now()}`,
          user_id: userId,
          started_at: new Date(),
          messages: [],
          context: {
            grade_level: gradeLevel,
            subject: subject,
            learning_style: 'visual' // Default, could be loaded from user preferences
          }
        };
        
        setCurrentSession(session);
        
        // Load progress data (mock data for now)
        const mockProgressData: ProgressData = {
          user_id: userId,
          subject: subject,
          topics: [
            {
              topic_id: 'fractions_basic',
              topic_name: 'Basic Fractions',
              cambridge_code: 'M3N1.1',
              skill_level: 0.75,
              confidence_score: 0.8,
              last_practiced: new Date(Date.now() - 86400000), // Yesterday
              mastery_indicators: {
                understanding: 0.8,
                application: 0.7,
                retention: 0.75
              },
              improvement_areas: ['Word problems', 'Mixed numbers']
            },
            {
              topic_id: 'multiplication_tables',
              topic_name: 'Multiplication Tables',
              cambridge_code: 'M3N2.3',
              skill_level: 0.9,
              confidence_score: 0.85,
              last_practiced: new Date(),
              mastery_indicators: {
                understanding: 0.9,
                application: 0.85,
                retention: 0.9
              },
              improvement_areas: []
            }
          ],
          overall_score: 0.82,
          last_updated: new Date()
        };
        
        setProgressData(mockProgressData);
        
        // Load activities
        const mockActivities: LearningActivityData[] = [
          {
            activity_id: 'act_1',
            topic_id: 'fractions_basic',
            activity_type: 'practice',
            title: 'Fraction Practice',
            description: 'Practice identifying and comparing fractions',
            difficulty_level: 3,
            estimated_duration: 15,
            completion_status: 'not_started'
          },
          {
            activity_id: 'act_2',
            topic_id: 'multiplication_tables',
            activity_type: 'game',
            title: 'Times Tables Challenge',
            description: 'Fun multiplication game with rewards',
            difficulty_level: 2,
            estimated_duration: 10,
            completion_status: 'completed',
            score: 85
          }
        ];
        
        setActivities(mockActivities);
        
      } catch (error) {
        console.error('Failed to initialize tutor session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeSession();
  }, [userId, gradeLevel, subject]);

  const handleSessionEnd = () => {
    if (currentSession) {
      const endedSession = {
        ...currentSession,
        ended_at: new Date()
      };
      onSessionEnd?.(endedSession);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96" role="status" aria-label="Loading tutor interface">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto p-4 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Cambridge AI Tutor - {subject.toUpperCase()}</span>
            <span className="text-sm font-normal text-muted-foreground">
              Grade {gradeLevel}
            </span>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Main Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="progress">Progress</TabsTrigger>
          <TabsTrigger value="activities">Activities</TabsTrigger>
          <TabsTrigger value="skills">Skills</TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="mt-6">
          <Card className="h-[600px]">
            <CardContent className="p-0 h-full">
              {currentSession && (
                <TutorChat
                  session={currentSession}
                  onSessionUpdate={setCurrentSession}
                  onSessionEnd={handleSessionEnd}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="progress" className="mt-6">
          <div className="grid gap-6">
            {progressData && (
              <ProgressVisualization 
                data={progressData}
                timeframe="week"
                showDetails={true}
              />
            )}
          </div>
        </TabsContent>

        <TabsContent value="activities" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {activities.map((activity) => (
              <LearningActivity
                key={activity.activity_id}
                activity={activity}
                onStart={() => {
                  // Handle activity start
                  console.log('Starting activity:', activity.activity_id);
                }}
                onComplete={(score) => {
                  // Handle activity completion
                  console.log('Activity completed with score:', score);
                }}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="skills" className="mt-6">
          {progressData && (
            <SkillsOverview 
              topics={progressData.topics}
              subject={subject}
              gradeLevel={gradeLevel}
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}