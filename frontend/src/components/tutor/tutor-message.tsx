'use client';

import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { TutorMessage as TutorMessageType } from './types';
import { cn } from '@/lib/utils';
import { Bot, User, Volume2, Image as ImageIcon } from 'lucide-react';
import { format } from 'date-fns';

interface TutorMessageProps {
  message: TutorMessageType;
  isOwn: boolean;
}

export function TutorMessage({ message, isOwn }: TutorMessageProps) {
  const formatTime = (timestamp: Date) => {
    return format(timestamp, 'HH:mm');
  };

  const getMessageIcon = () => {
    switch (message.type) {
      case 'voice':
        return <Volume2 className="w-4 h-4" />;
      case 'image':
        return <ImageIcon className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className={cn(
      "flex gap-3 max-w-[80%]",
      isOwn ? "ml-auto flex-row-reverse" : "mr-auto"
    )}>
      {/* Avatar */}
      <Avatar className="w-8 h-8 shrink-0">
        {isOwn ? (
          <>
            <AvatarFallback className="bg-primary text-primary-foreground">
              <User className="w-4 h-4" />
            </AvatarFallback>
          </>
        ) : (
          <>
            <AvatarImage src="/tutor-avatar.png" alt="AI Tutor" />
            <AvatarFallback className="bg-blue-500 text-white">
              <Bot className="w-4 h-4" />
            </AvatarFallback>
          </>
        )}
      </Avatar>

      {/* Message Content */}
      <div className={cn(
        "flex flex-col gap-1",
        isOwn ? "items-end" : "items-start"
      )}>
        {/* Message Bubble */}
        <Card className={cn(
          "max-w-full",
          isOwn 
            ? "bg-primary text-primary-foreground" 
            : "bg-muted"
        )}>
          <CardContent className="p-3">
            {/* Message Type Icon */}
            {message.type !== 'text' && (
              <div className="flex items-center gap-2 mb-2 text-xs opacity-70">
                {getMessageIcon()}
                <span className="capitalize">{message.type} message</span>
              </div>
            )}

            {/* Message Text */}
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.content}
            </div>

            {/* Metadata Badges */}
            {message.metadata && (
              <div className="flex flex-wrap gap-1 mt-2">
                {message.metadata.cambridge_code && (
                  <Badge 
                    variant="secondary" 
                    className={cn(
                      "text-xs",
                      isOwn ? "bg-primary-foreground/20 text-primary-foreground" : ""
                    )}
                  >
                    {message.metadata.cambridge_code}
                  </Badge>
                )}
                {message.metadata.topic_id && (
                  <Badge 
                    variant="outline" 
                    className={cn(
                      "text-xs",
                      isOwn ? "border-primary-foreground/20 text-primary-foreground" : ""
                    )}
                  >
                    Topic: {message.metadata.topic_id.replace(/_/g, ' ')}
                  </Badge>
                )}
                {message.metadata.difficulty_level && (
                  <Badge 
                    variant="outline" 
                    className={cn(
                      "text-xs",
                      isOwn ? "border-primary-foreground/20 text-primary-foreground" : ""
                    )}
                  >
                    Level {message.metadata.difficulty_level}
                  </Badge>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Timestamp */}
        <span className={cn(
          "text-xs text-muted-foreground px-1",
          isOwn ? "text-right" : "text-left"
        )}>
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}