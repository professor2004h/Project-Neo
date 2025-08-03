'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TutorMessage } from './tutor-message';
import { TutorInput } from './tutor-input';
import { TutorSession, TutorMessage as TutorMessageType } from './types';
import { cn } from '@/lib/utils';

interface TutorChatProps {
  session: TutorSession;
  onSessionUpdate: (session: TutorSession) => void;
  onSessionEnd: () => void;
}

export function TutorChat({ session, onSessionUpdate, onSessionEnd }: TutorChatProps) {
  const [isTyping, setIsTyping] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session.messages]);

  // Send initial greeting if no messages
  useEffect(() => {
    if (session.messages.length === 0) {
      const greetingMessage: TutorMessageType = {
        id: `msg_${Date.now()}`,
        content: `Hello! I'm your Cambridge AI Tutor for ${session.context.subject?.toUpperCase()}. I'm here to help you learn and practice. What would you like to work on today?`,
        sender: 'tutor',
        timestamp: new Date(),
        type: 'text',
        metadata: {
          difficulty_level: session.context.grade_level || 1
        }
      };

      const updatedSession = {
        ...session,
        messages: [greetingMessage]
      };
      
      onSessionUpdate(updatedSession);
    }
  }, [session, onSessionUpdate]);

  const handleSendMessage = async (content: string, type: 'text' | 'voice' = 'text') => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: TutorMessageType = {
      id: `msg_${Date.now()}`,
      content: content.trim(),
      sender: 'user',
      timestamp: new Date(),
      type: type
    };

    const sessionWithUserMessage = {
      ...session,
      messages: [...session.messages, userMessage]
    };
    
    onSessionUpdate(sessionWithUserMessage);

    // Show typing indicator
    setIsTyping(true);

    try {
      // Simulate AI response (in real implementation, this would call the backend)
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

      const tutorResponse = await generateTutorResponse(content, session);
      
      const tutorMessage: TutorMessageType = {
        id: `msg_${Date.now() + 1}`,
        content: tutorResponse.content,
        sender: 'tutor',
        timestamp: new Date(),
        type: 'text',
        metadata: tutorResponse.metadata
      };

      const finalSession = {
        ...sessionWithUserMessage,
        messages: [...sessionWithUserMessage.messages, tutorMessage]
      };

      onSessionUpdate(finalSession);
    } catch (error) {
      console.error('Failed to get tutor response:', error);
      
      const errorMessage: TutorMessageType = {
        id: `msg_${Date.now() + 1}`,
        content: "I'm sorry, I'm having trouble responding right now. Please try again in a moment.",
        sender: 'tutor',
        timestamp: new Date(),
        type: 'text'
      };

      const errorSession = {
        ...sessionWithUserMessage,
        messages: [...sessionWithUserMessage.messages, errorMessage]
      };

      onSessionUpdate(errorSession);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        <div className="space-y-4">
          {session.messages.map((message) => (
            <TutorMessage
              key={message.id}
              message={message}
              isOwn={message.sender === 'user'}
            />
          ))}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex items-center space-x-2 text-muted-foreground">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
              </div>
              <span className="text-sm">Tutor is typing...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t p-4">
        <TutorInput
          onSendMessage={handleSendMessage}
          disabled={isTyping}
          placeholder="Ask me anything about your studies..."
          supportVoice={true}
        />
      </div>
    </div>
  );
}

// Mock function to generate tutor responses
async function generateTutorResponse(userMessage: string, session: TutorSession) {
  const subject = session.context.subject || 'math';
  const gradeLevel = session.context.grade_level || 1;
  
  // Simple response generation based on keywords
  const lowerMessage = userMessage.toLowerCase();
  
  let response = '';
  let metadata = {
    difficulty_level: gradeLevel,
    topic_id: undefined as string | undefined,
    cambridge_code: undefined as string | undefined
  };

  if (lowerMessage.includes('fraction')) {
    response = `Great question about fractions! Let me help you understand this step by step. 

A fraction represents a part of a whole. Think of it like a pizza 🍕 - if you cut it into 4 equal pieces and eat 1 piece, you've eaten 1/4 of the pizza.

The number on top (1) is called the numerator - it tells us how many pieces we have.
The number on bottom (4) is called the denominator - it tells us how many equal pieces the whole thing was divided into.

Would you like me to show you some examples or do you have a specific fraction problem you're working on?`;
    
    metadata.topic_id = 'fractions_basic';
    metadata.cambridge_code = 'M3N1.1';
  } else if (lowerMessage.includes('multiply') || lowerMessage.includes('times')) {
    response = `Multiplication is like adding the same number multiple times! 

For example, 3 × 4 means "3 groups of 4" or "4 + 4 + 4" = 12.

Here's a helpful tip: Start with the times tables you know well (like 2s, 5s, and 10s) and build from there. 

What multiplication problem are you working on? I can help you solve it step by step!`;
    
    metadata.topic_id = 'multiplication_tables';
    metadata.cambridge_code = 'M3N2.3';
  } else if (lowerMessage.includes('help') || lowerMessage.includes('stuck')) {
    response = `I'm here to help! Don't worry about feeling stuck - that's a normal part of learning. 

Can you tell me:
1. What subject are you working on?
2. What specific problem or concept is giving you trouble?
3. What part do you understand so far?

Once I know more, I can break it down into smaller, easier steps for you! 😊`;
  } else {
    response = `That's an interesting question! I want to make sure I give you the best help possible. 

Could you tell me a bit more about what you're studying? For example:
- Is this about math, science, or English?
- Are you working on homework or just curious about something?
- What grade level material is this?

The more you tell me, the better I can help you understand! 🎓`;
  }

  return {
    content: response,
    metadata
  };
}