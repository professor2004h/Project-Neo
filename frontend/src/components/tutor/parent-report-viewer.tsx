'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { WeeklyReport, ParentInsight, Achievement } from './parent-types';
import { cn } from '@/lib/utils';
import { 
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  Award,
  BookOpen,
  Target,
  Lightbulb,
  CheckCircle,
  AlertTriangle,
  Download,
  Share
} from 'lucide-react';
import { format, startOfWeek, endOfWeek, subWeeks } from 'date-fns';

interface ParentReportViewerProps {
  childId: string;
}

export function ParentReportViewer({ childId }: ParentReportViewerProps) {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);

  // Mock data for development - replace with actual API calls
  useEffect(() => {
    const mockReports: WeeklyReport[] = [
      {
        report_id: 'report1',
        child_id: childId,
        week_start: startOfWeek(new Date()),
        week_end: endOfWeek(new Date()),
        total_study_time: 180, // 3 hours
        sessions_completed: 8,
        topics_practiced: ['Fractions', 'Multiplication', 'Reading Comprehension', 'Science Experiments'],
        achievements: [
          {
            achievement_id: 'ach1',
            title: 'Math Master',
            description: 'Completed 5 math exercises in a row',
            icon: '🏆',
            earned_at: new Date(),
            category: 'mastery'
          },
          {
            achievement_id: 'ach2',
            title: 'Consistent Learner',
            description: 'Studied for 7 days straight',
            icon: '📚',
            earned_at: new Date(),
            category: 'consistency'
          }
        ],
        progress_summary: {
          overall_improvement: 0.12,
          subject_breakdown: {
            math: { score: 0.78, change: 0.08 },
            esl: { score: 0.71, change: 0.05 },
            science: { score: 0.85, change: 0.15 }
          }
        },
        parent_insights: [
          {
            insight_id: 'insight1',
            child_id: childId,
            type: 'strength',
            title: 'Excellent Progress in Science',
            description: 'Your child shows exceptional understanding of scientific concepts and experiments.',
            action_items: [
              'Consider introducing more advanced science topics',
              'Encourage hands-on experiments at home',
              'Visit a science museum together'
            ],
            priority: 'medium',
            created_at: new Date()
          },
          {
            insight_id: 'insight2',
            child_id: childId,
            type: 'improvement',
            title: 'Reading Comprehension Needs Attention',
            description: 'Your child may benefit from additional reading practice to improve comprehension skills.',
            action_items: [
              'Read together for 15 minutes daily',
              'Ask questions about the story',
              'Practice summarizing what was read'
            ],
            priority: 'high',
            created_at: new Date()
          },
          {
            insight_id: 'insight3',
            child_id: childId,
            type: 'suggestion',
            title: 'Optimal Study Time',
            description: 'Your child performs best during afternoon sessions between 2-4 PM.',
            action_items: [
              'Schedule main study sessions in the afternoon',
              'Keep morning sessions light and fun',
              'Ensure adequate breaks between sessions'
            ],
            priority: 'low',
            created_at: new Date()
          }
        ],
        recommendations: [
          'Continue with current math curriculum pace',
          'Introduce more interactive reading activities',
          'Consider science enrichment programs',
          'Maintain consistent daily study routine'
        ]
      },
      {
        report_id: 'report2',
        child_id: childId,
        week_start: startOfWeek(subWeeks(new Date(), 1)),
        week_end: endOfWeek(subWeeks(new Date(), 1)),
        total_study_time: 165,
        sessions_completed: 7,
        topics_practiced: ['Addition', 'Subtraction', 'Vocabulary Building', 'Plant Life Cycle'],
        achievements: [
          {
            achievement_id: 'ach3',
            title: 'Quick Learner',
            description: 'Mastered addition facts under 2 minutes',
            icon: '⚡',
            earned_at: subWeeks(new Date(), 1),
            category: 'progress'
          }
        ],
        progress_summary: {
          overall_improvement: 0.08,
          subject_breakdown: {
            math: { score: 0.70, change: 0.05 },
            esl: { score: 0.66, change: 0.03 },
            science: { score: 0.70, change: 0.12 }
          }
        },
        parent_insights: [],
        recommendations: [
          'Focus on multiplication tables next week',
          'Increase reading time to improve vocabulary',
          'Great progress in science - keep it up!'
        ]
      }
    ];

    setReports(mockReports);
    setSelectedReport(mockReports[0]);
    setLoading(false);
  }, [childId]);

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'strength':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'improvement':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'suggestion':
        return <Lightbulb className="w-5 h-5 text-blue-500" />;
      case 'achievement':
        return <Award className="w-5 h-5 text-purple-500" />;
      default:
        return <Target className="w-5 h-5 text-gray-500" />;
    }
  };

  const getInsightBadgeVariant = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      case 'low':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) {
      return <TrendingUp className="w-4 h-4 text-green-500" />;
    } else if (change < 0) {
      return <TrendingDown className="w-4 h-4 text-red-500" />;
    }
    return null;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" role="status" aria-label="Loading"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Report Selector */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Weekly Progress Reports</h2>
          <p className="text-sm text-muted-foreground">
            Detailed insights into your child's learning journey
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select 
            value={selectedReport?.report_id || ''} 
            onValueChange={(reportId) => {
              const report = reports.find(r => r.report_id === reportId);
              if (report) setSelectedReport(report);
            }}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select a report" />
            </SelectTrigger>
            <SelectContent>
              {reports.map((report) => (
                <SelectItem key={report.report_id} value={report.report_id}>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>
                      {format(report.week_start, 'MMM dd')} - {format(report.week_end, 'MMM dd')}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          
          <Button variant="outline" size="sm">
            <Share className="w-4 h-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      {selectedReport && (
        <>
          {/* Report Summary */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Study Time</p>
                    <p className="text-2xl font-bold">
                      {Math.floor(selectedReport.total_study_time / 60)}h {selectedReport.total_study_time % 60}m
                    </p>
                  </div>
                  <Clock className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Sessions</p>
                    <p className="text-2xl font-bold">{selectedReport.sessions_completed}</p>
                  </div>
                  <BookOpen className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Topics</p>
                    <p className="text-2xl font-bold">{selectedReport.topics_practiced.length}</p>
                  </div>
                  <Target className="w-8 h-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Achievements</p>
                    <p className="text-2xl font-bold">{selectedReport.achievements.length}</p>
                  </div>
                  <Award className="w-8 h-8 text-yellow-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Progress Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Progress Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Overall Improvement */}
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Overall Improvement</h4>
                    <p className="text-sm text-muted-foreground">
                      Compared to previous week
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getChangeIcon(selectedReport.progress_summary.overall_improvement)}
                    <span className={cn(
                      "text-lg font-bold",
                      selectedReport.progress_summary.overall_improvement > 0 
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                    )}>
                      {selectedReport.progress_summary.overall_improvement > 0 ? '+' : ''}
                      {Math.round(selectedReport.progress_summary.overall_improvement * 100)}%
                    </span>
                  </div>
                </div>

                {/* Subject Breakdown */}
                <div className="space-y-4">
                  <h4 className="font-medium">Subject Performance</h4>
                  
                  {Object.entries(selectedReport.progress_summary.subject_breakdown).map(([subject, data]) => (
                    <div key={subject} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">{subject}</span>
                        <div className="flex items-center gap-2">
                          {getChangeIcon(data.change)}
                          <span className={cn("text-sm", getScoreColor(data.score))}>
                            {Math.round(data.score * 100)}%
                          </span>
                          <span className="text-xs text-muted-foreground">
                            ({data.change > 0 ? '+' : ''}{Math.round(data.change * 100)}%)
                          </span>
                        </div>
                      </div>
                      <Progress value={data.score * 100} className="h-2" />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Parent Insights */}
          {selectedReport.parent_insights.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Parent Insights & Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {selectedReport.parent_insights.map((insight) => (
                    <div key={insight.insight_id} className="border rounded-lg p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          {getInsightIcon(insight.type)}
                          <div>
                            <h4 className="font-medium">{insight.title}</h4>
                            <p className="text-sm text-muted-foreground">
                              {insight.description}
                            </p>
                          </div>
                        </div>
                        <Badge variant={getInsightBadgeVariant(insight.priority)} className="capitalize">
                          {insight.priority}
                        </Badge>
                      </div>
                      
                      {insight.action_items.length > 0 && (
                        <div className="ml-8">
                          <p className="text-sm font-medium mb-2">Suggested Actions:</p>
                          <ul className="text-sm text-muted-foreground space-y-1">
                            {insight.action_items.map((action, index) => (
                              <li key={index} className="flex items-start gap-2">
                                <span className="text-primary">•</span>
                                <span>{action}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Achievements */}
          {selectedReport.achievements.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5" />
                  Achievements This Week
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  {selectedReport.achievements.map((achievement) => (
                    <div key={achievement.achievement_id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <div className="text-2xl">{achievement.icon}</div>
                      <div>
                        <h4 className="font-medium">{achievement.title}</h4>
                        <p className="text-sm text-muted-foreground">
                          {achievement.description}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {format(achievement.earned_at, 'MMM dd, HH:mm')}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Topics Practiced */}
          <Card>
            <CardHeader>
              <CardTitle>Topics Practiced This Week</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {selectedReport.topics_practiced.map((topic, index) => (
                  <Badge key={index} variant="outline">
                    {topic}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* General Recommendations */}
          {selectedReport.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations for Next Week</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {selectedReport.recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}