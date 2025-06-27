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

type AudioCaptureMode = 'microphone-only' | 'system-and-microphone' | 'failed';

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
  const [audioCaptureMode, setAudioCaptureMode] = useState<AudioCaptureMode>('microphone-only');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamsRef = useRef<{
    combined?: MediaStream;
    microphone?: MediaStream;
    system?: MediaStream;
  }>({});
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

  const attemptSystemAudioCapture = async (): Promise<MediaStream | null> => {
    try {
      console.log('[MEETING RECORDER] Attempting system audio capture...');
      
      // Request display media with audio for system audio capture
      // This only works reliably on Chrome/Edge and has platform limitations
      const displayStream = await navigator.mediaDevices.getDisplayMedia({ 
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
        video: {
          width: 1,
          height: 1,
          frameRate: 1
        }
      });
      
      // Extract audio tracks and discard video immediately
      const audioTracks = displayStream.getAudioTracks();
      const videoTracks = displayStream.getVideoTracks();
      
      // Stop and remove video tracks immediately to save resources
      videoTracks.forEach(track => {
        track.stop();
        displayStream.removeTrack(track);
      });
      
      if (audioTracks.length > 0) {
        const systemAudioStream = new MediaStream(audioTracks);
        console.log('[MEETING RECORDER] System audio captured successfully');
        return systemAudioStream;
      } else {
        console.log('[MEETING RECORDER] No audio tracks in display stream');
        return null;
      }
    } catch (error) {
      console.log('[MEETING RECORDER] System audio capture failed:', error);
      return null;
    }
  };

  const getMicrophoneStream = async (): Promise<MediaStream> => {
    try {
      console.log('[MEETING RECORDER] Getting microphone stream...');
      const micStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      console.log('[MEETING RECORDER] Microphone captured successfully');
      return micStream;
    } catch (error) {
      console.error('[MEETING RECORDER] Microphone access failed:', error);
      throw error;
    }
  };

  const mixAudioStreams = (micStream: MediaStream, systemStream: MediaStream): MediaStream => {
    try {
      console.log('[MEETING RECORDER] Mixing audio streams...');
      
      // Create audio context for mixing
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;

      // Create sources from streams
      const micSource = audioContext.createMediaStreamSource(micStream);
      const systemSource = audioContext.createMediaStreamSource(systemStream);
      const destination = audioContext.createMediaStreamDestination();

      // Create gain nodes for volume control
      const micGain = audioContext.createGain();
      const systemGain = audioContext.createGain();
      
      // Set reasonable gain levels (can be adjusted)
      micGain.gain.value = 0.8; // Slightly lower microphone to avoid overpowering
      systemGain.gain.value = 0.7; // Lower system audio to balance

      // Connect the audio graph
      micSource.connect(micGain).connect(destination);
      systemSource.connect(systemGain).connect(destination);

      console.log('[MEETING RECORDER] Audio streams mixed successfully');
      return destination.stream;
    } catch (error) {
      console.error('[MEETING RECORDER] Error mixing audio streams:', error);
      throw error;
    }
  };

  const startRecording = async () => {
    try {
      setState('recording'); // Set state early for UI feedback
      setAudioCaptureMode('microphone-only'); // Default fallback
      
      console.log('[MEETING RECORDER] Starting recording...');
      
      // Always get microphone first (required)
      const microphoneStream = await getMicrophoneStream();
      streamsRef.current.microphone = microphoneStream;
      
      // Attempt to get system audio (optional)
      const systemStream = await attemptSystemAudioCapture();
      streamsRef.current.system = systemStream;
      
      // Determine recording stream and capture mode
      let recordingStream: MediaStream;
      
      if (systemStream) {
        try {
          // Mix both streams
          recordingStream = mixAudioStreams(microphoneStream, systemStream);
          streamsRef.current.combined = recordingStream;
          setAudioCaptureMode('system-and-microphone');
          console.log('[MEETING RECORDER] Recording with system audio + microphone');
        } catch (mixError) {
          console.warn('[MEETING RECORDER] Failed to mix streams, using microphone only:', mixError);
          recordingStream = microphoneStream;
          setAudioCaptureMode('microphone-only');
        }
      } else {
        recordingStream = microphoneStream;
        setAudioCaptureMode('microphone-only');
        console.log('[MEETING RECORDER] Recording with microphone only');
      }

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
        setState('idle');
        cleanupStreams();
      };

      // Start recording with 5 second time slices for better data structure
      mediaRecorder.start(5000);
      recordingStartTimeRef.current = Date.now();
      pausedDurationRef.current = 0;
      
      console.log('[MEETING RECORDER] Recording started successfully');
    } catch (error) {
      console.error('[MEETING RECORDER] Error starting recording:', error);
      setState('idle');
      setAudioCaptureMode('failed');
      cleanupStreams();
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.pause();
      pauseStartTimeRef.current = Date.now();
      setState('paused');
      console.log('[MEETING RECORDER] Recording paused');
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && state === 'paused' && pauseStartTimeRef.current) {
      pausedDurationRef.current += Date.now() - pauseStartTimeRef.current;
      pauseStartTimeRef.current = null;
      mediaRecorderRef.current.resume();
      setState('recording');
      console.log('[MEETING RECORDER] Recording resumed');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && (state === 'recording' || state === 'paused')) {
      setState('stopped');
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
    setState('idle');
    setRecordingTime(0);
    setAudioCaptureMode('microphone-only');
    recordingStartTimeRef.current = null;
    pausedDurationRef.current = 0;
    pauseStartTimeRef.current = null;
    chunksRef.current = [];
  };

  const cleanupStreams = () => {
    console.log('[MEETING RECORDER] Cleaning up streams...');
    
    // Stop all tracks in all streams
    const { combined, microphone, system } = streamsRef.current;
    
    [combined, microphone, system].forEach(stream => {
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

  const getTooltipText = () => {
    if (state === 'idle') {
      return 'Start meeting recording - attempts to capture system audio + microphone (up to 2 hours)';
    } else if (state === 'recording') {
      const modeText = audioCaptureMode === 'system-and-microphone' 
        ? 'Recording system audio + microphone'
        : 'Recording microphone only';
      return `${modeText} - Click to pause`;
    } else if (state === 'paused') {
      return 'Resume recording';
    }
    return '';
  };

  if (state === 'stopped') {
    const modeIndicator = audioCaptureMode === 'system-and-microphone' 
      ? ' (system + mic)' 
      : ' (microphone)';
      
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          Recording complete ({formatTime(recordingTime)}){modeIndicator}
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
          <TooltipContent>{getTooltipText()}</TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {state !== 'idle' && (
        <>
          <span className="text-sm tabular-nums text-muted-foreground">
            {formatTime(recordingTime)}
          </span>
          {audioCaptureMode === 'system-and-microphone' && state === 'recording' && (
            <span className="text-xs text-green-600 font-medium">SYS+MIC</span>
          )}
          {audioCaptureMode === 'microphone-only' && state === 'recording' && (
            <span className="text-xs text-blue-600 font-medium">MIC</span>
          )}
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