'use client';

import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ChatInputProps } from './types';
import { cn } from '@/lib/utils';
import { Send, Mic, MicOff, Image as ImageIcon, Paperclip } from 'lucide-react';

export function TutorInput({ 
  onSendMessage, 
  disabled = false, 
  placeholder = "Type your message...",
  supportVoice = false 
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };

  const handleVoiceToggle = () => {
    if (!supportVoice) return;
    
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      // In a real implementation, this would stop the recording and process the audio
      console.log('Stopping voice recording');
    } else {
      // Start recording
      setIsRecording(true);
      // In a real implementation, this would start voice recording
      console.log('Starting voice recording');
    }
  };

  const handleImageUpload = () => {
    // In a real implementation, this would open a file picker for images
    console.log('Image upload clicked');
  };

  const handleFileAttach = () => {
    // In a real implementation, this would open a file picker
    console.log('File attach clicked');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {/* Main Input Area */}
      <div className="flex gap-2 items-end">
        {/* Text Input */}
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "Please wait..." : placeholder}
            disabled={disabled}
            className={cn(
              "min-h-[44px] max-h-[120px] resize-none pr-12",
              "focus:ring-2 focus:ring-primary/20"
            )}
            rows={1}
          />
          
          {/* Character count for longer messages */}
          {message.length > 100 && (
            <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
              {message.length}/500
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-1">
          {/* Voice Recording Button */}
          {supportVoice && (
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={handleVoiceToggle}
              disabled={disabled}
              aria-label={isRecording ? "Stop recording" : "Start voice recording"}
              className={cn(
                "shrink-0",
                isRecording && "bg-red-500 text-white hover:bg-red-600"
              )}
            >
              {isRecording ? (
                <MicOff className="w-4 h-4" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
            </Button>
          )}

          {/* Image Upload Button */}
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={handleImageUpload}
            disabled={disabled}
            aria-label="Upload image"
            className="shrink-0"
          >
            <ImageIcon className="w-4 h-4" />
          </Button>

          {/* File Attach Button */}
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={handleFileAttach}
            disabled={disabled}
            aria-label="Attach file"
            className="shrink-0"
          >
            <Paperclip className="w-4 h-4" />
          </Button>

          {/* Send Button */}
          <Button
            type="submit"
            disabled={disabled || !message.trim()}
            aria-label="Send message"
            className="shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Voice Recording Indicator */}
      {isRecording && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 dark:bg-red-950/20 p-2 rounded-lg">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
          <span>Recording... Click the microphone to stop</span>
        </div>
      )}

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onSendMessage("I need help with my homework")}
          disabled={disabled}
          className="text-xs"
        >
          Help with homework
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onSendMessage("Explain this concept to me")}
          disabled={disabled}
          className="text-xs"
        >
          Explain concept
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onSendMessage("Give me practice problems")}
          disabled={disabled}
          className="text-xs"
        >
          Practice problems
        </Button>
      </div>
    </form>
  );
}