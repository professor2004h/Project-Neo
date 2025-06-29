# Podcast Tool API Setup

The podcast tool has been updated to use the Podcastfy REST API instead of the local library. This eliminates dependency conflicts and provides a more reliable service.

## Required Environment Variables

Add these environment variables to your `.env` file:

```bash
# Podcastfy API Configuration
PODCASTFY_API_URL=https://thatupiso-podcastfy-ai-demo.hf.space
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# LLM API Keys (at least one is required)
OPENAI_API_KEY=your_openai_api_key_here  # Usually already configured
GEMINI_API_KEY=your_gemini_api_key_here   # Alternative to OpenAI

# LLM Preference (optional)
PODCAST_PREFERRED_LLM=openai  # Options: 'openai' or 'gemini' (default: openai)
```

## API Key Setup

### 1. ElevenLabs API Key (Required)
1. Go to [ElevenLabs](https://elevenlabs.io/)
2. Sign up for an account
3. Go to your profile settings
4. Copy your API key
5. Add it to your `.env` file as `ELEVENLABS_API_KEY`

### 2. OpenAI API Key (Required if not using Gemini)
1. Go to [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file as `OPENAI_API_KEY`

### 3. Gemini API Key (Alternative to OpenAI)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY`

## Docker Container Setup for Podcastfy API

If you want to run your own instance of the Podcastfy API instead of using the public one:

### Option 1: Use the Official Podcastfy Docker Container

```bash
# Clone the repository
git clone https://github.com/souzatharsis/podcastfy.git
cd podcastfy

# Build the API container
docker build -f Dockerfile_api -t podcastfy-api .

# Run the container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_openai_key \
  -e ELEVENLABS_API_KEY=your_elevenlabs_key \
  -e GEMINI_API_KEY=your_gemini_key \
  podcastfy-api
```

### Option 2: Deploy on Render

1. Fork the [podcastfy repository](https://github.com/souzatharsis/podcastfy)
2. Connect it to Render as a web service
3. Use `Dockerfile_api` as the build configuration
4. Set the environment variables in Render:
   - `OPENAI_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `GEMINI_API_KEY`
5. Update your `PODCASTFY_API_URL` to point to your Render deployment

### Option 3: Deploy on Other Platforms

The podcastfy API can be deployed on any platform that supports Docker containers:
- Google Cloud Run
- AWS ECS/Fargate
- Azure Container Instances
- Railway
- Fly.io

## Usage

Once configured, the podcast tool will automatically use the API. No code changes are needed in your agent interactions.

Example usage:
```python
# This will now use the API instead of the local library
result = await podcast_tool.generate_podcast(
    urls=["https://example.com/article"],
    podcast_name="My Podcast",
    conversation_style=["engaging", "educational"]
)
```

## Troubleshooting

### Common Issues

1. **API timeout**: The API can take 1-3 minutes to generate podcasts. The tool automatically polls for completion.

2. **Invalid API keys**: Make sure all required API keys are correctly set in your environment.

3. **API URL not accessible**: Verify that the `PODCASTFY_API_URL` is correct and accessible from your deployment environment.

4. **Rate limits**: Be aware of rate limits for the underlying services (ElevenLabs, OpenAI, etc.).

5. **Gemini quota exceeded**: If you see "429 You exceeded your current quota" for Gemini, set `PODCAST_PREFERRED_LLM=openai` to use OpenAI instead.

### API Response Format

The API returns a file download URL in this format:
```json
{
  "path": "/tmp/gradio/..../podcast_xyz.mp3",
  "url": "https://api-url/gradio_api/file=/tmp/gradio/.../podcast_xyz.mp3",
  "orig_name": "podcast_xyz.mp3"
}
```

The tool automatically downloads the file and saves it to the sandbox workspace.

## Benefits of API Approach

1. **No dependency conflicts**: Eliminates issues with podcastfy library dependencies
2. **Consistent environment**: Same API works across all deployments
3. **Scalability**: External service handles the heavy lifting
4. **Reliability**: Well-maintained API endpoint
5. **Latest features**: Always uses the latest version of podcastfy

## Security Notes

- API keys are sensitive - never commit them to version control
- Use environment variables or secure secret management
- Consider using your own deployment for production workloads
- Monitor API usage and costs for external services 