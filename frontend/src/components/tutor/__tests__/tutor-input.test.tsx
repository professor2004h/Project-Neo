/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TutorInput } from '../tutor-input';

describe('TutorInput', () => {
  const defaultProps = {
    onSendMessage: jest.fn(),
    disabled: false,
    placeholder: 'Type your message...',
    supportVoice: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock console.log to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders input field correctly', () => {
    render(<TutorInput {...defaultProps} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    expect(textarea).toBeInTheDocument();
    expect(textarea).not.toBeDisabled();
  });

  it('renders send button', () => {
    render(<TutorInput {...defaultProps} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeInTheDocument();
  });

  it('renders voice button when voice is supported', () => {
    render(<TutorInput {...defaultProps} supportVoice={true} />);
    
    const voiceButton = screen.getByRole('button', { name: /start voice recording/i });
    expect(voiceButton).toBeInTheDocument();
  });

  it('does not render voice button when voice is not supported', () => {
    render(<TutorInput {...defaultProps} supportVoice={false} />);
    
    const voiceButton = screen.queryByRole('button', { name: /start voice recording/i });
    expect(voiceButton).not.toBeInTheDocument();
  });

  it('renders additional action buttons', () => {
    render(<TutorInput {...defaultProps} />);
    
    // Should have image upload and file attach buttons
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(2); // Send + Voice + Image + File
  });

  it('sends message on form submit', async () => {
    const onSendMessage = jest.fn();
    render(<TutorInput {...defaultProps} onSendMessage={onSendMessage} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    const form = textarea.closest('form');
    
    fireEvent.change(textarea, { target: { value: 'Hello world' } });
    fireEvent.submit(form!);
    
    expect(onSendMessage).toHaveBeenCalledWith('Hello world');
  });

  it('sends message on Enter key press', async () => {
    const onSendMessage = jest.fn();
    render(<TutorInput {...defaultProps} onSendMessage={onSendMessage} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    
    fireEvent.change(textarea, { target: { value: 'Hello world' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
    
    expect(onSendMessage).toHaveBeenCalledWith('Hello world');
  });

  it('does not send message on Shift+Enter', async () => {
    const onSendMessage = jest.fn();
    render(<TutorInput {...defaultProps} onSendMessage={onSendMessage} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    
    fireEvent.change(textarea, { target: { value: 'Hello world' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: true });
    
    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it('clears input after sending message', async () => {
    const onSendMessage = jest.fn();
    render(<TutorInput {...defaultProps} onSendMessage={onSendMessage} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    
    fireEvent.change(textarea, { target: { value: 'Hello world' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
    
    expect(textarea).toHaveValue('');
  });

  it('disables input when disabled prop is true', () => {
    render(<TutorInput {...defaultProps} disabled={true} />);
    
    const textarea = screen.getByPlaceholderText('Please wait...');
    expect(textarea).toBeDisabled();
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
  });

  it('disables send button when message is empty', () => {
    render(<TutorInput {...defaultProps} />);
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when message has content', () => {
    render(<TutorInput {...defaultProps} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send message/i });
    
    fireEvent.change(textarea, { target: { value: 'Hello' } });
    
    expect(sendButton).not.toBeDisabled();
  });

  it('does not send empty or whitespace-only messages', () => {
    const onSendMessage = jest.fn();
    render(<TutorInput {...defaultProps} onSendMessage={onSendMessage} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    
    // Try to send empty message
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
    expect(onSendMessage).not.toHaveBeenCalled();
    
    // Try to send whitespace-only message
    fireEvent.change(textarea, { target: { value: '   ' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it('handles voice recording toggle', () => {
    render(<TutorInput {...defaultProps} supportVoice={true} />);
    
    const voiceButton = screen.getByRole('button', { name: /start voice recording/i });
    
    // Start recording
    fireEvent.click(voiceButton);
    expect(console.log).toHaveBeenCalledWith('Starting voice recording');
    
    // Stop recording - button text should change
    const stopButton = screen.getByRole('button', { name: /stop recording/i });
    fireEvent.click(stopButton);
    expect(console.log).toHaveBeenCalledWith('Stopping voice recording');
  });

  it('shows recording indicator when recording', () => {
    render(<TutorInput {...defaultProps} supportVoice={true} />);
    
    const voiceButton = screen.getByRole('button', { name: /start voice recording/i });
    
    // Start recording
    fireEvent.click(voiceButton);
    
    expect(screen.getByText(/Recording\.\.\./)).toBeInTheDocument();
  });

  it('handles quick action buttons', () => {
    const onSendMessage = jest.fn();
    render(<TutorInput {...defaultProps} onSendMessage={onSendMessage} />);
    
    const helpButton = screen.getByText('Help with homework');
    fireEvent.click(helpButton);
    
    expect(onSendMessage).toHaveBeenCalledWith('I need help with my homework');
  });

  it('auto-resizes textarea', () => {
    render(<TutorInput {...defaultProps} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    
    // Simulate typing a long message
    const longMessage = 'This is a very long message that should cause the textarea to expand in height to accommodate the content without requiring scrolling.';
    
    fireEvent.change(textarea, { target: { value: longMessage } });
    
    // The textarea should have auto-resize behavior
    expect(textarea).toHaveValue(longMessage);
  });

  it('shows character count for long messages', () => {
    render(<TutorInput {...defaultProps} />);
    
    const textarea = screen.getByPlaceholderText('Type your message...');
    const longMessage = 'a'.repeat(150); // More than 100 characters
    
    fireEvent.change(textarea, { target: { value: longMessage } });
    
    expect(screen.getByText('150/500')).toBeInTheDocument();
  });

  it('handles image upload button click', () => {
    render(<TutorInput {...defaultProps} />);
    
    const imageButton = screen.getByRole('button', { name: /upload image/i });
    fireEvent.click(imageButton);
    
    expect(console.log).toHaveBeenCalledWith('Image upload clicked');
  });

  it('handles file attach button click', () => {
    render(<TutorInput {...defaultProps} />);
    
    const fileButton = screen.getByRole('button', { name: /attach file/i });
    fireEvent.click(fileButton);
    
    expect(console.log).toHaveBeenCalledWith('File attach clicked');
  });
});