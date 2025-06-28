'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Mic,
  MicOff,
  Monitor,
  User,
  Download,
  Share2,
  Search,
  MessageSquare,
  Loader2,
  Pause,
  Play,
  Square,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import {
  getMeeting,
  updateMeeting,
  TranscriptionWebSocket,
  type Meeting,
} from '@/lib/api-meetings';
import { createClient } from '@/lib/supabase/client';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

// Speech recognition types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function MeetingPage() {
  const params = useParams();
  const router = useRouter();
  const meetingId = params.meetingId as string;
  
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [transcript, setTranscript] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<{ index: number; text: string }[]>([]);
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);
  
  // Recording states
  const [recordingMode, setRecordingMode] = useState<'local' | 'online' | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [wsConnection, setWsConnection] = useState<TranscriptionWebSocket | null>(null);
  const [botStatus, setBotStatus] = useState<string>('');
  
  const transcriptRef = useRef<HTMLDivElement>(null);
  const searchHighlightRefs = useRef<(HTMLSpanElement | null)[]>([]);

  // Load meeting data
  useEffect(() => {
    loadMeeting();
  }, [meetingId]);

  const loadMeeting = async () => {
    try {
      setIsLoading(true);
      const data = await getMeeting(meetingId);
      setMeeting(data);
      setTranscript(data.transcript || '');
      
      // If meeting is active and online, check bot status
      if (data.status === 'active' && data.recording_mode === 'online' && data.metadata?.bot_id) {
        checkBotStatus(data.metadata.bot_id);
      }
    } catch (error) {
      console.error('Error loading meeting:', error);
      toast.error('Failed to load meeting');
      router.push('/meetings');
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize WebSocket connection
  useEffect(() => {
    if (!meeting || meeting.status !== 'active') return;

    const initWebSocket = async () => {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session?.access_token) return;

      const ws = new TranscriptionWebSocket(
        meetingId,
        session.access_token,
        (text) => {
          setTranscript((prev) => prev + ' ' + text);
        },
        (status) => {
          if (status === 'completed') {
            setMeeting((prev) => prev ? { ...prev, status: 'completed' } : null);
            setIsRecording(false);
          }
        },
        (error) => {
          console.error('WebSocket error:', error);
          toast.error('Connection error');
        }
      );

      ws.connect();
      setWsConnection(ws);
    };

    initWebSocket();

    return () => {
      wsConnection?.disconnect();
    };
  }, [meeting, meetingId]);

  // Initialize speech recognition for local recording
  const initSpeechRecognition = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast.error('Speech recognition is not supported in your browser');
      return null;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        // Send final transcript through WebSocket
        wsConnection?.sendTranscript(finalTranscript);
      }

      // Update local display with both final and interim
      const displayText = finalTranscript + interimTranscript;
      if (displayText) {
        setTranscript((prev) => prev + displayText);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      if (event.error === 'no-speech') {
        // Restart recognition on no-speech error
        recognition.stop();
        setTimeout(() => recognition.start(), 100);
      } else {
        toast.error(`Speech recognition error: ${event.error}`);
        setIsRecording(false);
      }
    };

    recognition.onend = () => {
      if (isRecording) {
        // Restart if still recording
        recognition.start();
      }
    };

    return recognition;
  }, [wsConnection, isRecording]);

  // Start recording
  const startRecording = async (mode: 'local' | 'online') => {
    setRecordingMode(mode);

    if (mode === 'local') {
      const rec = initSpeechRecognition();
      if (!rec) return;

      setRecognition(rec);
      try {
        await rec.start();
        setIsRecording(true);
        wsConnection?.updateStatus('active');
        toast.success('Recording started');
      } catch (error) {
        console.error('Error starting recording:', error);
        toast.error('Failed to start recording');
      }
    } else {
      // For online mode, show meeting URL input dialog
      const meetingUrl = prompt('Enter the meeting URL:');
      if (!meetingUrl) return;

      try {
        // Start meeting bot
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/meeting-bot/start`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            meeting_url: meetingUrl,
            sandbox_id: meetingId, // Using meeting ID as sandbox ID
          }),
        });

        const data = await response.json();
        if (data.success) {
          setBotStatus(data.status);
          setIsRecording(true);
          
          // Update meeting metadata with bot info
          await updateMeeting(meetingId, {
            metadata: { bot_id: data.bot_id, meeting_url: meetingUrl },
            status: 'active',
          });

          toast.success('Meeting bot is joining the meeting...');
          
          // Start polling for bot status
          checkBotStatus(data.bot_id);
        } else {
          throw new Error(data.error || 'Failed to start meeting bot');
        }
      } catch (error) {
        console.error('Error starting online recording:', error);
        toast.error('Failed to start meeting bot');
      }
    }
  };

  // Stop recording
  const stopRecording = async () => {
    if (recordingMode === 'local') {
      recognition?.stop();
      setIsRecording(false);
      wsConnection?.updateStatus('completed');
      
      // Save transcript
      await updateMeeting(meetingId, {
        transcript,
        status: 'completed',
      });
      
      toast.success('Recording stopped and saved');
    } else if (recordingMode === 'online' && meeting?.metadata?.bot_id) {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/meeting-bot/${meeting.metadata.bot_id}/stop`, {
          method: 'POST',
        });

        const data = await response.json();
        if (data.content) {
          // Update transcript with bot's transcript
          const fullTranscript = transcript + '\n\n' + data.content;
          setTranscript(fullTranscript);
          
          await updateMeeting(meetingId, {
            transcript: fullTranscript,
            status: 'completed',
          });
        }
        
        setIsRecording(false);
        setBotStatus('completed');
        toast.success('Meeting recording completed');
      } catch (error) {
        console.error('Error stopping bot:', error);
        toast.error('Failed to stop meeting bot');
      }
    }
  };

  // Check bot status
  const checkBotStatus = async (botId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/meeting-bot/${botId}/status`);
      const data = await response.json();
      
      if (data.success) {
        setBotStatus(data.status);
        
        if (data.status === 'completed' && data.transcript) {
          // Update transcript
          const fullTranscript = transcript + '\n\n' + data.transcript;
          setTranscript(fullTranscript);
          
          await updateMeeting(meetingId, {
            transcript: fullTranscript,
            status: 'completed',
          });
          
          setIsRecording(false);
        } else if (['failed', 'ended'].includes(data.status)) {
          setIsRecording(false);
          await updateMeeting(meetingId, { status: 'completed' });
        } else if (isRecording) {
          // Continue polling
          setTimeout(() => checkBotStatus(botId), 5000);
        }
      }
    } catch (error) {
      console.error('Error checking bot status:', error);
    }
  };

  // Search functionality
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const results: { index: number; text: string }[] = [];
    const query = searchQuery.toLowerCase();
    const lines = transcript.split('\n');

    lines.forEach((line, lineIndex) => {
      const lowerLine = line.toLowerCase();
      if (lowerLine.includes(query)) {
        results.push({ index: lineIndex, text: line });
      }
    });

    setSearchResults(results);
    setCurrentSearchIndex(0);
  }, [searchQuery, transcript]);

  // Navigate search results
  const navigateSearch = (direction: 'next' | 'prev') => {
    if (searchResults.length === 0) return;

    let newIndex = currentSearchIndex;
    if (direction === 'next') {
      newIndex = (currentSearchIndex + 1) % searchResults.length;
    } else {
      newIndex = currentSearchIndex === 0 ? searchResults.length - 1 : currentSearchIndex - 1;
    }

    setCurrentSearchIndex(newIndex);
    searchHighlightRefs.current[newIndex]?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });
  };

  // Download transcript
  const downloadTranscript = () => {
    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${meeting?.title.replace(/[^a-z0-9]/gi, '_')}_transcript.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Start chat with transcript
  const startChatWithTranscript = async () => {
    // Save current transcript
    await updateMeeting(meetingId, { transcript });
    
    // Navigate to dashboard with meeting attachment
    router.push(`/dashboard?attachMeeting=${meetingId}`);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col">
        <div className="border-b px-6 py-4">
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="flex-1 p-6">
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-semibold mb-2">Meeting not found</h2>
          <Button onClick={() => router.push('/meetings')}>
            Back to Meetings
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/meetings')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-xl font-semibold">{meeting.title}</h1>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
              <span>{formatDistanceToNow(new Date(meeting.created_at), { addSuffix: true })}</span>
              <Badge variant={meeting.status === 'active' ? 'default' : 'secondary'}>
                {meeting.status}
              </Badge>
              {botStatus && (
                <Badge variant="outline">{botStatus}</Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={downloadTranscript}
            disabled={!transcript}
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => toast.info('Sharing coming soon')}
          >
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Button
            size="sm"
            onClick={startChatWithTranscript}
            disabled={!transcript}
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Talk to Operator
          </Button>
        </div>
      </div>

      {/* Search bar */}
      <div className="px-6 py-3 border-b">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search in transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-20 h-9"
          />
          {searchResults.length > 0 && (
            <div className="absolute right-2 top-2 flex items-center gap-1 text-xs text-muted-foreground">
              <span>{currentSearchIndex + 1}/{searchResults.length}</span>
              <div className="flex">
                <button
                  onClick={() => navigateSearch('prev')}
                  className="p-0.5 hover:bg-accent rounded"
                >
                  ↑
                </button>
                <button
                  onClick={() => navigateSearch('next')}
                  className="p-0.5 hover:bg-accent rounded"
                >
                  ↓
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Transcript area */}
      <ScrollArea className="flex-1 px-6 py-4">
        <div ref={transcriptRef} className="max-w-4xl mx-auto">
          {transcript ? (
            <div className="whitespace-pre-wrap font-mono text-sm">
              {transcript.split('\n').map((line, index) => {
                const isSearchMatch = searchResults.some((r) => r.index === index);
                const isCurrentMatch = searchResults[currentSearchIndex]?.index === index;

                return (
                  <div
                    key={index}
                    className={cn(
                      'py-1',
                      isSearchMatch && 'bg-yellow-100 dark:bg-yellow-900/30',
                      isCurrentMatch && 'bg-yellow-200 dark:bg-yellow-800/50'
                    )}
                  >
                    <span
                      ref={(el) => {
                        if (isCurrentMatch) {
                          searchHighlightRefs.current[currentSearchIndex] = el;
                        }
                      }}
                    >
                      {line || '\u00A0'}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              {meeting.status === 'active' ? (
                <p>Start recording to see the transcript here</p>
              ) : (
                <p>No transcript available</p>
              )}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Recording controls */}
      {meeting.status === 'active' && (
        <div className="border-t px-6 py-4 bg-background">
          {!isRecording ? (
            <div className="flex items-center justify-center gap-4">
              <Button
                onClick={() => startRecording('local')}
                disabled={isRecording}
                variant="outline"
              >
                <User className="h-4 w-4 mr-2" />
                Record In-Person
              </Button>
              <Button
                onClick={() => startRecording('online')}
                disabled={isRecording}
                variant="outline"
              >
                <Monitor className="h-4 w-4 mr-2" />
                Record Online Meeting
              </Button>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-4">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium">
                  {recordingMode === 'local' ? 'Recording...' : `Bot ${botStatus}`}
                </span>
              </div>
              <Button
                onClick={stopRecording}
                variant="destructive"
                size="sm"
              >
                <Square className="h-4 w-4 mr-2" />
                Stop Recording
              </Button>
            </div>
          )}

          {recordingMode === 'local' && !isRecording && (
            <Alert className="mt-4 max-w-2xl mx-auto">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                For best results, speak clearly and ensure you're in a quiet environment.
                The transcript will appear in real-time as you speak.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </div>
  );
} 