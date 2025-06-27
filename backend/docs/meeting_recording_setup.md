# Meeting Recording Setup & Usage

The meeting recorder in Operator captures up to 2 hours of audio with intelligent dual-source capture and automatic transcription.

## How It Works

### Audio Capture Strategy
The meeting recorder uses a **graceful degradation approach** for maximum compatibility:

1. **Primary**: Attempts to capture both system audio and microphone
2. **Fallback**: Falls back to microphone-only if system audio fails
3. **Intelligent Mixing**: Uses Web Audio API to blend both sources when available

### System Audio Availability
System audio capture has **browser and platform limitations**:

- ✅ **Chrome/Edge**: Best support (Windows: full screen + tabs, macOS: tabs only)
- ❌ **Firefox**: Limited system audio support
- ❌ **Safari**: No system audio support
- ❌ **Mobile**: No system audio support

### Visual Indicators
- **SYS+MIC**: Green indicator = capturing system audio + microphone
- **MIC**: Blue indicator = microphone only
- **Pulse animation**: Red pulsing = actively recording
- **Orange color**: Paused state

## User Experience

### Recording Process
1. Click the record button (⭕)
2. **System audio prompt**: Grant screen share permission for system audio (optional)
3. **Microphone prompt**: Grant microphone permission (required)
4. Recording starts with best available audio sources
5. Visual indicator shows capture mode (SYS+MIC or MIC)

### User Controls
- **Record/Pause**: Click main button to record or pause
- **Resume**: Click play button when paused
- **Stop**: Click square button to stop recording
- **Accept**: Green checkmark to save recording
- **Delete**: Red X to discard recording

## Browser Permissions

### First Time Setup
1. **Microphone**: Always required - grant when prompted
2. **Screen Share**: Optional for system audio - choose:
   - **Tab**: Captures audio from specific browser tab
   - **Window**: Captures audio from specific application
   - **Screen**: Captures all system audio (Chrome/Edge only)

### Permission Tips
- **macOS Users**: May need to grant "Screen Recording" permission in System Preferences
- **Corporate Networks**: Some policies may block screen capture
- **Privacy**: System audio capture only works with user's explicit permission

## Technical Specifications

### Audio Quality
- **Format**: WebM with Opus codec (fallback to MP4 when needed)
- **Bitrate**: 64kbps (optimized for speech/meetings)
- **Channels**: Mixed to mono for efficient processing
- **Gain Control**: Microphone (80%) + System Audio (70%) balanced mix

### Recording Limits
- **Duration**: 2 hours maximum (auto-stops)
- **File Size**: Approximately 55MB for 2-hour recording
- **Chunks**: 5-second segments for better file structure

### Dependencies for Transcription
If using the audio transcription tool, ensure FFmpeg is available:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Troubleshooting

### Common Issues

**"No system audio captured"**
- Expected behavior on Firefox/Safari
- Check browser compatibility above
- Grant screen share permission when prompted

**"Microphone access denied"**
- Check browser permissions in address bar
- Reload page and try again
- Verify microphone isn't used by other applications

**"Recording failed to start"**
- Ensure you're on HTTPS or localhost
- Check if other applications are using microphone
- Try refreshing the page

**"macOS permission issues"**
- Go to System Preferences > Security & Privacy > Privacy
- Enable "Screen Recording" for your browser
- Restart browser after enabling

### Quality Issues
- **Low system audio**: Increase computer volume before recording
- **Echo/feedback**: Use headphones during recording
- **Background noise**: Record in quiet environment

## Best Practices

### For Best Audio Quality
1. **Use headphones** to prevent feedback
2. **Close unnecessary applications** that might capture audio
3. **Test recording** for a few seconds first
4. **Record in quiet environment** when possible

### For System Audio Capture
1. **Use Chrome or Edge** for best compatibility
2. **Select appropriate source** when prompted:
   - Browser tab for meeting audio
   - Full screen for system-wide capture
3. **Grant permissions** when prompted
4. **Check volume levels** before starting

### File Management
- Recordings auto-upload after acceptance
- Large files may take time to process
- Transcription happens automatically when tool is enabled
- Files are saved with timestamp for easy identification

## Privacy & Security

- **Local processing**: Audio mixing happens in browser
- **User control**: System audio requires explicit permission
- **No background recording**: Only active during user session
- **Clear indicators**: Always shows when recording is active
- **Secure transmission**: Files uploaded over HTTPS only 