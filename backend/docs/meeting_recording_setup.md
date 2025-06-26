# Meeting Recording Feature Setup

## Overview
The meeting recording feature allows users to record up to 2 hours of audio during meetings and automatically transcribe them using OpenAI's Whisper API.

## System Requirements

### Frontend
- Modern web browser with WebRTC support (Chrome, Firefox, Safari, Edge)
- Microphone permissions must be granted

### Backend Dependencies
The following Python packages are required (already added to requirements.txt):
- `pydub>=0.25.1` - For audio file manipulation and chunking
- `openai>=1.72.0` - For Whisper API transcription

### System Dependencies
**Important**: The audio transcription tool requires FFmpeg to be installed on the system where the backend runs.

#### Installing FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

**Docker:**
If running in Docker, add this to your Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```

## Feature Components

### 1. Meeting Recorder Component
- Location: `frontend/src/components/thread/chat-input/meeting-recorder.tsx`
- Features:
  - Record up to 2 hours of audio
  - Pause/resume functionality
  - Visual timer display
  - Accept/delete options when stopped

### 2. Audio Transcription Tool
- Location: `backend/agent/tools/audio_transcription_tool.py`
- Features:
  - Handles files up to 2 hours in length
  - Automatic chunking for files > 20MB (OpenAI limit is 25MB)
  - Intelligent chunk boundary detection
  - Context preservation between chunks
  - Saves transcript as text file

## Usage

1. **Recording**: Click the circle icon next to the send button to start recording
2. **Pause/Resume**: Click the pause/play icon during recording
3. **Stop**: Click the square icon to stop recording
4. **Accept**: Click the checkmark to attach the recording to your message
5. **Delete**: Click the X to discard the recording

When accepted, the system automatically adds:
- The audio file as an attachment
- A message requesting transcription with duration info
- The AI will use the `transcribe_audio` tool to process the file

## Technical Details

### Audio Format
- Recording format: WebM (audio/webm)
- Supported formats for transcription: mp3, mp4, mpeg, mpga, wav, webm, m4a

### File Size Handling
- Files under 20MB: Direct transcription
- Files over 20MB: Automatically chunked into 10-minute segments
- Each chunk includes context from the previous chunk for continuity

### Transcription Model
- Uses OpenAI's `gpt-4o-mini-transcribe` model
- Supports multiple languages (auto-detection or manual specification)
- Context prompts can be provided for better accuracy

## Troubleshooting

### "ffmpeg not found" error
- Ensure FFmpeg is installed and in the system PATH
- Restart the backend service after installation

### Large file transcription fails
- Check available disk space for temporary files
- Ensure the audio file is not corrupted
- Monitor backend logs for specific error messages

### Poor transcription quality
- Ensure good audio quality during recording
- Use a headset or external microphone if possible
- Minimize background noise
- Consider providing a context prompt for domain-specific terminology 