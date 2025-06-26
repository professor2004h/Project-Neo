import React, { useState, useRef, useEffect } from 'react';
import { Circle, Pause, Play, Check, X, Square } from 'lucide-react';
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
  const [state, setState] = useState<'idle' | 'recording' | 'paused' | 'stopped'>('idle');
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const systemStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);
  const pausedDurationRef = useRef<number>(0);
  const pauseStartTimeRef = useRef<number | null>(null);
  const timerIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const maxTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Update recording time
  useEffect(() => {
    if (state === 'recording') {
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
  }, [state]);

  // Auto-stop after 2 hours
  useEffect(() => {
    if (state === 'recording') {
      const remainingTime = MAX_RECORDING_TIME - recordingTime;
      if (remainingTime > 0) {
        maxTimeoutRef.current = setTimeout(() => {
          console.log('Auto-stopping recording after 2 hours');
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
  }, [state, recordingTime]);

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

  const startRecording = async () => {
    try {
      // Try to get both microphone and system audio
      const combinedStream = await getCombinedAudioStream();
      streamRef.current = combinedStream;

      const options = { mimeType: 'audio/webm' };
      const mediaRecorder = new MediaRecorder(combinedStream, options);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        if (chunksRef.current.length > 0) {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
          setAudioBlob(blob);
        }
        cleanupStream();
      };

      mediaRecorder.start(1000); // Collect data every second
      recordingStartTimeRef.current = Date.now();
      pausedDurationRef.current = 0;
      setState('recording');
    } catch (error) {
      console.error('Error starting recording:', error);
      setState('idle');
    }
  };

  const getCombinedAudioStream = async (): Promise<MediaStream> => {
    try {
      // Get microphone stream
      const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = micStream;

      // Try to get system audio (will prompt user)
      let systemStream: MediaStream | null = null;
      try {
        systemStream = await navigator.mediaDevices.getDisplayMedia({ 
          audio: true, 
          video: false 
        });
        systemStreamRef.current = systemStream;
      } catch (systemError) {
        console.log('System audio not available, using microphone only:', systemError);
      }

      // If we have both streams, mix them; otherwise just use microphone
      if (systemStream) {
        return mixAudioStreams(micStream, systemStream);
      } else {
        return micStream;
      }
    } catch (error) {
      console.error('Error getting audio streams:', error);
      throw error;
    }
  };

  const mixAudioStreams = (micStream: MediaStream, systemStream: MediaStream): MediaStream => {
    try {
      // Create audio context
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;

      // Create sources from streams
      const micSource = audioContext.createMediaStreamSource(micStream);
      const systemSource = audioContext.createMediaStreamSource(systemStream);

      // Create a destination for mixing
      const destination = audioContext.createMediaStreamDestination();

      // Connect both sources to the destination
      micSource.connect(destination);
      systemSource.connect(destination);

      return destination.stream;
    } catch (error) {
      console.error('Error mixing audio streams, falling back to microphone only:', error);
      // Fallback to microphone only if mixing fails
      return micStream;
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.pause();
      pauseStartTimeRef.current = Date.now();
      setState('paused');
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && state === 'paused' && pauseStartTimeRef.current) {
      pausedDurationRef.current += Date.now() - pauseStartTimeRef.current;
      pauseStartTimeRef.current = null;
      mediaRecorderRef.current.resume();
      setState('recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && (state === 'recording' || state === 'paused')) {
      setState('stopped');
      mediaRecorderRef.current.stop();
    }
  };

  const acceptRecording = async () => {
    if (audioBlob) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = normalizeFilenameToNFC(`meeting-recording-${timestamp}.webm`);
      const file = new File([audioBlob], filename, { type: 'audio/webm' });
      
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
    setState('idle');
    setRecordingTime(0);
    recordingStartTimeRef.current = null;
    pausedDurationRef.current = 0;
    pauseStartTimeRef.current = null;
    chunksRef.current = [];
  };

  const cleanupStream = () => {
    // Stop all tracks from the main combined stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Stop microphone stream
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(track => track.stop());
      micStreamRef.current = null;
    }

    // Stop system audio stream
    if (systemStreamRef.current) {
      systemStreamRef.current.getTracks().forEach(track => track.stop());
      systemStreamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }
  };

  const handleMainButtonClick = () => {
    switch (state) {
      case 'idle':
        startRecording();
        break;
      case 'recording':
        pauseRecording();
        break;
      case 'paused':
        resumeRecording();
        break;
    }
  };

  const getMainButtonIcon = () => {
    switch (state) {
      case 'idle':
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
    switch (state) {
      case 'recording':
        return 'text-yellow-500 hover:text-yellow-600 animate-pulse';
      case 'paused':
        return 'text-orange-500 hover:text-orange-600';
      default:
        return 'text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-neutral-100';
    }
  };

  if (state === 'stopped') {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          Recording complete ({formatTime(recordingTime)})
        </span>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={acceptRecording}
                className="h-8 w-8 p-0 text-green-500 hover:text-green-600"
              >
                <Check className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Accept recording</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={deleteRecording}
                className="h-8 w-8 p-0 text-red-500 hover:text-red-600"
              >
                <X className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Delete recording</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
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
          <TooltipContent>
            {state === 'idle' && 'Start meeting recording - captures microphone & system audio (up to 2 hours)'}
            {state === 'recording' && 'Pause recording'}
            {state === 'paused' && 'Resume recording'}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {state !== 'idle' && (
        <>
          <span className="text-sm tabular-nums text-muted-foreground">
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
                  className="h-8 w-8 p-0 text-red-500 hover:text-red-600 hover:scale-110 transition-transform"
                >
                  <Square className="h-4 w-4 fill-current" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Stop recording</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </>
      )}
    </div>
  );
}; 