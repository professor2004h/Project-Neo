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
import { UploadedFile } from './chat-input';
import { normalizeFilenameToNFC } from '@/lib/utils/unicode';
import { handleFiles } from './file-upload-handler';
import { useQueryClient } from '@tanstack/react-query';

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

type RecordingMode = 'screen-and-microphone' | 'microphone-only' | 'failed';
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
  const [sharedSource, setSharedSource] = useState<string>('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamsRef = useRef<{
    mixed?: MediaStream;
    microphone?: MediaStream;
    display?: MediaStream;
  }>({});
  const audioContextRef = useRef<AudioContext | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);
  const pausedDurationRef = useRef<number>(0);
  const pauseStartTimeRef = useRef<number | null>(null);
  const timerIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const maxTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
      setSharedSource('');
      
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

  const startOnlineRecording = async () => {
    try {
      setUIState('recording');
      setRecordingMode('microphone-only'); // Default fallback
      setSharedSource('');
      
      console.log('[MEETING RECORDER] Starting online recording (screen share + microphone)...');
      
      // Request both permissions simultaneously to prevent browsers from stopping streams
      const mediaPromises = Promise.allSettled([
        navigator.mediaDevices.getDisplayMedia({
          video: {
            width: 1920,
            height: 1080,
            frameRate: 1, // Minimal video since we only want audio
          },
          audio: {
            echoCancellation: false, // Keep original audio quality
            noiseSuppression: false,
            autoGainControl: false,
          }
        }),
        navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          }
        })
      ]);
      
      const [displayResult, microphoneResult] = await mediaPromises;
      
      // Handle microphone stream (required)
      let microphoneStream: MediaStream;
      if (microphoneResult.status === 'fulfilled') {
        microphoneStream = microphoneResult.value;
        console.log('[MEETING RECORDER] Microphone access granted');
      } else {
        console.error('[MEETING RECORDER] Microphone access failed:', microphoneResult.reason);
        throw new Error('Microphone access required for recording');
      }
      
      // Handle display stream (optional)
      if (displayResult.status === 'fulfilled') {
        const displayStream = displayResult.value;
        console.log('[MEETING RECORDER] Screen sharing access granted');
        
        // Extract what the user shared for display purposes
        const videoTrack = displayStream.getVideoTracks()[0];
        if (videoTrack) {
          const settings = videoTrack.getSettings();
          if (settings.displaySurface === 'browser') {
            setSharedSource('tab');
          } else if (settings.displaySurface === 'window') {
            setSharedSource('window');
          } else if (settings.displaySurface === 'monitor') {
            setSharedSource('screen');
          } else {
            setSharedSource('display');
          }
        }
        
        // Stop video track immediately since we only need audio
        displayStream.getVideoTracks().forEach(track => {
          track.stop();
          displayStream.removeTrack(track);
        });
        
        const displayAudioTracks = displayStream.getAudioTracks();
        
        if (displayAudioTracks.length > 0) {
          console.log('[MEETING RECORDER] Display audio available, mixing with microphone');
          // We have both microphone and display audio
          const mixedStream = mixAudioStreams(microphoneStream, displayStream);
          
          // Store streams for cleanup
          streamsRef.current.microphone = microphoneStream;
          streamsRef.current.display = displayStream;
          streamsRef.current.mixed = mixedStream;
          
          setRecordingMode('screen-and-microphone');
          await startRecordingWithStream(mixedStream, 'screen-and-microphone');
        } else {
          console.log('[MEETING RECORDER] Screen shared but no audio available, using microphone only');
          // User shared screen/window but no audio available
          setSharedSource('');
          streamsRef.current.microphone = microphoneStream;
          setRecordingMode('microphone-only');
          await startRecordingWithStream(microphoneStream, 'microphone-only');
        }
      } else {
        console.log('[MEETING RECORDER] Screen sharing declined or failed:', displayResult.reason);
        console.log('[MEETING RECORDER] Using microphone only');
        
        // User declined screen sharing, just use microphone
        setSharedSource('');
        streamsRef.current.microphone = microphoneStream;
        setRecordingMode('microphone-only');
        await startRecordingWithStream(microphoneStream, 'microphone-only');
      }
      
    } catch (error) {
      console.error('[MEETING RECORDER] Error starting online recording:', error);
      setUIState('idle');
      setRecordingMode('failed');
      cleanupStreams();
    }
  };

  const mixAudioStreams = (micStream: MediaStream, displayStream: MediaStream): MediaStream => {
    try {
      console.log('[MEETING RECORDER] Mixing microphone and display audio...');
      
      // Create audio context for mixing
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;

      // Create sources from streams
      const micSource = audioContext.createMediaStreamSource(micStream);
      const displaySource = audioContext.createMediaStreamSource(displayStream);
      const destination = audioContext.createMediaStreamDestination();

      // Create gain nodes for volume control
      const micGain = audioContext.createGain();
      const displayGain = audioContext.createGain();
      
      // Balance levels - microphone prominent but display audible
      micGain.gain.value = 0.8;
      displayGain.gain.value = 0.6;

      // Connect the audio graph
      micSource.connect(micGain).connect(destination);
      displaySource.connect(displayGain).connect(destination);

      console.log('[MEETING RECORDER] Audio streams mixed successfully');
      return destination.stream;
    } catch (error) {
      console.error('[MEETING RECORDER] Error mixing audio streams:', error);
      throw error;
    }
  };

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

  const stopRecording = () => {
    if (mediaRecorderRef.current && (uiState === 'recording' || uiState === 'paused')) {
      setUIState('stopped');
      mediaRecorderRef.current.stop();
      console.log('[MEETING RECORDER] Recording stopped');
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
    setSharedSource('');
    recordingStartTimeRef.current = null;
    pausedDurationRef.current = 0;
    pauseStartTimeRef.current = null;
    chunksRef.current = [];
  };

  const cleanupStreams = () => {
    console.log('[MEETING RECORDER] Cleaning up streams...');
    
    // Stop all tracks in all streams
    const { mixed, microphone, display } = streamsRef.current;
    
    [mixed, microphone, display].forEach(stream => {
      if (stream) {
        stream.getTracks().forEach(track => {
          track.stop();
          console.log(`[MEETING RECORDER] Stopped ${track.kind} track`);
        });
      }
    });
    
    // Clear stream references
    streamsRef.current = {};

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }
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
        
        <TooltipProvider>
          <Tooltip>
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
            <TooltipContent>Online</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    );
  }

  // Subtle recording panel
  if (uiState === 'recording' || uiState === 'paused') {
    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-700/50 rounded-md px-3 py-1.5 animate-in fade-in duration-300">
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
          
          <span className="text-sm tabular-nums text-neutral-600 dark:text-neutral-400">
            {formatTime(recordingTime)}
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