'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ParentSettingsProps, ParentalControl, StudySchedule } from './parent-types';
import { cn } from '@/lib/utils';
import { 
  Shield,
  Clock,
  Volume2,
  Image,
  Eye,
  Calendar,
  Trash2,
  Plus,
  Save,
  AlertTriangle,
  Lock,
  Globe,
  Database,
  UserX
} from 'lucide-react';
import { format } from 'date-fns';

export function ParentSettings({ 
  childId, 
  currentSettings, 
  onSettingsUpdate 
}: ParentSettingsProps) {
  const [settings, setSettings] = useState<ParentalControl[]>(currentSettings);
  const [schedules, setSchedules] = useState<StudySchedule[]>([]);
  const [hasChanges, setHasChanges] = useState(false);
  const [loading, setLoading] = useState(false);

  // Initialize with default settings if none provided
  useEffect(() => {
    if (currentSettings.length === 0) {
      const defaultSettings: ParentalControl[] = [
        {
          control_id: 'session_time_limit',
          child_id: childId,
          setting_name: 'Session Time Limit',
          setting_value: 45,
          description: 'Maximum time per study session in minutes',
          category: 'time',
          updated_at: new Date()
        },
        {
          control_id: 'content_filtering',
          child_id: childId,
          setting_name: 'Content Filtering',
          setting_value: 'moderate',
          description: 'Level of content filtering for educational materials',
          category: 'content',
          updated_at: new Date()
        },
        {
          control_id: 'voice_interaction',
          child_id: childId,
          setting_name: 'Voice Interaction',
          setting_value: true,
          description: 'Allow voice-based interactions with the AI tutor',
          category: 'safety',
          updated_at: new Date()
        },
        {
          control_id: 'image_sharing',
          child_id: childId,
          setting_name: 'Image Sharing',
          setting_value: false,
          description: 'Allow sharing of images and drawings',
          category: 'privacy',
          updated_at: new Date()
        },
        {
          control_id: 'data_collection',
          child_id: childId,
          setting_name: 'Learning Analytics',
          setting_value: true,
          description: 'Collect learning data for progress tracking and insights',
          category: 'privacy',
          updated_at: new Date()
        },
        {
          control_id: 'third_party_sharing',
          child_id: childId,
          setting_name: 'Third-party Sharing',
          setting_value: false,
          description: 'Share anonymized data with educational research partners',
          category: 'privacy',
          updated_at: new Date()
        }
      ];
      setSettings(defaultSettings);
    } else {
      setSettings(currentSettings);
    }

    // Mock study schedules
    const mockSchedules: StudySchedule[] = [
      {
        schedule_id: 'schedule1',
        child_id: childId,
        day_of_week: 1, // Monday
        start_time: '15:00',
        duration: 30,
        subjects: ['math'],
        is_active: true
      },
      {
        schedule_id: 'schedule2',
        child_id: childId,
        day_of_week: 3, // Wednesday
        start_time: '16:00',
        duration: 45,
        subjects: ['esl', 'science'],
        is_active: true
      }
    ];
    setSchedules(mockSchedules);
  }, [childId, currentSettings]);

  const updateSetting = (controlId: string, newValue: any) => {
    setSettings(prev => prev.map(setting => 
      setting.control_id === controlId 
        ? { ...setting, setting_value: newValue, updated_at: new Date() }
        : setting
    ));
    setHasChanges(true);
  };

  const handleSaveSettings = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      onSettingsUpdate(settings);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const addSchedule = () => {
    const newSchedule: StudySchedule = {
      schedule_id: `schedule_${Date.now()}`,
      child_id: childId,
      day_of_week: 1,
      start_time: '15:00',
      duration: 30,
      subjects: ['math'],
      is_active: true
    };
    setSchedules(prev => [...prev, newSchedule]);
    setHasChanges(true);
  };

  const removeSchedule = (scheduleId: string) => {
    setSchedules(prev => prev.filter(s => s.schedule_id !== scheduleId));
    setHasChanges(true);
  };

  const updateSchedule = (scheduleId: string, updates: Partial<StudySchedule>) => {
    setSchedules(prev => prev.map(schedule =>
      schedule.schedule_id === scheduleId
        ? { ...schedule, ...updates }
        : schedule
    ));
    setHasChanges(true);
  };

  const getSetting = (controlId: string) => {
    return settings.find(s => s.control_id === controlId);
  };

  const getDayName = (dayOfWeek: number) => {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[dayOfWeek];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Parental Controls & Settings</h2>
          <p className="text-sm text-muted-foreground">
            Manage your child's learning environment and privacy settings
          </p>
        </div>
        
        {hasChanges && (
          <Button onClick={handleSaveSettings} disabled={loading}>
            <Save className="w-4 h-4 mr-2" />
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        )}
      </div>

      <Tabs defaultValue="safety" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="safety" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Safety
          </TabsTrigger>
          <TabsTrigger value="time" className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Time & Schedule
          </TabsTrigger>
          <TabsTrigger value="content" className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Content
          </TabsTrigger>
          <TabsTrigger value="privacy" className="flex items-center gap-2">
            <Lock className="w-4 h-4" />
            Privacy
          </TabsTrigger>
        </TabsList>

        {/* Safety Settings */}
        <TabsContent value="safety" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Child Safety Controls
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Voice Interaction */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-base font-medium">Voice Interaction</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow your child to speak with the AI tutor using voice commands
                  </p>
                </div>
                <Switch
                  checked={getSetting('voice_interaction')?.setting_value || false}
                  onCheckedChange={(checked) => updateSetting('voice_interaction', checked)}
                />
              </div>

              <Separator />

              {/* Image Sharing */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-base font-medium">Image Sharing</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow your child to share drawings and images with the tutor
                  </p>
                </div>
                <Switch
                  checked={getSetting('image_sharing')?.setting_value || false}
                  onCheckedChange={(checked) => updateSetting('image_sharing', checked)}
                />
              </div>

              <Separator />

              {/* Content Filtering */}
              <div className="space-y-3">
                <div>
                  <Label className="text-base font-medium">Content Filtering Level</Label>
                  <p className="text-sm text-muted-foreground">
                    Control the level of content filtering for educational materials
                  </p>
                </div>
                <Select
                  value={getSetting('content_filtering')?.setting_value || 'moderate'}
                  onValueChange={(value) => updateSetting('content_filtering', value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="strict">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4 text-red-500" />
                        <div>
                          <p className="font-medium">Strict</p>
                          <p className="text-xs text-muted-foreground">Maximum filtering, very conservative</p>
                        </div>
                      </div>
                    </SelectItem>
                    <SelectItem value="moderate">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4 text-yellow-500" />
                        <div>
                          <p className="font-medium">Moderate</p>
                          <p className="text-xs text-muted-foreground">Balanced filtering, recommended</p>
                        </div>
                      </div>
                    </SelectItem>
                    <SelectItem value="relaxed">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4 text-green-500" />
                        <div>
                          <p className="font-medium">Relaxed</p>
                          <p className="text-xs text-muted-foreground">Minimal filtering, more freedom</p>
                        </div>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Time & Schedule Settings */}
        <TabsContent value="time" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Session Time Limits
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-base font-medium">Maximum Session Duration</Label>
                  <Badge variant="outline">
                    {getSetting('session_time_limit')?.setting_value || 45} minutes
                  </Badge>
                </div>
                <Slider
                  value={[getSetting('session_time_limit')?.setting_value || 45]}
                  onValueChange={([value]) => updateSetting('session_time_limit', value)}
                  max={120}
                  min={15}
                  step={15}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>15 min</span>
                  <span>60 min</span>
                  <span>120 min</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Study Schedule */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  Study Schedule
                </CardTitle>
                <Button onClick={addSchedule} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Schedule
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {schedules.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No study schedules set up yet.</p>
                </div>
              ) : (
                schedules.map((schedule) => (
                  <div key={schedule.schedule_id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">{getDayName(schedule.day_of_week)}</h4>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeSchedule(schedule.schedule_id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                    
                    <div className="grid gap-4 md:grid-cols-3">
                      <div>
                        <Label className="text-sm">Day of Week</Label>
                        <Select
                          value={schedule.day_of_week.toString()}
                          onValueChange={(value) => 
                            updateSchedule(schedule.schedule_id, { day_of_week: parseInt(value) })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {[0, 1, 2, 3, 4, 5, 6].map(day => (
                              <SelectItem key={day} value={day.toString()}>
                                {getDayName(day)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div>
                        <Label className="text-sm">Start Time</Label>
                        <Input
                          type="time"
                          value={schedule.start_time}
                          onChange={(e) => 
                            updateSchedule(schedule.schedule_id, { start_time: e.target.value })
                          }
                        />
                      </div>
                      
                      <div>
                        <Label className="text-sm">Duration (minutes)</Label>
                        <Input
                          type="number"
                          value={schedule.duration}
                          onChange={(e) => 
                            updateSchedule(schedule.schedule_id, { duration: parseInt(e.target.value) })
                          }
                          min={15}
                          max={120}
                          step={15}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label className="text-sm">Subjects</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {['math', 'esl', 'science'].map(subject => (
                          <Badge
                            key={subject}
                            variant={schedule.subjects.includes(subject) ? "default" : "outline"}
                            className="cursor-pointer capitalize"
                            onClick={() => {
                              const newSubjects = schedule.subjects.includes(subject)
                                ? schedule.subjects.filter(s => s !== subject)
                                : [...schedule.subjects, subject];
                              updateSchedule(schedule.schedule_id, { subjects: newSubjects });
                            }}
                          >
                            {subject}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Content Settings */}
        <TabsContent value="content" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5" />
                Content Preferences
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div>
                  <Label className="text-base font-medium">Difficulty Level Preference</Label>
                  <p className="text-sm text-muted-foreground mb-3">
                    Set the preferred difficulty level for learning content
                  </p>
                  <Select defaultValue="medium">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="easy">Easy - Below grade level</SelectItem>
                      <SelectItem value="medium">Medium - At grade level</SelectItem>
                      <SelectItem value="challenging">Challenging - Above grade level</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                <div>
                  <Label className="text-base font-medium">Learning Style Adaptation</Label>
                  <p className="text-sm text-muted-foreground mb-3">
                    How should the AI adapt to your child's learning style?
                  </p>
                  <Select defaultValue="visual">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="visual">Visual - Charts, diagrams, images</SelectItem>
                      <SelectItem value="auditory">Auditory - Spoken explanations, sounds</SelectItem>
                      <SelectItem value="kinesthetic">Kinesthetic - Interactive, hands-on</SelectItem>
                      <SelectItem value="adaptive">Adaptive - Let AI determine best approach</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacy Settings */}
        <TabsContent value="privacy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="w-5 h-5" />
                Data Privacy & Security
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Learning Analytics */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-base font-medium">Learning Analytics</Label>
                  <p className="text-sm text-muted-foreground">
                    Collect learning data to provide progress insights and personalized recommendations
                  </p>
                </div>
                <Switch
                  checked={getSetting('data_collection')?.setting_value || true}
                  onCheckedChange={(checked) => updateSetting('data_collection', checked)}
                />
              </div>

              <Separator />

              {/* Third-party Sharing */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-base font-medium">Educational Research Participation</Label>
                  <p className="text-sm text-muted-foreground">
                    Share anonymized data with educational research partners to improve learning outcomes
                  </p>
                </div>
                <Switch
                  checked={getSetting('third_party_sharing')?.setting_value || false}
                  onCheckedChange={(checked) => updateSetting('third_party_sharing', checked)}
                />
              </div>

              <Separator />

              {/* Data Export */}
              <div className="space-y-3">
                <Label className="text-base font-medium">Data Management</Label>
                <p className="text-sm text-muted-foreground">
                  Manage your child's learning data and exercise your privacy rights
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Database className="w-4 h-4 mr-2" />
                    Export Data
                  </Button>
                  <Button variant="outline" size="sm">
                    <UserX className="w-4 h-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </div>

              {/* Privacy Notice */}
              <div className="bg-muted/50 p-4 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5" />
                  <div className="space-y-2">
                    <h4 className="font-medium">Privacy Protection</h4>
                    <p className="text-sm text-muted-foreground">
                      We comply with COPPA and GDPR regulations to protect your child's privacy. 
                      All data is encrypted and stored securely. You can request data deletion at any time.
                    </p>
                    <Button variant="link" className="p-0 h-auto text-sm">
                      Read our Privacy Policy
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}