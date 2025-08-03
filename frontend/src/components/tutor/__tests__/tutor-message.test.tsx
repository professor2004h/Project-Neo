/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TutorMessage } from '../tutor-message';
import { TutorMessage as TutorMessageType } from '../types';

describe('TutorMessage', () => {
  const baseMessage: TutorMessageType = {
    id: 'msg123',
    content: 'This is a test message',
    sender: 'user',
    timestamp: new Date('2024-01-01T12:00:00Z'),
    type: 'text'
  };

  it('renders user message correctly', () => {
    render(<TutorMessage message={baseMessage} isOwn={true} />);
    
    expect(screen.getByText('This is a test message')).toBeInTheDocument();
    // Use a more flexible approach for time checking due to timezone differences
    const timeElement = screen.getByText(/\d{2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });

  it('renders tutor message correctly', () => {
    const tutorMessage = { ...baseMessage, sender: 'tutor' as const };
    render(<TutorMessage message={tutorMessage} isOwn={false} />);
    
    expect(screen.getByText('This is a test message')).toBeInTheDocument();
    // Use a more flexible approach for time checking due to timezone differences
    const timeElement = screen.getByText(/\d{2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });

  it('displays correct avatar for user messages', () => {
    render(<TutorMessage message={baseMessage} isOwn={true} />);
    
    // User avatar should be present (using data-slot attribute)
    const avatar = document.querySelector('[data-slot="avatar"]');
    expect(avatar).toBeInTheDocument();
  });

  it('displays correct avatar for tutor messages', () => {
    const tutorMessage = { ...baseMessage, sender: 'tutor' as const };
    render(<TutorMessage message={tutorMessage} isOwn={false} />);
    
    // Tutor avatar should be present (using data-slot attribute)
    const avatar = document.querySelector('[data-slot="avatar"]');
    expect(avatar).toBeInTheDocument();
  });

  it('handles voice messages', () => {
    const voiceMessage = { ...baseMessage, type: 'voice' as const };
    render(<TutorMessage message={voiceMessage} isOwn={true} />);
    
    expect(screen.getByText('voice message')).toBeInTheDocument();
    expect(screen.getByText('This is a test message')).toBeInTheDocument();
  });

  it('handles image messages', () => {
    const imageMessage = { ...baseMessage, type: 'image' as const };
    render(<TutorMessage message={imageMessage} isOwn={true} />);
    
    expect(screen.getByText('image message')).toBeInTheDocument();
    expect(screen.getByText('This is a test message')).toBeInTheDocument();
  });

  it('displays metadata badges when present', () => {
    const messageWithMetadata = {
      ...baseMessage,
      metadata: {
        cambridge_code: 'M3N1.1',
        topic_id: 'fractions_basic',
        difficulty_level: 3
      }
    };
    
    render(<TutorMessage message={messageWithMetadata} isOwn={false} />);
    
    expect(screen.getByText('M3N1.1')).toBeInTheDocument();
    expect(screen.getByText('Topic: fractions basic')).toBeInTheDocument();
    expect(screen.getByText('Level 3')).toBeInTheDocument();
  });

  it('handles long messages correctly', () => {
    const longMessage = {
      ...baseMessage,
      content: 'This is a very long message that should wrap properly and maintain good readability even when it spans multiple lines. It should preserve whitespace and line breaks as needed.'
    };
    
    render(<TutorMessage message={longMessage} isOwn={true} />);
    
    expect(screen.getByText(longMessage.content)).toBeInTheDocument();
  });

  it('formats timestamp correctly', () => {
    const messageWithTime = {
      ...baseMessage,
      timestamp: new Date('2024-01-01T15:30:45Z')
    };
    
    render(<TutorMessage message={messageWithTime} isOwn={true} />);
    
    // Use a more flexible approach for time checking due to timezone differences
    const timeElement = screen.getByText(/\d{2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });

  it('applies correct styling for own messages', () => {
    const { container } = render(<TutorMessage message={baseMessage} isOwn={true} />);
    
    // Check for right-aligned styling
    const messageContainer = container.querySelector('[class*="ml-auto"]');
    expect(messageContainer).toBeInTheDocument();
  });

  it('applies correct styling for other messages', () => {
    const tutorMessage = { ...baseMessage, sender: 'tutor' as const };
    const { container } = render(<TutorMessage message={tutorMessage} isOwn={false} />);
    
    // Check for left-aligned styling
    const messageContainer = container.querySelector('[class*="mr-auto"]');
    expect(messageContainer).toBeInTheDocument();
  });

  it('handles messages without metadata gracefully', () => {
    const messageWithoutMetadata = {
      ...baseMessage,
      metadata: undefined
    };
    
    render(<TutorMessage message={messageWithoutMetadata} isOwn={true} />);
    
    expect(screen.getByText('This is a test message')).toBeInTheDocument();
    // Use flexible time matching
    const timeElement = screen.getByText(/\d{2}:\d{2}/);
    expect(timeElement).toBeInTheDocument();
  });

  it('preserves whitespace in message content', () => {
    const messageWithWhitespace = {
      ...baseMessage,
      content: 'Line 1\n\nLine 3 with  extra  spaces'
    };
    
    render(<TutorMessage message={messageWithWhitespace} isOwn={true} />);
    
    // Find the specific message content div with whitespace-pre-wrap class
    const messageContent = document.querySelector('.whitespace-pre-wrap');
    expect(messageContent).toBeInTheDocument();
    expect(messageContent).toHaveClass('whitespace-pre-wrap');
    expect(messageContent?.textContent).toContain('Line 1');
    expect(messageContent?.textContent).toContain('Line 3 with  extra  spaces');
  });
});