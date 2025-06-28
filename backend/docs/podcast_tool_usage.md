# Podcast Generation Tool

The Podcast Generation Tool integrates with the [podcastfy library](https://github.com/souzatharsis/podcastfy) to create AI-powered podcasts from various content sources.

## Features

- **Multi-source content support**: Generate podcasts from URLs, local files, and images
- **Flexible file format support**: PDFs, text files, markdown, images (JPG, PNG)
- **Customizable conversation styles**: Educational, casual, analytical, storytelling, etc.
- **Multiple podcast lengths**: Short (2-5 min), medium (10-15 min), long (20-30 min)
- **Multi-language support**: Generate podcasts in various languages
- **TTS model options**: OpenAI (default) or ElevenLabs for higher quality
- **Transcript-only mode**: Review content before audio generation
- **Sandbox integration**: All files are processed and saved within the sandbox

## Usage Examples

### Basic URL Podcast
```python
# Generate a podcast from web articles
await generate_podcast(
    urls=["https://example.com/article1", "https://example.com/article2"],
    output_name="my_news_podcast",
    conversation_style=["engaging", "educational"]
)
```

### Local Files Podcast
```python
# Generate podcast from files in the sandbox
await generate_podcast(
    file_paths=["documents/research.pdf", "notes/summary.txt"],
    podcast_length="long",
    language="English"
)
```

### Image-based Podcast
```python
# Generate podcast from images (charts, infographics, etc.)
await generate_podcast(
    image_paths=["charts/sales_data.png", "images/diagram.jpg"],
    conversation_style=["analytical", "educational"]
)
```

### Mixed Content Podcast
```python
# Combine multiple content types
await generate_podcast(
    urls=["https://research.example.com/paper"],
    file_paths=["local_analysis.pdf"],
    image_paths=["chart.png"],
    output_name="comprehensive_analysis",
    podcast_length="medium",
    tts_model="elevenlabs"
)
```

### Transcript Only
```python
# Generate only transcript for review
await generate_podcast(
    urls=["https://example.com/content"],
    transcript_only=True
)
```

## Parameters

### Content Sources (at least one required)
- `urls`: List of website URLs to include
- `file_paths`: List of local file paths in sandbox (relative to /workspace)
- `image_paths`: List of image file paths in sandbox

### Customization Options
- `output_name`: Custom name for generated files (default: timestamp-based)
- `conversation_style`: List of styles - "engaging", "educational", "casual", "formal", "analytical", "storytelling", "interview", "debate"
- `podcast_length`: "short", "medium", or "long"
- `language`: Target language for the podcast (default: "English")
- `tts_model`: "openai" (default) or "elevenlabs"
- `transcript_only`: Generate only transcript without audio (default: False)

## Output

Generated podcasts are saved in the `/workspace/podcasts/` directory with:
- Audio file: `{output_name}.mp3`
- Transcript file: `{output_name}_transcript.txt`

Use the `list_podcasts` function to view all generated podcasts with their details.

## API Key Requirements

- **OpenAI**: Required for transcript generation and default TTS
- **ElevenLabs**: Optional, for higher quality TTS (set `tts_model="elevenlabs"`)

Configure API keys in your environment variables or config files.

## Supported File Formats

### Documents
- PDF files (.pdf)
- Text files (.txt)
- Markdown files (.md)
- Rich text format (.rtf)

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

### URLs
- News articles
- Blog posts
- Research papers
- Documentation pages
- Any web content with readable text

## Error Handling

The tool includes comprehensive error handling for:
- Missing dependencies (auto-installs podcastfy)
- Invalid file paths
- Network connectivity issues
- API rate limits
- File format incompatibilities

## Performance Notes

- Podcast generation time varies based on content length and TTS model
- ElevenLabs TTS provides higher quality but takes longer
- Large files may require chunking for processing
- Generated audio files are typically 1-10 MB depending on length

## Troubleshooting

### Common Issues

1. **"Podcastfy library not available"**
   - Tool will attempt auto-installation
   - Ensure pip is available in the environment

2. **"File not found"**
   - Verify file paths are relative to /workspace
   - Use the files tool to check file existence

3. **"No content sources provided"**
   - Provide at least one of: urls, file_paths, or image_paths

4. **TTS generation fails**
   - Check API key configuration
   - Try switching TTS model
   - Verify network connectivity 