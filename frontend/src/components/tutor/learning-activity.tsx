'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { LearningActivityData } from './types';
import { cn } from '@/lib/utils';
import { 
  Play, 
  CheckCircle2, 
  Clock, 
  Star, 
  Target, 
  BookOpen,
  Gamepad2,
  FileText,
  HelpCircle
} from 'lucide-react';

interface LearningActivityProps {
  activity: LearningActivityData;
  onStart: () => void;
  onComplete: (score: number) => void;
}

export function LearningActivity({ activity, onStart, onComplete }: LearningActivityProps) {
  const [isStarting, setIsStarting] = useState(false);

  const getActivityIcon = () => {
    switch (activity.activity_type) {
      case 'practice':
        return <Target className="w-5 h-5" />;
      case 'assessment':
        return <FileText className="w-5 h-5" />;
      case 'explanation':
        return <HelpCircle className="w-5 h-5" />;
      case 'game':
        return <Gamepad2 className="w-5 h-5" />;
      default:
        return <BookOpen className="w-5 h-5" />;
    }
  };

  const getActivityColor = () => {
    switch (activity.activity_type) {
      case 'practice':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/20';
      case 'assessment':
        return 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/20';
      case 'explanation':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/20';
      case 'game':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-950/20';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-950/20';
    }
  };

  const getDifficultyStars = () => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={cn(
          "w-3 h-3",
          i < activity.difficulty_level 
            ? "fill-yellow-400 text-yellow-400" 
            : "text-gray-300 dark:text-gray-600"
        )}
      />
    ));
  };

  const getStatusBadge = () => {
    switch (activity.completion_status) {
      case 'completed':
        return (
          <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        );
      case 'in_progress':
        return (
          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
            <Clock className="w-3 h-3 mr-1" />
            In Progress
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            <Play className="w-3 h-3 mr-1" />
            Not Started
          </Badge>
        );
    }
  };

  const handleStart = async () => {
    setIsStarting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate loading
      onStart();
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <Card className={cn(
      "transition-all duration-200 hover:shadow-md",
      activity.completion_status === 'completed' && "border-green-200 dark:border-green-800"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", getActivityColor())}>
              {getActivityIcon()}
            </div>
            <div className="space-y-1">
              <CardTitle className="text-base leading-tight">
                {activity.title}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs capitalize">
                  {activity.activity_type}
                </Badge>
                {getStatusBadge()}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Description */}
        <p className="text-sm text-muted-foreground leading-relaxed">
          {activity.description}
        </p>

        {/* Activity Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-1">
            <span className="text-muted-foreground">Difficulty:</span>
            <div className="flex items-center gap-1">
              {getDifficultyStars()}
            </div>
          </div>
          <div className="space-y-1">
            <span className="text-muted-foreground">Duration:</span>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{activity.estimated_duration} min</span>
            </div>
          </div>
        </div>

        {/* Score Display (if completed) */}
        {activity.completion_status === 'completed' && activity.score !== undefined && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Your Score:</span>
              <span className={cn(
                "font-medium",
                activity.score >= 80 ? "text-green-600 dark:text-green-400" :
                activity.score >= 60 ? "text-yellow-600 dark:text-yellow-400" :
                "text-red-600 dark:text-red-400"
              )}>
                {activity.score}%
              </span>
            </div>
            <Progress value={activity.score} className="h-2" />
          </div>
        )}

        {/* Action Button */}
        <div className="pt-2">
          {activity.completion_status === 'completed' ? (
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleStart}
                disabled={isStarting}
                className="flex-1"
              >
                <Play className="w-4 h-4 mr-1" />
                {isStarting ? 'Loading...' : 'Practice Again'}
              </Button>
              {activity.score !== undefined && activity.score < 80 && (
                <Button 
                  size="sm" 
                  onClick={handleStart}
                  disabled={isStarting}
                  className="flex-1"
                >
                  <Target className="w-4 h-4 mr-1" />
                  Improve Score
                </Button>
              )}
            </div>
          ) : (
            <Button 
              onClick={handleStart}
              disabled={isStarting}
              className="w-full"
              size="sm"
            >
              <Play className="w-4 h-4 mr-1" />
              {isStarting ? 'Starting...' : 
               activity.completion_status === 'in_progress' ? 'Continue' : 'Start Activity'}
            </Button>
          )}
        </div>

        {/* Achievement Badge (for high scores) */}
        {activity.completion_status === 'completed' && 
         activity.score !== undefined && 
         activity.score >= 90 && (
          <div className="flex items-center justify-center gap-2 p-2 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-300">
              Excellent Work!
            </span>
            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}