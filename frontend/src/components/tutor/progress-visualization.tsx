'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ProgressChart } from './progress-chart';
import { ProgressVisualizationProps } from './types';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Target, Clock, Award } from 'lucide-react';
import { format } from 'date-fns';

export function ProgressVisualization({ 
  data, 
  timeframe = 'week', 
  showDetails = false 
}: ProgressVisualizationProps) {
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getProgressColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getTrendIcon = (current: number, previous: number = 0.7) => {
    if (current > previous) {
      return <TrendingUp className="w-4 h-4 text-green-500" />;
    }
    return <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Overall Progress Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Overall Progress - {data.subject.toUpperCase()}</span>
            <Badge variant="outline" className="capitalize">
              {timeframe}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            {/* Overall Score */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Overall Score</span>
                <span className={cn("text-2xl font-bold", getScoreColor(data.overall_score))}>
                  {Math.round(data.overall_score * 100)}%
                </span>
              </div>
              <Progress 
                value={data.overall_score * 100} 
                className="h-2"
              />
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                {getTrendIcon(data.overall_score)}
                <span>vs last {timeframe}</span>
              </div>
            </div>

            {/* Topics Mastered */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Topics Mastered</span>
                <span className="text-2xl font-bold text-primary">
                  {data.topics.filter(t => t.skill_level >= 0.8).length}
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                out of {data.topics.length} topics
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Award className="w-3 h-3" />
                <span>Great progress!</span>
              </div>
            </div>

            {/* Last Updated */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Last Practice</span>
                <span className="text-sm font-medium">
                  {format(data.last_updated, 'MMM dd')}
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                {format(data.last_updated, 'HH:mm')}
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="w-3 h-3" />
                <span>Keep it up!</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Progress Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ProgressChart data={data} timeframe={timeframe} />
        </CardContent>
      </Card>

      {/* Topics Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Topics Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.topics.map((topic) => (
              <div key={topic.topic_id} className="space-y-3">
                {/* Topic Header */}
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <h4 className="font-medium">{topic.topic_name}</h4>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {topic.cambridge_code}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        Last practiced: {format(topic.last_practiced, 'MMM dd')}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={cn("text-lg font-bold", getScoreColor(topic.skill_level))}>
                      {Math.round(topic.skill_level * 100)}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Confidence: {Math.round(topic.confidence_score * 100)}%
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <Progress 
                  value={topic.skill_level * 100} 
                  className="h-2"
                />

                {/* Detailed Breakdown */}
                {showDetails && (
                  <div className="grid gap-3 md:grid-cols-3 text-sm">
                    {/* Mastery Indicators */}
                    <div className="space-y-2">
                      <h5 className="font-medium text-xs uppercase tracking-wide text-muted-foreground">
                        Mastery Indicators
                      </h5>
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <span>Understanding</span>
                          <span className={getScoreColor(topic.mastery_indicators.understanding)}>
                            {Math.round(topic.mastery_indicators.understanding * 100)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Application</span>
                          <span className={getScoreColor(topic.mastery_indicators.application)}>
                            {Math.round(topic.mastery_indicators.application * 100)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Retention</span>
                          <span className={getScoreColor(topic.mastery_indicators.retention)}>
                            {Math.round(topic.mastery_indicators.retention * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Improvement Areas */}
                    <div className="space-y-2 md:col-span-2">
                      <h5 className="font-medium text-xs uppercase tracking-wide text-muted-foreground">
                        Areas for Improvement
                      </h5>
                      {topic.improvement_areas.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {topic.improvement_areas.map((area, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              <Target className="w-3 h-3 mr-1" />
                              {area}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                          <Award className="w-4 h-4" />
                          <span>No areas for improvement - Great job!</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}