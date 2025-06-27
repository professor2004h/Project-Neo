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

type RecordingMode = 'screen-and-microphone' | 'microphone-only' | 'failed';

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

  const getDisplayAndMicrophoneStreams = async () => {
    console.log('[MEETING RECORDER] Starting unified recording setup...');
    
    // Get microphone stream first (this is always required)
    const microphoneStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      }
    });
    
    console.log('[MEETING RECORDER] Microphone access granted');
    
    // Now request screen/window sharing with audio
    try {
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
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
      });
      
      console.log('[MEETING RECORDER] Screen sharing access granted');
      
      // Extract what the user shared for display purposes
      const videoTrack = displayStream.getVideoTracks()[0];
      if (videoTrack) {
        const settings = videoTrack.getSettings();
        if (settings.displaySurface === 'browser') {
          setSharedSource('Browser Tab');
        } else if (settings.displaySurface === 'window') {
          setSharedSource('Application Window');
        } else if (settings.displaySurface === 'monitor') {
          setSharedSource('Screen');
        } else {
          setSharedSource('Display Surface');
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
        return {
          recordingStream: mixedStream,
          microphoneStream,
          displayStream,
          mode: 'screen-and-microphone' as RecordingMode
        };
      } else {
        console.log('[MEETING RECORDER] No display audio, using microphone only');
        // User shared screen/window but no audio available
        setSharedSource('');
        return {
          recordingStream: microphoneStream,
          microphoneStream,
          displayStream: null,
          mode: 'microphone-only' as RecordingMode
        };
      }
    } catch (displayError) {
      console.log('[MEETING RECORDER] Screen sharing declined or failed, using microphone only');
      // User declined screen sharing or it failed, just use microphone
      setSharedSource('');
      return {
        recordingStream: microphoneStream,
        microphoneStream,
        displayStream: null,
        mode: 'microphone-only' as RecordingMode
      };
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

  const startRecording = async () => {
    try {
      setState('recording'); // Set state early for UI feedback
      setRecordingMode('microphone-only'); // Default fallback
      setSharedSource('');
      
      console.log('[MEETING RECORDER] Starting recording...');
      
      // Get streams using unified approach
      const { recordingStream, microphoneStream, displayStream, mode } = await getDisplayAndMicrophoneStreams();
      
      // Store streams for cleanup
      streamsRef.current.microphone = microphoneStream;
      streamsRef.current.display = displayStream;
      streamsRef.current.mixed = recordingStream;
      
      setRecordingMode(mode);

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
      setRecordingMode('failed');
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
      return 'Start meeting recording - choose what to share (screen, window, or tab) + microphone (up to 2 hours)';
    } else if (state === 'recording') {
      if (recordingMode === 'screen-and-microphone') {
        const sourceText = sharedSource ? ` from ${sharedSource}` : '';
        return `Recording audio${sourceText} + microphone - Click to pause`;
      } else {
        return 'Recording microphone only - Click to pause';
      }
    } else if (state === 'paused') {
      return 'Resume recording';
    }
    return '';
  };

  if (state === 'stopped') {
    const modeIndicator = recordingMode === 'screen-and-microphone' 
      ? ` (${sharedSource} + mic)` 
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
          {recordingMode === 'screen-and-microphone' && state === 'recording' && (
            <span className="text-xs text-green-600 font-medium">
              {sharedSource ? sharedSource.toUpperCase().replace(' ', '+') : 'SHARED'}+MIC
            </span>
          )}
          {recordingMode === 'microphone-only' && state === 'recording' && (
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