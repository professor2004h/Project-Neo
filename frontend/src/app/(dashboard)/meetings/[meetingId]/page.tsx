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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';

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
  const [isPaused, setIsPaused] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [wsConnection, setWsConnection] = useState<TranscriptionWebSocket | null>(null);
  const [botStatus, setBotStatus] = useState<string>('');
  
  // Meeting URL dialog state
  const [showMeetingUrlDialog, setShowMeetingUrlDialog] = useState(false);
  const [meetingUrl, setMeetingUrl] = useState('');
  
  // Timestamp tracking for local recordings
  const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
  const [totalPausedTime, setTotalPausedTime] = useState<number>(0);
  const [pauseStartTime, setPauseStartTime] = useState<number | null>(null);

  const transcriptRef = useRef<HTMLDivElement>(null);
  const searchHighlightRefs = useRef<(HTMLSpanElement | null)[]>([]);

  // Auto-scroll to bottom when transcript updates
  useEffect(() => {
    if (transcriptRef.current && (isRecording || interimTranscript)) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript, interimTranscript, isRecording]);

  // Calculate current elapsed time (excluding paused time)
  const getCurrentElapsedTime = (): number => {
    if (!recordingStartTime) return 0;
    const now = Date.now();
    const currentPausedTime = isPaused && pauseStartTime ? now - pauseStartTime : 0;
    return now - recordingStartTime - totalPausedTime - currentPausedTime;
  };

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
      if (isRecording && !isPaused) {
        // Restart if still recording and not paused
        recognition.start();
      }
    };

    return recognition;
  }, [wsConnection, isRecording, isPaused]);

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
        setIsPaused(false);
        setRecordingStartTime(Date.now());
        setTotalPausedTime(0);
        setPauseStartTime(null);
        wsConnection?.updateStatus('active');
        
        // If meeting was completed, reactivate it
        if (meeting?.status === 'completed') {
          await updateMeeting(meetingId, { status: 'active' });
        }
        
        toast.success('Recording started');
      } catch (error) {
        console.error('Error starting recording:', error);
        toast.error('Failed to start recording');
      }
    } else {
      // For online mode, show meeting URL input dialog
      setShowMeetingUrlDialog(true);
    }
  };

  // Continue recording (start a new session on existing transcript)
  const continueRecording = async (mode: 'local' | 'online') => {
    // Add a session separator to the transcript
    const sessionSeparator = `\n\n--- New Recording Session (${new Date().toLocaleString()}) ---\n`;
    setTranscript(prev => prev + sessionSeparator);
    
    // Update meeting status to active and save the separator
    await updateMeeting(meetingId, { 
      status: 'active',
      transcript: transcript + sessionSeparator
    });
    
    // Start recording normally
    await startRecording(mode);
  };

  // Clean bot status display with minimal indicators
  const getBotStatusDisplay = (status: string) => {
    switch (status) {
      case 'starting':
        return <span className="text-blue-600 dark:text-blue-400">Starting bot...</span>;
      case 'joining':
        return <span className="text-amber-600 dark:text-amber-400">Joining meeting...</span>;
      case 'waiting':
        return <span className="text-amber-600 dark:text-amber-400">Waiting for access</span>;
      case 'in_call':
        return <span className="text-green-600 dark:text-green-400">In meeting</span>;
      case 'recording':
        return <span className="text-red-600 dark:text-red-400">Recording active</span>;
      case 'stopping':
        return <span className="text-orange-600 dark:text-orange-400">Stopping...</span>;
      case 'completed':
        return <span className="text-green-600 dark:text-green-400">Complete</span>;
      case 'failed':
        return <span className="text-red-600 dark:text-red-400">Failed</span>;
      case 'ended':
        return <span className="text-gray-600 dark:text-gray-400">Ended</span>;
      default:
        return <span className="text-muted-foreground">{status}</span>;
    }
  };

  // Handle starting online recording with URL
  const handleStartOnlineRecording = async () => {
    if (!meetingUrl.trim()) return;

    setShowMeetingUrlDialog(false);

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

    // Clear the URL for next time
    setMeetingUrl('');
  };

  // Stop recording
  const stopRecording = async () => {
    if (recordingMode === 'local') {
      recognition?.stop();
      setIsRecording(false);
      setIsPaused(false);
      setRecordingMode(null);
      setRecordingStartTime(null);
      setTotalPausedTime(0);
      setPauseStartTime(null);
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
        } else if (data.success && data.status === 'stopping') {
          // Bot is stopping, wait for final transcript via polling
          toast.info('Stopping meeting bot, waiting for final transcript...');
          setBotStatus('stopping');
          
          // Continue polling for the final result
          setTimeout(() => {
            if (meeting?.metadata?.bot_id) {
              checkBotStatusWithPolling(meeting.metadata.bot_id);
            }
          }, 2000);
          
          return; // Don't set recording to false yet
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

  // Pause recording (local only)
  const pauseRecording = () => {
    if (recordingMode === 'local' && recognition) {
      recognition.stop();
      setIsPaused(true);
      setPauseStartTime(Date.now());
      toast.info('Recording paused');
    }
  };

  // Resume recording (local only)
  const resumeRecording = () => {
    if (recordingMode === 'local' && recognition && isPaused && pauseStartTime) {
      const pauseDuration = Date.now() - pauseStartTime;
      setTotalPausedTime(prev => prev + pauseDuration);
      setPauseStartTime(null);
      recognition.start();
      setIsPaused(false);
      toast.info('Recording resumed');
    }
  };

  // Real-time bot status with SSE and enhanced polling
  const [sseConnection, setSseConnection] = useState<EventSource | null>(null);
  const [statusRetryCount, setStatusRetryCount] = useState(0);
  const [lastStatusUpdate, setLastStatusUpdate] = useState<number>(Date.now());

  // Enhanced bot status checking with real-time updates
  const startBotStatusMonitoring = (botId: string) => {
    // Start SSE connection for real-time updates
    const setupSSE = () => {
      try {
        const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_BACKEND_URL}/meeting-bot/${botId}/events`);
        
        eventSource.onopen = () => {
          console.log('[SSE] Connected to bot status stream');
          setStatusRetryCount(0);
        };
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastStatusUpdate(Date.now());
            
            if (data.type === 'status_update') {
              const newStatus = data.status;
              console.log(`[SSE] Bot status update: ${newStatus}`);
              setBotStatus(newStatus);
              
              // Handle status-specific actions
              if (['starting', 'joining', 'waiting', 'in_call', 'recording'].includes(newStatus)) {
                setIsRecording(true);
                setRecordingMode('online');
              } else if (['completed', 'ended', 'failed'].includes(newStatus)) {
                setIsRecording(false);
                setRecordingMode(null);
                eventSource.close();
                setSseConnection(null);
              }
            }
          } catch (parseError) {
            console.error('[SSE] Error parsing message:', parseError);
          }
        };
        
        eventSource.onerror = (error) => {
          console.error('[SSE] Connection error:', error);
          eventSource.close();
          setSseConnection(null);
          
          // Fallback to polling with retry logic
          if (statusRetryCount < 3) {
            setTimeout(() => {
              setStatusRetryCount(prev => prev + 1);
              setupSSE();
            }, Math.min(1000 * Math.pow(2, statusRetryCount), 5000));
          } else {
            // Switch to enhanced polling mode
            checkBotStatusWithPolling(botId);
          }
        };
        
        setSseConnection(eventSource);
      } catch (error) {
        console.error('[SSE] Failed to setup EventSource:', error);
        // Fallback to enhanced polling
        checkBotStatusWithPolling(botId);
      }
    };
    
    setupSSE();
    
    // Also start polling as backup (less frequent than SSE)
    checkBotStatusWithPolling(botId);
  };

  // Enhanced polling with adaptive intervals
  const checkBotStatusWithPolling = async (botId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/meeting-bot/${botId}/status`);
      const data = await response.json();
      
      if (data.success) {
        const newStatus = data.status;
        setBotStatus(newStatus);
        setLastStatusUpdate(Date.now());
        
        // If we just reconnected and bot is still active, continue recording
        if (['starting', 'joining', 'waiting', 'in_call', 'recording'].includes(newStatus)) {
          setIsRecording(true);
          setRecordingMode('online');
        }
        
        if (newStatus === 'completed' && data.transcript) {
          // Update transcript
          const fullTranscript = transcript + '\n\n' + data.transcript;
          setTranscript(fullTranscript);
          
          await updateMeeting(meetingId, {
            transcript: fullTranscript,
            status: 'completed',
            metadata: { ...meeting?.metadata, bot_id: undefined }
          });
          
          setIsRecording(false);
          setRecordingMode(null);
          setBotStatus('completed');
          
          // Stop monitoring
          if (sseConnection) {
            sseConnection.close();
            setSseConnection(null);
          }
          
          toast.success('Meeting transcript received and saved');
          return;
        } else if (newStatus === 'failed') {
          // Bot failed - stop immediately
          setIsRecording(false);
          setRecordingMode(null);
          setBotStatus('failed');
          await updateMeeting(meetingId, { 
            status: 'completed',
            metadata: { ...meeting?.metadata, bot_id: undefined }
          });
          
          // Stop monitoring
          if (sseConnection) {
            sseConnection.close();
            setSseConnection(null);
          }
          toast.error('Meeting bot failed');
          return;
        } else if (newStatus === 'ended') {
          // Meeting ended naturally - continue polling for final transcript
          setBotStatus('ended');
          setIsRecording(false); // Stop the UI recording state
          
          // Continue polling for the "completed" status with transcript
          setTimeout(() => checkBotStatusWithPolling(botId), 1000);
          return;
        } else if (['starting', 'joining', 'waiting', 'in_call', 'recording', 'stopping'].includes(newStatus)) {
          // Adaptive polling intervals based on status
          let pollInterval;
          switch (newStatus) {
            case 'starting':
            case 'joining':
              pollInterval = 500; // Very frequent during critical joining phase
              break;
            case 'waiting':
              pollInterval = 1000; // Frequent while waiting
              break;
            case 'in_call':
              pollInterval = 2000; // Moderate once in call
              break;
            case 'recording':
              pollInterval = 5000; // Less frequent once recording
              break;
            case 'stopping':
              pollInterval = 1000; // Frequent while waiting for final transcript
              break;
            default:
              pollInterval = 2000;
          }
          
          setTimeout(() => checkBotStatusWithPolling(botId), pollInterval);
        }
      } else {
        // Bot not found or error - clear bot data
        setIsRecording(false);
        setRecordingMode(null);
        setBotStatus('');
        await updateMeeting(meetingId, {
          metadata: { ...meeting?.metadata, bot_id: undefined }
        });
        
        if (sseConnection) {
          sseConnection.close();
          setSseConnection(null);
        }
      }
    } catch (error) {
      console.error('Error checking bot status:', error);
      
      // Check if we've lost connection for too long
      const timeSinceLastUpdate = Date.now() - lastStatusUpdate;
      if (timeSinceLastUpdate > 30000) { // 30 seconds without update
        // Clean up the bot state
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
        
        if (sseConnection) {
          sseConnection.close();
          setSseConnection(null);
        }
      } else {
        // Retry with exponential backoff
        const retryDelay = Math.min(1000 * Math.pow(2, statusRetryCount), 10000);
        setTimeout(() => {
          setStatusRetryCount(prev => prev + 1);
          checkBotStatusWithPolling(botId);
        }, retryDelay);
      }
    }
  };

  // Cleanup SSE connection on unmount
  useEffect(() => {
    return () => {
      if (sseConnection) {
        sseConnection.close();
        setSseConnection(null);
      }
    };
  }, [sseConnection]);

  // Legacy function for backward compatibility
  const checkBotStatus = (botId: string) => {
    startBotStatusMonitoring(botId);
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
      <div className="flex-shrink-0 border-b bg-gradient-to-r from-background/95 via-background to-background/95 backdrop-blur-sm px-6 py-5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/meetings')}
            className="hover:bg-accent/80 transition-all duration-200 hover:scale-105"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-xl font-semibold bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text">
              {meeting.title}
            </h1>
            <div className="flex items-center gap-2 text-sm mt-2">
              <span className="text-muted-foreground/80">
                {formatDistanceToNow(new Date(meeting.created_at), { addSuffix: true })}
              </span>
              <Badge 
                variant={meeting.status === 'active' ? 'default' : 'secondary'}
                className="shadow-sm"
              >
                {meeting.status}
              </Badge>
              {botStatus && (
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground/70">
                  {getBotStatusDisplay(botStatus)}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-card/60 backdrop-blur border border-border/50 rounded-xl p-1 shadow-sm hover:shadow-md transition-all duration-300">
            <Button
              variant="ghost"
              size="sm"
              onClick={downloadTranscript}
              disabled={!transcript}
              className="hover:bg-blue-50 dark:hover:bg-blue-950/30 text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-all duration-200 hover:scale-105 disabled:opacity-50"
            >
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
            <div className="w-px h-6 bg-gradient-to-t from-transparent via-border to-transparent mx-1" />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toast.info('Sharing coming soon')}
              className="hover:bg-purple-50 dark:hover:bg-purple-950/30 text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 transition-all duration-200 hover:scale-105"
            >
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
          </div>
          <Button
            size="sm"
            onClick={startChatWithTranscript}
            disabled={!transcript}
            className="bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-sm hover:shadow-md transition-all duration-200 hover:scale-105 disabled:opacity-50"
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Talk to Operator
          </Button>
        </div>
      </div>

      {/* Search bar */}
      <div className="flex-shrink-0 px-6 py-4 border-b bg-gradient-to-r from-background/50 to-background/80 backdrop-blur">
        <div className="relative max-w-lg">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/60">
            <Search className="h-4 w-4" />
          </div>
          <Input
            placeholder="Search within transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-24 h-10 bg-card/50 backdrop-blur border-border/50 shadow-sm focus:shadow-md transition-all duration-200 focus:scale-[1.02] placeholder:text-muted-foreground/60"
          />
          {searchResults.length > 0 && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 text-xs">
              <span className="text-muted-foreground/80 bg-background/80 px-2 py-1 rounded-md font-medium">
                {currentSearchIndex + 1}/{searchResults.length}
              </span>
              <div className="flex bg-background/80 backdrop-blur rounded-md border border-border/30 shadow-sm">
                <button
                  onClick={() => navigateSearch('prev')}
                  className="p-1.5 hover:bg-accent/80 rounded-l-md transition-all duration-200 hover:scale-110 text-muted-foreground hover:text-foreground"
                  aria-label="Previous result"
                >
                  ↑
                </button>
                <button
                  onClick={() => navigateSearch('next')}
                  className="p-1.5 hover:bg-accent/80 rounded-r-md transition-all duration-200 hover:scale-110 text-muted-foreground hover:text-foreground"
                  aria-label="Next result"
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
        <ScrollArea className="h-full px-6 py-4 bg-gradient-to-b from-background to-muted/10" ref={transcriptRef}>
          <div className="max-w-4xl mx-auto">
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
                    <div className="text-muted-foreground italic mt-2">
                      {interimTranscript}
                    </div>
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
      {(meeting.status === 'active' || (meeting.status === 'completed' && transcript)) && (
        <div className="flex-shrink-0 border-t bg-gradient-to-r from-background/95 via-background to-background/95 backdrop-blur-sm">
          <div className="px-6 py-6 max-h-36 overflow-visible">
            <div className="max-w-4xl mx-auto">
              {!isRecording ? (
                <div className="flex flex-col items-center justify-center space-y-4">
                  {meeting.status === 'completed' ? (
                    /* Continue Recording Section */
                    <>
                      <div className="text-center mb-3">
                        <p className="text-sm font-medium text-foreground/90 mb-1">Meeting Completed</p>
                        <p className="text-xs text-muted-foreground/80">Start a new recording session to continue adding to this transcript</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Button
                          onClick={() => continueRecording('local')}
                          variant="outline"
                          className="flex items-center gap-2 px-4 py-2 h-auto rounded-lg transition-all duration-200"
                        >
                          <User className="h-4 w-4" />
                          <span className="font-medium">Continue In Person</span>
                        </Button>
                        
                        <Button
                          onClick={() => continueRecording('online')}
                          variant="outline"
                          className="flex items-center gap-2 px-4 py-2 h-auto rounded-lg transition-all duration-200"
                        >
                          <Monitor className="h-4 w-4" />
                          <span className="font-medium">Continue Online</span>
                        </Button>
                      </div>
                    </>
                  ) : (
                    /* Initial Recording Section */
                    <>
                      <div className="flex items-center gap-3">
                        <Button
                          onClick={() => startRecording('local')}
                          variant="outline"
                          className="flex items-center gap-2 px-4 py-2 h-auto rounded-lg transition-all duration-200"
                        >
                          <User className="h-4 w-4" />
                          <span className="font-medium">In Person</span>
                        </Button>
                        
                        <Button
                          onClick={() => startRecording('online')}
                          variant="outline"
                          className="flex items-center gap-2 px-4 py-2 h-auto rounded-lg transition-all duration-200"
                        >
                          <Monitor className="h-4 w-4" />
                          <span className="font-medium">Online</span>
                        </Button>
                      </div>
                      
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground/80 max-w-lg mx-auto leading-relaxed">
                          Choose <span className="font-medium text-blue-600 dark:text-blue-400">In Person</span> for real-time speech-to-text or <span className="font-medium text-green-600 dark:text-green-400">Online</span> to join virtual meetings with a bot
                        </p>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <div className="flex items-center justify-between w-full max-w-sm bg-card/50 backdrop-blur border border-border/50 rounded-xl px-4 py-3 shadow-sm">
                    {/* Recording status */}
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-muted/50 flex items-center justify-center">
                          {recordingMode === 'local' ? (
                            <User className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Monitor className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                        <div className="text-sm">
                          {recordingMode === 'local' ? (
                            <span className="font-medium text-foreground">
                              {isPaused ? 'Paused' : 'Recording'}
                            </span>
                          ) : (
                            <div className="font-medium text-foreground">
                              {getBotStatusDisplay(botStatus)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Control buttons */}
                    <div className="flex items-center gap-2">
                      {recordingMode === 'local' && (
                        <Button
                          onClick={isPaused ? resumeRecording : pauseRecording}
                          size="sm"
                          variant="outline"
                          className="h-8 px-3 text-xs"
                        >
                          {isPaused ? (
                            <>
                              <Play className="h-3 w-3 mr-1" />
                              Resume
                            </>
                          ) : (
                            <>
                              <Pause className="h-3 w-3 mr-1" />
                              Pause
                            </>
                          )}
                        </Button>
                      )}
                      
                      <Button
                        onClick={stopRecording}
                        size="sm"
                        variant="destructive"
                        className="h-8 px-3 text-xs"
                      >
                        <Square className="h-3 w-3 mr-1" />
                        Stop
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Meeting URL Dialog */}
      <Dialog open={showMeetingUrlDialog} onOpenChange={(open) => {
        setShowMeetingUrlDialog(open);
        if (!open) setMeetingUrl('');
      }}>
        <DialogContent className="max-w-md bg-gradient-to-br from-card/95 via-card to-card/90 backdrop-blur border border-border/50 shadow-2xl">
          <DialogHeader className="space-y-3">
            <DialogTitle className="text-xl font-semibold bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text">
              Join Online Meeting
            </DialogTitle>
            <DialogDescription className="text-muted-foreground/80 leading-relaxed">
              Enter the meeting URL to join with an AI bot that will record and transcribe the conversation
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="space-y-2">
              <Label htmlFor="meeting-url" className="text-sm font-medium text-foreground/90">
                Meeting URL
              </Label>
              <Input
                id="meeting-url"
                value={meetingUrl}
                onChange={(e) => setMeetingUrl(e.target.value)}
                placeholder="https://zoom.us/j/123456789 or https://meet.google.com/abc-defg-hij"
                onKeyDown={(e) => e.key === 'Enter' && handleStartOnlineRecording()}
                className="h-11 bg-background/50 backdrop-blur border-border/50 shadow-sm focus:shadow-md transition-all duration-200 focus:scale-[1.01] placeholder:text-muted-foreground/60"
              />
            </div>
          </div>
          <DialogFooter className="gap-3">
            <Button 
              variant="outline" 
              onClick={() => setShowMeetingUrlDialog(false)}
              className="shadow-sm hover:shadow-md transition-all duration-200"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleStartOnlineRecording} 
              disabled={!meetingUrl.trim()}
              className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-sm hover:shadow-md transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Monitor className="h-4 w-4 mr-2" />
              Start Bot Recording
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
} 