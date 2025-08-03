'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ParentInsight } from './parent-types';
import { cn } from '@/lib/utils';
import { 
  Lightbulb,
  CheckCircle,
  AlertTriangle,
  Award,
  Target,
  TrendingUp,
  BookOpen,
  Clock,
  Users,
  Star,
  ArrowRight,
  X
} from 'lucide-react';
import { format } from 'date-fns';

interface ParentInsightsProps {
  childId: string;
}

export function ParentInsights({ childId }: ParentInsightsProps) {
  const [insights, setInsights] = useState<ParentInsight[]>([]);
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);

  // Mock data for development - replace with actual API calls
  useEffect(() => {
    const mockInsights: ParentInsight[] = [
      {
        insight_id: 'insight1',
        child_id: childId,
        type: 'strength',
        title: 'Exceptional Mathematical Reasoning',
        description: 'Your child demonstrates advanced problem-solving skills in mathematics, particularly with word problems and logical reasoning tasks. They consistently score above grade level and show creativity in their solution approaches.',
        action_items: [
          'Consider enrolling in advanced math programs or competitions',
          'Introduce mathematical puzzles and brain teasers at home',
          'Explore real-world applications of math through cooking or building projects',
          'Connect with local math clubs or online communities for gifted students'
        ],
        priority: 'medium',
        created_at: new Date()
      },
      {
        insight_id: 'insight2',
        child_id: childId,
        type: 'improvement',
        title: 'Reading Fluency Needs Support',
        description: 'While your child understands content well, their reading speed is below grade level expectations. This may impact comprehension in timed assessments and could affect confidence in language arts.',
        action_items: [
          'Practice reading aloud together for 15-20 minutes daily',
          'Use guided reading techniques with finger tracking',
          'Try audiobooks paired with text to improve pace recognition',
          'Consider consulting with a reading specialist if progress stalls'
        ],
        priority: 'high',
        created_at: new Date()
      },
      {
        insight_id: 'insight3',
        child_id: childId,
        type: 'suggestion',
        title: 'Optimal Learning Schedule Identified',
        description: 'Data analysis shows your child performs 23% better during afternoon sessions (2-4 PM) compared to morning or evening study times. Their attention span is longest during this window.',
        action_items: [
          'Schedule challenging subjects during 2-4 PM when possible',
          'Use morning time for creative activities and review',
          'Keep evening sessions light with games and fun activities',
          'Ensure adequate breaks every 25-30 minutes during peak hours'
        ],
        priority: 'low',
        created_at: new Date()
      },
      {
        insight_id: 'insight4',
        child_id: childId,
        type: 'achievement',
        title: 'Science Curiosity Milestone Reached',
        description: 'Your child has asked over 50 science questions this month and completed all optional experiments. This shows exceptional scientific curiosity and engagement with STEM subjects.',
        action_items: [
          'Visit science museums or planetariums to fuel curiosity',
          'Set up simple home experiments using household items',
          'Consider science camps or after-school STEM programs',
          'Encourage them to keep a science journal of observations'
        ],
        priority: 'medium',
        created_at: new Date()
      },
      {
        insight_id: 'insight5',
        child_id: childId,
        type: 'improvement',
        title: 'Attention Span Patterns',
        description: 'Your child\'s focus tends to decrease after 20 minutes of continuous study. Breaking sessions into shorter chunks with movement breaks could improve retention and engagement.',
        action_items: [
          'Use the Pomodoro technique with 20-minute focused sessions',
          'Include 5-minute movement breaks between study blocks',
          'Try standing desk options or exercise ball seating',
          'Incorporate kinesthetic learning activities for better engagement'
        ],
        priority: 'medium',
        created_at: new Date()
      },
      {
        insight_id: 'insight6',
        child_id: childId,
        type: 'strength',
        title: 'Visual Learning Excellence',
        description: 'Your child shows 40% better comprehension when information is presented visually through diagrams, charts, and images. This is a significant learning strength to leverage.',
        action_items: [
          'Use mind maps and visual organizers for complex topics',
          'Incorporate educational videos and interactive simulations',
          'Create colorful study materials with charts and diagrams',
          'Encourage drawing and sketching to explain concepts'
        ],
        priority: 'low',
        created_at: new Date()
      }
    ];

    setInsights(mockInsights);
    setLoading(false);
  }, [childId]);

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'strength':
        return <Star className="w-5 h-5 text-green-500" />;
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

  const getInsightBorderColor = (type: string) => {
    switch (type) {
      case 'strength':
        return 'border-green-200 dark:border-green-800';
      case 'improvement':
        return 'border-yellow-200 dark:border-yellow-800';
      case 'suggestion':
        return 'border-blue-200 dark:border-blue-800';
      case 'achievement':
        return 'border-purple-200 dark:border-purple-800';
      default:
        return 'border-gray-200 dark:border-gray-800';
    }
  };

  const filteredInsights = activeTab === 'all' 
    ? insights 
    : insights.filter(insight => insight.type === activeTab);

  const handleDismissInsight = (insightId: string) => {
    setInsights(prev => prev.filter(insight => insight.insight_id !== insightId));
  };

  const handleMarkAsRead = (insightId: string) => {
    // In a real app, this would update the backend
    console.log('Marking insight as read:', insightId);
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
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">Learning Insights & Recommendations</h2>
        <p className="text-sm text-muted-foreground">
          AI-powered insights to help you support your child's learning journey
        </p>
      </div>

      {/* Insights Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Strengths</p>
                <p className="text-2xl font-bold text-green-600">
                  {insights.filter(i => i.type === 'strength').length}
                </p>
              </div>
              <Star className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Improvements</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {insights.filter(i => i.type === 'improvement').length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Suggestions</p>
                <p className="text-2xl font-bold text-blue-600">
                  {insights.filter(i => i.type === 'suggestion').length}
                </p>
              </div>
              <Lightbulb className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Achievements</p>
                <p className="text-2xl font-bold text-purple-600">
                  {insights.filter(i => i.type === 'achievement').length}
                </p>
              </div>
              <Award className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="strength" className="flex items-center gap-2">
            <Star className="w-4 h-4" />
            Strengths
          </TabsTrigger>
          <TabsTrigger value="improvement" className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Improvements
          </TabsTrigger>
          <TabsTrigger value="suggestion" className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            Suggestions
          </TabsTrigger>
          <TabsTrigger value="achievement" className="flex items-center gap-2">
            <Award className="w-4 h-4" />
            Achievements
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          {filteredInsights.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Target className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  No insights available for this category yet.
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredInsights.map((insight) => (
              <Card key={insight.insight_id} className={cn("relative", getInsightBorderColor(insight.type))}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {getInsightIcon(insight.type)}
                      <div>
                        <CardTitle className="text-lg">{insight.title}</CardTitle>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant={getInsightBadgeVariant(insight.priority)} className="capitalize">
                            {insight.priority} Priority
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {format(insight.created_at, 'MMM dd, yyyy')}
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDismissInsight(insight.insight_id)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground leading-relaxed">
                    {insight.description}
                  </p>
                  
                  {insight.action_items.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-medium flex items-center gap-2">
                        <ArrowRight className="w-4 h-4 text-primary" />
                        Recommended Actions
                      </h4>
                      <div className="space-y-2">
                        {insight.action_items.map((action, index) => (
                          <div key={index} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
                            <CheckCircle className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                            <span className="text-sm">{action}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleMarkAsRead(insight.insight_id)}
                    >
                      Mark as Read
                    </Button>
                    <Button variant="ghost" size="sm">
                      Learn More
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Quick Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            Quick Tips for Parents
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <h4 className="font-medium flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-500" />
                Study Schedule
              </h4>
              <p className="text-sm text-muted-foreground">
                Consistency is key. Even 15-20 minutes daily is more effective than longer, irregular sessions.
              </p>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-green-500" />
                Reading Together
              </h4>
              <p className="text-sm text-muted-foreground">
                Reading aloud together improves comprehension and creates positive associations with learning.
              </p>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-500" />
                Celebrate Progress
              </h4>
              <p className="text-sm text-muted-foreground">
                Acknowledge effort and improvement, not just perfect scores. This builds growth mindset.
              </p>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium flex items-center gap-2">
                <Target className="w-4 h-4 text-yellow-500" />
                Ask Questions
              </h4>
              <p className="text-sm text-muted-foreground">
                Encourage curiosity by asking "What do you think?" and "How did you figure that out?"
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}