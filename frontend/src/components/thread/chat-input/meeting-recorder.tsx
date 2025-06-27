/**
 * Meeting Recorder Component
 * 
 * Supports two recording modes:
 * 1. In-Person: Records microphone directly from device
 * 2. Online: Sends a bot to join meeting via MeetingBaaS API
 * 
 * MeetingBaaS Integration:
 * - $0.69/hour transcription bot service
 * - Supports Zoom, Teams, Google Meet
 * - Bot joins meeting, records, and transcribes
 * - API: POST /api/meeting-bot/start { meetingUrl }
 */

import React, { useState, useRef, useEffect } from 'react';
import { Circle, Pause, Play, Check, X, Square, User, Monitor } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { UploadedFile } from './chat-input';
import { normalizeFilenameToNFC } from '@/lib/utils/unicode';
import { handleFiles } from './file-upload-handler';
import { useQueryClient } from '@tanstack/react-query';
import { backendApi } from '@/lib/api-client';

interface MeetingRecorderProps {
  onFileAttached: (file: UploadedFile) => void;
  setPendingFiles: React.Dispatch<React.SetStateAction<File[]>>;
  setUploadedFiles: React.Dispatch<React.SetStateAction<UploadedFile[]>>;
  setIsUploading: React.Dispatch<React.SetStateAction<boolean>>;
  sandboxId?: string;
  messages?: any[];
  disabled?: boolean;
}

const MAX_RECORDING_TIME = 2 * 60 * 60 * 1000; // 2 hours in milliseconds

type RecordingMode = 'microphone-only' | 'meeting-bot' | 'failed';
type UIState = 'idle' | 'split' | 'recording' | 'paused' | 'stopped';

export const MeetingRecorder: React.FC<MeetingRecorderProps> = ({
  onFileAttached,
  setPendingFiles,
  setUploadedFiles,
  setIsUploading,
  sandboxId,
  messages = [],
  disabled = false,
}) => {
  const queryClient = useQueryClient();
  const [uiState, setUIState] = useState<UIState>('idle');
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingMode, setRecordingMode] = useState<RecordingMode>('microphone-only');
  const [meetingUrl, setMeetingUrl] = useState<string>('');
  const [botId, setBotId] = useState<string>('');
  const [botStatus, setBotStatus] = useState<string>('');
  const [isPolling, setIsPolling] = useState(false);
  const [isUrlPopoverOpen, setIsUrlPopoverOpen] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamsRef = useRef<{
    microphone?: MediaStream;
  }>({});
  const recordingStartTimeRef = useRef<number | null>(null);
  const pausedDurationRef = useRef<number>(0);
  const pauseStartTimeRef = useRef<number | null>(null);
  const timerIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const maxTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-collapse split after 5 seconds if no selection
  useEffect(() => {
    if (uiState === 'split') {
      const timeout = setTimeout(() => {
        setUIState('idle');
      }, 5000);
      return () => clearTimeout(timeout);
    }
  }, [uiState]);

  // Update recording time
  useEffect(() => {
    if (uiState === 'recording') {
      timerIntervalRef.current = setInterval(() => {
        if (recordingStartTimeRef.current) {
          const elapsed = Date.now() - recordingStartTimeRef.current - pausedDurationRef.current;
          setRecordingTime(elapsed);
        }
      }, 100);
    } else {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    }

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [uiState]);

  // Auto-stop after 2 hours
  useEffect(() => {
    if (uiState === 'recording') {
      const remainingTime = MAX_RECORDING_TIME - recordingTime;
      if (remainingTime > 0) {
        maxTimeoutRef.current = setTimeout(() => {
          console.log('[MEETING RECORDER] Auto-stopping recording after 2 hours');
          stopRecording();
        }, remainingTime);
      }
    } else {
      if (maxTimeoutRef.current) {
        clearTimeout(maxTimeoutRef.current);
        maxTimeoutRef.current = null;
      }
    }

    return () => {
      if (maxTimeoutRef.current) {
        clearTimeout(maxTimeoutRef.current);
      }
    };
  }, [uiState, recordingTime]);

  const formatTime = (ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const startInPersonRecording = async () => {
    try {
      setUIState('recording');
      setRecordingMode('microphone-only');
      
      console.log('[MEETING RECORDER] Starting in-person recording (microphone only)...');
      
      // Get microphone stream only
      const microphoneStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      
      console.log('[MEETING RECORDER] Microphone access granted');
      
      // Store stream for cleanup
      streamsRef.current.microphone = microphoneStream;
      
      await startRecordingWithStream(microphoneStream, 'microphone-only');
      
    } catch (error) {
      console.error('[MEETING RECORDER] Error starting in-person recording:', error);
      setUIState('idle');
      setRecordingMode('failed');
      cleanupStreams();
    }
  };

  const startOnlineRecording = () => {
    // Open URL popover for meeting bot transcription
    setIsUrlPopoverOpen(true);
  };

  const handleMeetingUrlSubmit = async (url: string) => {
    if (!url.trim()) return;
    
    try {
      console.log('[MEETING RECORDER] Starting meeting bot transcription for:', url);
      
      setMeetingUrl(url.trim());
      setRecordingMode('meeting-bot');
      setUIState('recording');
      setBotStatus('starting...');
      setIsUrlPopoverOpen(false); // Close the popover
      
      // Start the meeting bot using backendApi
      const result = await backendApi.post('/meeting-bot/start', {
        meeting_url: url.trim(),
        sandbox_id: sandboxId
      });
      
      if (result.success && result.data) {
        setBotId(result.data.bot_id);
        setBotStatus(result.data.status);
        startRealTimeUpdates(result.data.bot_id);
        console.log(`[MEETING RECORDER] Bot started with ID: ${result.data.bot_id}`);
      } else {
        throw new Error(result.error?.message || 'Failed to start meeting bot');
      }
      
    } catch (error) {
      console.error('[MEETING RECORDER] Error starting meeting bot:', error);
      setUIState('idle');
      setRecordingMode('failed');
      setBotStatus('failed');
      setIsUrlPopoverOpen(false); // Close popover on error too
    }
  };

  const startRealTimeUpdates = (botId: string) => {
    setIsPolling(true);
    
    // Use Server-Sent Events for real-time updates (replaces polling!)
    const eventSource = new EventSource(`/api/meeting-bot/${botId}/events`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'connected') {
          console.log('[MEETING RECORDER] Real-time connection established');
          return;
        }
        
        if (data.type === 'heartbeat') {
          return; // Keep-alive, no action needed
        }
        
        // Update bot status from real-time webhook
        if (data.bot_id === botId && data.status) {
          setBotStatus(data.status);
          
          // Share status with other tabs via localStorage
          localStorage.setItem(`meeting_bot_status_${botId}`, JSON.stringify({
            value: data.status,
            timestamp: Date.now()
          }));
          
          // Handle meeting completion (MeetingBaaS sends 'completed' status)
          if (data.status === 'completed' && !localStorage.getItem(`meeting_bot_completed_${botId}`)) {
            localStorage.setItem(`meeting_bot_completed_${botId}`, 'true');
            stopRealTimeUpdates();
            handleMeetingComplete(botId);
          }
        }
      } catch (error) {
        console.error('[MEETING RECORDER] Error processing real-time update:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('[MEETING RECORDER] SSE connection error:', error);
      eventSource.close();
      
      // Fallback to single status check after connection issues
      setTimeout(async () => {
        try {
          const result = await backendApi.get(`/meeting-bot/${botId}/status`);
          if (result.success && result.data) {
            setBotStatus(result.data.status);
          }
        } catch (e) {
          console.error('[MEETING RECORDER] Fallback status check failed:', e);
        }
      }, 5000);
    };
    
    // Store reference for cleanup
    pollingIntervalRef.current = eventSource as any;
  };

  const stopRealTimeUpdates = () => {
    setIsPolling(false);
    if (pollingIntervalRef.current) {
      // Close SSE connection or clear interval
      if (pollingIntervalRef.current.close) {
        pollingIntervalRef.current.close();
      } else {
        clearInterval(pollingIntervalRef.current);
      }
      pollingIntervalRef.current = null;
    }
  };

  const handleMeetingComplete = async (botId: string) => {
    try {
      const result = await backendApi.post(`/meeting-bot/${botId}/stop`, {
        sandbox_id: sandboxId
      });
      
      if (result.success && result.data?.content) {
        // Create file object for transcript
        const blob = new Blob([result.data.content], { type: 'text/plain' });
        const file = new File([blob], result.data.filename, { type: 'text/plain' });
        
        // Auto-attach transcript using existing file upload system
        await handleFiles(
          [file],
          sandboxId,
          setPendingFiles,
          setUploadedFiles,
          setIsUploading,
          messages,
          queryClient,
        );
        
        setUIState('stopped');
        console.log('[MEETING RECORDER] Transcript auto-attached:', result.data.filename);
      }
    } catch (error) {
      console.error('[MEETING RECORDER] Error handling meeting completion:', error);
    }
  };

  // Check for existing bot sessions on mount (persistence)
  useEffect(() => {
    const checkExistingSessions = async () => {
      if (!sandboxId) return;
      
      try {
        const result = await backendApi.get(`/meeting-bot/sessions?sandbox_id=${sandboxId}`);
        
        if (result.success && result.data?.sessions?.length > 0) {
          const session = result.data.sessions[0]; // Get most recent
          setBotId(session.bot_id);
          setMeetingUrl(session.meeting_url);
          setRecordingMode('meeting-bot');
          setUIState('recording');
          setBotStatus(session.status);
          
          // Resume real-time updates if still active (not completed or failed)
          if (['joining', 'waiting', 'in_call', 'recording'].includes(session.status)) {
            startRealTimeUpdates(session.bot_id);
          }
          
          console.log('[MEETING RECORDER] Resumed existing bot session:', session.bot_id);
        }
      } catch (error) {
        console.error('[MEETING RECORDER] Error checking existing sessions:', error);
      }
    };
    
    checkExistingSessions();
  }, [sandboxId]);

  // Cleanup real-time updates on unmount
  useEffect(() => {
    return () => {
      stopRealTimeUpdates();
    };
  }, []);

  const startRecordingWithStream = async (recordingStream: MediaStream, mode: RecordingMode) => {
    // Create MediaRecorder with optimal settings
    let options: MediaRecorderOptions = {};
    
    // Try different MIME types for best compatibility
    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      options.mimeType = 'audio/webm;codecs=opus';
    } else if (MediaRecorder.isTypeSupported('audio/webm')) {
      options.mimeType = 'audio/webm';
    } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
      options.mimeType = 'audio/mp4';
    }
    
    // Set a reasonable bitrate for speech/meetings
    options.audioBitsPerSecond = 64000; // 64kbps is good for voice
    
    console.log(`[MEETING RECORDER] Using MIME type: ${options.mimeType || 'default'}`);
    console.log(`[MEETING RECORDER] Recording mode: ${mode}`);
    
    const mediaRecorder = new MediaRecorder(recordingStream, options);
    mediaRecorderRef.current = mediaRecorder;
    chunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      if (chunksRef.current.length > 0) {
        const blob = new Blob(chunksRef.current, { 
          type: options.mimeType || 'audio/webm'
        });
        console.log(`[MEETING RECORDER] Created blob: ${blob.size} bytes, type: ${blob.type}`);
        setAudioBlob(blob);
      }
      cleanupStreams();
    };

    mediaRecorder.onerror = (event) => {
      console.error('[MEETING RECORDER] MediaRecorder error:', event);
      setUIState('idle');
      cleanupStreams();
    };

    // Start recording with 5 second time slices for better data structure
    mediaRecorder.start(5000);
    recordingStartTimeRef.current = Date.now();
    pausedDurationRef.current = 0;
    
    console.log('[MEETING RECORDER] Recording started successfully');
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && uiState === 'recording') {
      mediaRecorderRef.current.pause();
      pauseStartTimeRef.current = Date.now();
      setUIState('paused');
      console.log('[MEETING RECORDER] Recording paused');
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && uiState === 'paused' && pauseStartTimeRef.current) {
      pausedDurationRef.current += Date.now() - pauseStartTimeRef.current;
      pauseStartTimeRef.current = null;
      mediaRecorderRef.current.resume();
      setUIState('recording');
      console.log('[MEETING RECORDER] Recording resumed');
    }
  };

  const stopRecording = async () => {
    if (uiState === 'recording' || uiState === 'paused') {
      if (recordingMode === 'meeting-bot' && botId) {
        console.log('[MEETING RECORDER] Manually stopping meeting bot');
        stopRealTimeUpdates();
        await handleMeetingComplete(botId);
      } else if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        console.log('[MEETING RECORDER] Recording stopped');
      }
      setUIState('stopped');
    }
  };

  const acceptRecording = async () => {
    if (audioBlob) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const extension = audioBlob.type.includes('mp4') ? 'mp4' : 'webm';
      const filename = normalizeFilenameToNFC(`meeting-recording-${timestamp}.${extension}`);
      const file = new File([audioBlob], filename, { type: audioBlob.type });
      
      // Use the same upload logic as normal file attachments
      await handleFiles(
        [file],
        sandboxId,
        setPendingFiles,
        setUploadedFiles,
        setIsUploading,
        messages,
        queryClient,
      );
      
      resetRecording();
    }
  };

  const deleteRecording = () => {
    if (audioBlob) {
      URL.revokeObjectURL(URL.createObjectURL(audioBlob));
    }
    resetRecording();
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setUIState('idle');
    setRecordingTime(0);
    setRecordingMode('microphone-only');
    setMeetingUrl('');
    setBotId('');
    setBotStatus('');
    setIsUrlPopoverOpen(false); // Close popover on reset
    stopRealTimeUpdates();
    recordingStartTimeRef.current = null;
    pausedDurationRef.current = 0;
    pauseStartTimeRef.current = null;
    chunksRef.current = [];
  };

  const getBotStatusText = () => {
    switch (botStatus) {
      case 'starting...':
        return 'Starting bot...';
      case 'joining':
        return 'Joining meeting...';
      case 'waiting':
        return 'In waiting room...';
      case 'in_call':
        return 'In meeting...';
      case 'recording':
        return 'Bot recording ●';
      case 'ended':
        return 'Call ended';
      case 'completed':
        return 'Complete!';
      case 'failed':
        return 'Failed';
      default:
        return botStatus || 'Bot active...';
    }
  };

  const cleanupStreams = () => {
    console.log('[MEETING RECORDER] Cleaning up streams...');
    
    // Stop microphone stream
    const { microphone } = streamsRef.current;
    
    if (microphone) {
      microphone.getTracks().forEach(track => {
        track.stop();
        console.log(`[MEETING RECORDER] Stopped ${track.kind} track`);
      });
    }
    
    // Clear stream references
    streamsRef.current = {};
  };

  const handleMainButtonClick = () => {
    if (uiState === 'idle') {
      setUIState('split');
    } else if (uiState === 'recording') {
      pauseRecording();
    } else if (uiState === 'paused') {
      resumeRecording();
    }
  };

  const getMainButtonIcon = () => {
    switch (uiState) {
      case 'idle':
      case 'split':
        return (
          <div className="relative h-4 w-4 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-2 border-current" />
            <div className="h-2 w-2 rounded-full bg-red-500" />
          </div>
        );
      case 'recording':
        return <Pause className="h-4 w-4" />;
      case 'paused':
        return <Play className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getMainButtonClass = () => {
    switch (uiState) {
      case 'recording':
        return 'text-yellow-500 hover:text-yellow-600 animate-pulse';
      case 'paused':
        return 'text-orange-500 hover:text-orange-600';
      default:
        return 'text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-neutral-100';
    }
  };

  const getTooltipText = () => {
    if (uiState === 'idle') {
      return 'Start recording';
    } else if (uiState === 'split') {
      return 'Choose recording type';
    } else if (uiState === 'recording') {
      return 'Pause recording';
    } else if (uiState === 'paused') {
      return 'Resume recording';
    }
    return '';
  };

  // Clean red completion tag
  if (uiState === 'stopped') {
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-md px-2 py-1">
          <div className="h-2 w-2 rounded-full bg-red-500"></div>
          <span className="text-sm font-medium text-red-700 dark:text-red-300">
            {formatTime(recordingTime)}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={acceptRecording}
            className="h-6 w-6 p-0 text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-950/30"
          >
            <Check className="h-3 w-3" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={deleteRecording}
            className="h-6 w-6 p-0 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>
    );
  }



  // Split state UI - two buttons side by side
  if (uiState === 'split') {
    return (
      <div className="flex items-center gap-1 animate-in slide-in-from-left-1 duration-200">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={startInPersonRecording}
                disabled={disabled}
                className="h-8 w-8 p-0 text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
              >
                <User className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>In Person</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        
        <Popover open={isUrlPopoverOpen} onOpenChange={setIsUrlPopoverOpen}>
          <TooltipProvider>
            <Tooltip>
              <PopoverTrigger asChild>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={startOnlineRecording}
                    disabled={disabled}
                    className="h-8 w-8 p-0 text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 transition-colors"
                  >
                    <Monitor className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
              </PopoverTrigger>
              <TooltipContent>Online</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <PopoverContent className="w-64 p-2" side="top" align="center" sideOffset={8}>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Meeting URL"
                value={meetingUrl}
                onChange={(e) => setMeetingUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleMeetingUrlSubmit(meetingUrl);
                  } else if (e.key === 'Escape') {
                    setIsUrlPopoverOpen(false);
                    setMeetingUrl('');
                  }
                }}
                className="flex-1 px-2 py-1.5 text-sm bg-transparent border border-neutral-200 dark:border-neutral-700 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 focus:border-green-500 dark:focus:ring-green-400 dark:focus:border-green-400 transition-colors"
                autoFocus
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setIsUrlPopoverOpen(false);
                  setMeetingUrl('');
                }}
                className="h-7 w-7 p-0 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-neutral-200 dark:hover:bg-neutral-800 transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => handleMeetingUrlSubmit(meetingUrl)}
                disabled={!meetingUrl.trim()}
                className="h-7 w-7 p-0 bg-green-600 hover:bg-green-700 disabled:bg-neutral-200 disabled:hover:bg-neutral-200 dark:disabled:bg-neutral-700 dark:disabled:hover:bg-neutral-700 text-white disabled:text-neutral-400 transition-colors"
              >
                <Check className="h-3.5 w-3.5" />
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    );
  }

  // Subtle recording panel
  if (uiState === 'recording' || uiState === 'paused') {
    const isMeetingBot = recordingMode === 'meeting-bot';
    const panelColor = isMeetingBot ? 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800/50' : 'bg-neutral-50 dark:bg-neutral-900/50 border-neutral-200 dark:border-neutral-700/50';
    
    return (
      <div className="flex items-center gap-2">
        <div className={cn("flex items-center gap-2 border rounded-md px-3 py-1.5 animate-in fade-in duration-300", panelColor)}>
          {isMeetingBot ? (
            <Monitor className="h-4 w-4 text-green-600 dark:text-green-400" />
          ) : (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleMainButtonClick}
                    disabled={disabled}
                    className={cn("h-6 w-6 p-0 transition-colors", getMainButtonClass())}
                  >
                    {getMainButtonIcon()}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{getTooltipText()}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          
          <span className={cn("text-sm tabular-nums", isMeetingBot ? "text-green-700 dark:text-green-300" : "text-neutral-600 dark:text-neutral-400")}>
            {isMeetingBot ? getBotStatusText() : formatTime(recordingTime)}
          </span>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={stopRecording}
                  className="h-6 w-6 p-0 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                >
                  <Square className="h-3 w-3 fill-current" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Stop</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    );
  }

  // Idle state - single record button
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleMainButtonClick}
            disabled={disabled}
            className={cn("h-8 w-8 p-0 transition-colors", getMainButtonClass())}
          >
            {getMainButtonIcon()}
          </Button>
        </TooltipTrigger>
        <TooltipContent>{getTooltipText()}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
      );
  }; 