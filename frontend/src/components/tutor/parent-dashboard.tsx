'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ParentDashboardProps, ParentDashboardData, ChildProfile } from './parent-types';
import { ParentReportViewer } from './parent-report-viewer';
import { ParentSettings } from './parent-settings';
import { ParentInsights } from './parent-insights';
import { cn } from '@/lib/utils';
import { 
  Users, 
  TrendingUp, 
  Clock, 
  Award, 
  Settings, 
  Calendar,
  BookOpen,
  Target,
  AlertCircle
} from 'lucide-react';
import { format, startOfWeek, endOfWeek } from 'date-fns';

export function ParentDashboard({ 
  parentId, 
  onChildSelect, 
  onSettingsChange 
}: ParentDashboardProps) {
  const [dashboardData, setDashboardData] = useState<ParentDashboardData | null>(null);
  const [selectedChild, setSelectedChild] = useState<ChildProfile | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  // Mock data for development - replace with actual API calls
  useEffect(() => {
    const mockData: ParentDashboardData = {
      children: [
        {
          child_id: 'child1',
          parent_id: parentId,
          name: 'Emma',
          age: 8,
          grade_level: 3,
          learning_preferences: {
            learning_style: 'visual',
            preferred_subjects: ['math', 'science'],
            difficulty_preference: 'medium'
          },
          curriculum_progress: {
            math: 0.75,
            esl: 0.68,
            science: 0.82
          },
          safety_settings: {
            session_time_limit: 45,
            content_filtering: 'moderate',
            voice_interaction_enabled: true,
            image_sharing_enabled: false
          },
          created_at: new Date('2024-01-15')
        },
        {
          child_id: 'child2',
          parent_id: parentId,
          name: 'James',
          age: 10,
          grade_level: 5,
          learning_preferences: {
            learning_style: 'kinesthetic',
            preferred_subjects: ['science', 'esl'],
            difficulty_preference: 'challenging'
          },
          curriculum_progress: {
            math: 0.65,
            esl: 0.78,
            science: 0.71
          },
          safety_settings: {
            session_time_limit: 60,
            content_filtering: 'moderate',
            voice_interaction_enabled: true,
            image_sharing_enabled: true
          },
          created_at: new Date('2024-02-20')
        }
      ],
      weekly_reports: [],
      recent_insights: [],
      upcoming_schedules: [],
      family_achievements: []
    };

    setDashboardData(mockData);
    setSelectedChild(mockData.children[0]);
    setLoading(false);
  }, [parentId]);

  const handleChildSelect = (childId: string) => {
    const child = dashboardData?.children.find(c => c.child_id === childId);
    if (child) {
      setSelectedChild(child);
      onChildSelect?.(child);
    }
  };

  const getProgressColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getProgressBadgeVariant = (score: number) => {
    if (score >= 0.8) return 'default';
    if (score >= 0.6) return 'secondary';
    return 'destructive';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" role="status" aria-label="Loading"></div>
      </div>
    );
  }

  if (!dashboardData || !selectedChild) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No children found. Please add a child profile first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Child Selector */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold">Parent Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your child's learning progress and manage settings
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <Select value={selectedChild.child_id} onValueChange={handleChildSelect}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {dashboardData.children.map((child) => (
                <SelectItem key={child.child_id} value={child.child_id}>
                  <div className="flex items-center gap-2">
                    <Avatar className="w-6 h-6">
                      <AvatarFallback className="text-xs">
                        {child.name.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <span>{child.name}</span>
                    <Badge variant="outline" className="text-xs">
                      Grade {child.grade_level}
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Child Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Avatar className="w-12 h-12">
                <AvatarFallback className="text-lg font-bold">
                  {selectedChild.name.charAt(0)}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold">{selectedChild.name}</h3>
                <p className="text-sm text-muted-foreground">
                  Age {selectedChild.age} • Grade {selectedChild.grade_level}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Mathematics</p>
                <p className={cn("text-2xl font-bold", getProgressColor(selectedChild.curriculum_progress.math))}>
                  {Math.round(selectedChild.curriculum_progress.math * 100)}%
                </p>
              </div>
              <BookOpen className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">English (ESL)</p>
                <p className={cn("text-2xl font-bold", getProgressColor(selectedChild.curriculum_progress.esl))}>
                  {Math.round(selectedChild.curriculum_progress.esl * 100)}%
                </p>
              </div>
              <Users className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Science</p>
                <p className={cn("text-2xl font-bold", getProgressColor(selectedChild.curriculum_progress.science))}>
                  {Math.round(selectedChild.curriculum_progress.science * 100)}%
                </p>
              </div>
              <Target className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Reports
          </TabsTrigger>
          <TabsTrigger value="insights" className="flex items-center gap-2">
            <Award className="w-4 h-4" />
            Insights
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Learning Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Learning Profile</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-sm font-medium mb-2">Learning Style</p>
                  <Badge variant="outline" className="capitalize">
                    {selectedChild.learning_preferences.learning_style}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">Preferred Subjects</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedChild.learning_preferences.preferred_subjects.map((subject) => (
                      <Badge key={subject} variant="secondary" className="text-xs capitalize">
                        {subject}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">Difficulty Level</p>
                  <Badge 
                    variant={getProgressBadgeVariant(
                      selectedChild.learning_preferences.difficulty_preference === 'challenging' ? 0.9 :
                      selectedChild.learning_preferences.difficulty_preference === 'medium' ? 0.7 : 0.5
                    )}
                    className="capitalize"
                  >
                    {selectedChild.learning_preferences.difficulty_preference}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Safety Settings Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Safety & Controls</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Session Time Limit</span>
                    <Badge variant="outline">
                      {selectedChild.safety_settings.session_time_limit} minutes
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Content Filtering</span>
                    <Badge variant="outline" className="capitalize">
                      {selectedChild.safety_settings.content_filtering}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Voice Interaction</span>
                    <Badge variant={selectedChild.safety_settings.voice_interaction_enabled ? "default" : "secondary"}>
                      {selectedChild.safety_settings.voice_interaction_enabled ? "Enabled" : "Disabled"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Image Sharing</span>
                    <Badge variant={selectedChild.safety_settings.image_sharing_enabled ? "default" : "secondary"}>
                      {selectedChild.safety_settings.image_sharing_enabled ? "Enabled" : "Disabled"}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <ParentReportViewer childId={selectedChild.child_id} />
        </TabsContent>

        <TabsContent value="insights">
          <ParentInsights childId={selectedChild.child_id} />
        </TabsContent>

        <TabsContent value="settings">
          <ParentSettings 
            childId={selectedChild.child_id}
            currentSettings={[]}
            onSettingsUpdate={(settings) => {
              onSettingsChange?.(settings);
            }}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}