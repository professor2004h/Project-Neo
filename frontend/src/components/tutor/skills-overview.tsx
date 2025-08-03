'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TopicProgress } from './types';
import { cn } from '@/lib/utils';
import { 
  BookOpen, 
  Target, 
  TrendingUp, 
  Clock, 
  Award, 
  AlertCircle,
  CheckCircle2,
  Play
} from 'lucide-react';
import { format } from 'date-fns';

interface SkillsOverviewProps {
  topics: TopicProgress[];
  subject: 'math' | 'esl' | 'science';
  gradeLevel: number;
}

export function SkillsOverview({ topics, subject, gradeLevel }: SkillsOverviewProps) {
  const getSkillLevelStatus = (skillLevel: number) => {
    if (skillLevel >= 0.8) return { status: 'mastered', color: 'text-green-600 dark:text-green-400', icon: CheckCircle2 };
    if (skillLevel >= 0.6) return { status: 'progressing', color: 'text-yellow-600 dark:text-yellow-400', icon: TrendingUp };
    return { status: 'needs-work', color: 'text-red-600 dark:text-red-400', icon: AlertCircle };
  };

  const getSubjectIcon = () => {
    switch (subject) {
      case 'math':
        return '🔢';
      case 'esl':
        return '🗣️';
      case 'science':
        return '🔬';
      default:
        return '📚';
    }
  };

  const sortedTopics = [...topics].sort((a, b) => {
    // Sort by skill level (lowest first to prioritize areas needing work)
    return a.skill_level - b.skill_level;
  });

  const masteredTopics = topics.filter(t => t.skill_level >= 0.8);
  const progressingTopics = topics.filter(t => t.skill_level >= 0.6 && t.skill_level < 0.8);
  const needsWorkTopics = topics.filter(t => t.skill_level < 0.6);

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="text-2xl">{getSubjectIcon()}</div>
              <div>
                <div className="text-2xl font-bold">{topics.length}</div>
                <div className="text-xs text-muted-foreground">Total Topics</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-8 h-8 text-green-500" />
              <div>
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {masteredTopics.length}
                </div>
                <div className="text-xs text-muted-foreground">Mastered</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-yellow-500" />
              <div>
                <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                  {progressingTopics.length}
                </div>
                <div className="text-xs text-muted-foreground">In Progress</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-red-500" />
              <div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {needsWorkTopics.length}
                </div>
                <div className="text-xs text-muted-foreground">Needs Work</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Priority Topics (Needs Work) */}
      {needsWorkTopics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-red-500" />
              Priority Topics - Needs Attention
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {needsWorkTopics.map((topic) => {
                const { status, color, icon: StatusIcon } = getSkillLevelStatus(topic.skill_level);
                
                return (
                  <div key={topic.topic_id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <h4 className="font-medium">{topic.topic_name}</h4>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">
                            {topic.cambridge_code}
                          </Badge>
                          <Badge variant="outline" className={cn("text-xs", color)}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {Math.round(topic.skill_level * 100)}%
                          </Badge>
                        </div>
                      </div>
                      <Button size="sm" className="shrink-0">
                        <Play className="w-4 h-4 mr-1" />
                        Practice
                      </Button>
                    </div>

                    <Progress value={topic.skill_level * 100} className="h-2" />

                    <div className="grid gap-2 md:grid-cols-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Last practiced: </span>
                        <span>{format(topic.last_practiced, 'MMM dd, yyyy')}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Confidence: </span>
                        <span className={color}>
                          {Math.round(topic.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>

                    {topic.improvement_areas.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-xs font-medium text-muted-foreground">
                          Focus Areas:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {topic.improvement_areas.map((area, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {area}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Topics Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            All Topics - Grade {gradeLevel} {subject.toUpperCase()}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sortedTopics.map((topic) => {
              const { status, color, icon: StatusIcon } = getSkillLevelStatus(topic.skill_level);
              
              return (
                <div key={topic.topic_id} className="flex items-center gap-4 p-3 rounded-lg border">
                  {/* Status Icon */}
                  <StatusIcon className={cn("w-5 h-5", color)} />

                  {/* Topic Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium truncate">{topic.topic_name}</h4>
                      <Badge variant="secondary" className="text-xs shrink-0">
                        {topic.cambridge_code}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Skill: {Math.round(topic.skill_level * 100)}%</span>
                      <span>Confidence: {Math.round(topic.confidence_score * 100)}%</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {format(topic.last_practiced, 'MMM dd')}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-24 space-y-1">
                    <Progress value={topic.skill_level * 100} className="h-2" />
                    <div className="text-xs text-center text-muted-foreground">
                      {Math.round(topic.skill_level * 100)}%
                    </div>
                  </div>

                  {/* Action Button */}
                  <Button 
                    size="sm" 
                    variant={topic.skill_level >= 0.8 ? "outline" : "default"}
                    className="shrink-0"
                  >
                    {topic.skill_level >= 0.8 ? (
                      <>
                        <Award className="w-4 h-4 mr-1" />
                        Review
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-1" />
                        Practice
                      </>
                    )}
                  </Button>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Mastery Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Mastery Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {sortedTopics.slice(0, 6).map((topic) => (
              <div key={topic.topic_id} className="space-y-3 p-3 border rounded-lg">
                <div className="space-y-1">
                  <h5 className="font-medium text-sm">{topic.topic_name}</h5>
                  <Badge variant="secondary" className="text-xs">
                    {topic.cambridge_code}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Understanding</span>
                    <span>{Math.round(topic.mastery_indicators.understanding * 100)}%</span>
                  </div>
                  <Progress value={topic.mastery_indicators.understanding * 100} className="h-1" />

                  <div className="flex justify-between text-xs">
                    <span>Application</span>
                    <span>{Math.round(topic.mastery_indicators.application * 100)}%</span>
                  </div>
                  <Progress value={topic.mastery_indicators.application * 100} className="h-1" />

                  <div className="flex justify-between text-xs">
                    <span>Retention</span>
                    <span>{Math.round(topic.mastery_indicators.retention * 100)}%</span>
                  </div>
                  <Progress value={topic.mastery_indicators.retention * 100} className="h-1" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}