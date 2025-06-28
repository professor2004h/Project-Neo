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
  FileAudio,
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
  const [interimTranscript, setInterimTranscript] = useState('');
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
      
      // If meeting is active and has bot metadata, reconnect to existing bot
      if (data.status === 'active' && data.metadata?.bot_id) {
        setRecordingMode('online');
        setIsRecording(true);
        setBotStatus('checking...');
        toast.info('Reconnecting to existing meeting bot...');
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
          // Don't add WebSocket text if it's duplicate from speech recognition
          setTranscript((prev) => {
            const cleanText = text.trim();
            if (!cleanText || prev.includes(cleanText)) return prev;
            const cleanPrev = prev.trim();
            return cleanPrev + (cleanPrev ? '\n' : '') + cleanText;
          });
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
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript.trim()) {
        // Send final transcript through WebSocket and add to local state
        wsConnection?.sendTranscript(finalTranscript.trim());
        setTranscript((prev) => {
          const cleanPrev = prev.trim(); // Remove trailing whitespace
          return cleanPrev + (cleanPrev ? '\n' : '') + finalTranscript.trim();
        });
      }
      
      // Store interim results separately for display only
      setInterimTranscript(interimTranscript);
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
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/meeting-bot/start`, {
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
          
          // Update meeting metadata with bot info and recording mode
          await updateMeeting(meetingId, {
            metadata: { bot_id: data.bot_id, meeting_url: meetingUrl },
            recording_mode: 'online',
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
        
        // If error is "AlreadyStarted", try to find existing bot
        if (error.message.includes('AlreadyStarted')) {
          try {
            // Try to get existing bot for this meeting URL
            const statusResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/meeting-bot/find`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                meeting_url: meetingUrl,
                sandbox_id: meetingId,
              }),
            });

            const statusData = await statusResponse.json();
            if (statusData.success && statusData.bot_id) {
              setBotStatus(statusData.status || 'in_call');
              setIsRecording(true);
              
              // Update meeting metadata with existing bot info
              await updateMeeting(meetingId, {
                metadata: { bot_id: statusData.bot_id, meeting_url: meetingUrl },
                recording_mode: 'online',
                status: 'active',
              });

              toast.success('Reconnected to existing meeting bot!');
              checkBotStatus(statusData.bot_id);
            } else {
              toast.error('Bot already exists but could not reconnect');
            }
          } catch (findError) {
            console.error('Error finding existing bot:', findError);
            toast.error('Bot already running for this meeting URL. Please try again.');
          }
        } else {
          toast.error('Failed to start meeting bot');
        }
      }
    }
  };

  // Stop recording
  const stopRecording = async () => {
    if (recordingMode === 'local') {
      recognition?.stop();
      setIsRecording(false);
      setRecordingMode(null);
      wsConnection?.updateStatus('completed');
      
      // Save transcript
      await updateMeeting(meetingId, {
        transcript,
        status: 'completed',
      });
      
      toast.success('Recording stopped and saved');
    } else if (recordingMode === 'online' && meeting?.metadata?.bot_id) {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/meeting-bot/${meeting.metadata.bot_id}/stop`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            sandbox_id: meetingId,
          }),
        });

        const data = await response.json();
        if (data.success && data.content) {
          // Update transcript with bot's transcript
          const fullTranscript = transcript + '\n\n' + data.content;
          setTranscript(fullTranscript);
          
          await updateMeeting(meetingId, {
            transcript: fullTranscript,
            status: 'completed',
            metadata: { ...meeting?.metadata, bot_id: undefined } // Clear bot data
          });
          toast.success('Meeting recording completed and transcript saved');
        } else if (data.success) {
          // Meeting ended successfully but no transcript
          await updateMeeting(meetingId, {
            status: 'completed',
            metadata: { ...meeting?.metadata, bot_id: undefined }
          });
          toast.info('Meeting ended - no transcript was generated');
        } else {
          // Handle partial success or informational errors
          const errorMessage = data.error || 'Unknown error occurred';
          if (data.transcript) {
            // We got some transcript data despite the error
            const fullTranscript = transcript + '\n\n' + data.transcript;
            setTranscript(fullTranscript);
            await updateMeeting(meetingId, {
              transcript: fullTranscript,
              status: 'completed',
              metadata: { ...meeting?.metadata, bot_id: undefined }
            });
            toast.warning(`Meeting ended with issues: ${errorMessage}`);
          } else {
            // No transcript available
            await updateMeeting(meetingId, {
              status: 'completed',
              metadata: { ...meeting?.metadata, bot_id: undefined }
            });
            toast.error(`Failed to get transcript: ${errorMessage}`);
          }
        }
        
        setIsRecording(false);
        setRecordingMode(null);
        setBotStatus('completed');
        toast.success('Meeting recording completed');
      } catch (error) {
        console.error('Error stopping bot:', error);
        // Even on error, clean up the UI state
        setIsRecording(false);
        setRecordingMode(null);
        setBotStatus('');
        toast.error('Failed to stop meeting bot');
      }
    }
  };

  // Check bot status
  const checkBotStatus = async (botId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/meeting-bot/${botId}/status`);
      const data = await response.json();
      
      if (data.success) {
        setBotStatus(data.status);
        
        // If we just reconnected and bot is still active, continue recording
        if (['starting', 'in_call', 'recording'].includes(data.status)) {
          setIsRecording(true);
          setRecordingMode('online');
        }
        
        if (data.status === 'completed' && data.transcript) {
          // Update transcript
          const fullTranscript = transcript + '\n\n' + data.transcript;
          setTranscript(fullTranscript);
          
          await updateMeeting(meetingId, {
            transcript: fullTranscript,
            status: 'completed',
            metadata: { ...meeting?.metadata, bot_id: undefined } // Clear bot_id when completed
          });
          
          setIsRecording(false);
          setRecordingMode(null);
        } else if (['failed', 'ended'].includes(data.status)) {
          setIsRecording(false);
          setRecordingMode(null);
          await updateMeeting(meetingId, { 
            status: 'completed',
            metadata: { ...meeting?.metadata, bot_id: undefined } // Clear bot_id when failed
          });
        } else if (['starting', 'in_call', 'recording'].includes(data.status)) {
          // Continue polling for active bot
          setTimeout(() => checkBotStatus(botId), 5000);
        }
      } else {
        // Bot not found or error - clear bot data
        setIsRecording(false);
        setRecordingMode(null);
        setBotStatus('');
        await updateMeeting(meetingId, {
          metadata: { ...meeting?.metadata, bot_id: undefined }
        });
      }
    } catch (error) {
      console.error('Error checking bot status:', error);
      // On repeated errors, clean up the bot state
      // This handles cases where the bot was manually removed from the meeting
      if (isRecording && recordingMode === 'online') {
        setIsRecording(false);
        setRecordingMode(null);
        setBotStatus('');
        await updateMeeting(meetingId, {
          status: 'completed',
          metadata: { ...meeting?.metadata, bot_id: undefined }
        });
        toast.info('Bot session ended - meeting status has been updated');
      }
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
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b px-6 py-4 flex items-center justify-between">
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
      <div className="flex-shrink-0 px-6 py-3 border-b">
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
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full px-6 py-4 bg-gradient-to-b from-background to-muted/10">
          <div ref={transcriptRef} className="max-w-4xl mx-auto">
          {transcript || interimTranscript ? (
            <div className="bg-card/50 backdrop-blur border rounded-xl p-6 shadow-sm">
              <div className="prose dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {transcript.split('\n').map((line, index) => {
                    const isSearchMatch = searchResults.some((r) => r.index === index);
                    const isCurrentMatch = searchResults[currentSearchIndex]?.index === index;

                    return (
                      <div
                        key={index}
                        className={cn(
                          'py-1 px-2 rounded transition-all duration-200',
                          isSearchMatch && 'bg-yellow-100 dark:bg-yellow-900/30',
                          isCurrentMatch && 'bg-yellow-200 dark:bg-yellow-800/50 shadow-sm'
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
                  {interimTranscript && (
                    <span className="text-muted-foreground italic">
                      {interimTranscript}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-20">
              <div className="mx-auto w-16 h-16 bg-muted/20 rounded-full flex items-center justify-center mb-4">
                <FileAudio className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {meeting.status === 'active' ? 'Ready to Record' : 'No Transcript Available'}
              </h3>
              <p className="text-muted-foreground max-w-md mx-auto">
                {meeting.status === 'active' 
                  ? 'Start recording to see the real-time transcript appear here. Choose between in-person or online meeting recording.'
                  : 'This meeting doesn\'t have any recorded transcript yet.'
                }
              </p>
            </div>
          )}
        </div>
        </ScrollArea>
      </div>

      {/* Recording controls */}
      {meeting.status === 'active' && (
        <div className="flex-shrink-0 border-t bg-sidebar/50 backdrop-blur">
          <div className="px-6 py-4 max-h-32 overflow-visible">
            <div className="max-w-4xl mx-auto">
              {!isRecording ? (
                <div className="flex items-center justify-center">
                  <div className="flex items-center gap-1 bg-background rounded-xl border p-1 shadow-sm">
                    <button
                      onClick={() => startRecording('local')}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-accent transition-colors text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    >
                      <User className="h-4 w-4" />
                      <span className="text-sm font-medium">In Person</span>
                    </button>
                    <div className="w-px h-6 bg-border" />
                    <button
                      onClick={() => startRecording('online')}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-accent transition-colors text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                    >
                      <Monitor className="h-4 w-4" />
                      <span className="text-sm font-medium">Online</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <div className="flex items-center gap-4 bg-background rounded-xl border px-4 py-3 shadow-sm">
                    <div className="flex items-center gap-3">
                      {recordingMode === 'local' ? (
                        <div className="flex items-center gap-2">
                          <div className="relative">
                            <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse" />
                          </div>
                          <User className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <div className="relative">
                            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                          </div>
                          <Monitor className="h-4 w-4 text-green-600 dark:text-green-400" />
                        </div>
                      )}
                      <span className="text-sm font-medium tabular-nums">
                        {recordingMode === 'local' ? 'Recording...' : `Bot ${botStatus}`}
                      </span>
                    </div>
                    <button
                      onClick={stopRecording}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-medium transition-colors"
                    >
                      <Square className="h-3 w-3 fill-current" />
                      Stop
                    </button>
                  </div>
                </div>
              )}

              {!isRecording && (
                <div className="text-center mt-4">
                  <p className="text-xs text-muted-foreground max-w-md mx-auto">
                    Choose <strong>In Person</strong> for real-time speech-to-text or <strong>Online</strong> to join virtual meetings with a bot
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 