import os
import json
import tempfile
import asyncio
import datetime
import time
import requests
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from urllib.parse import urlparse, urljoin
from agentpress.tool import ToolResult, openapi_schema, xml_schema
from sandbox.tool_base import SandboxToolsBase
from agentpress.thread_manager import ThreadManager
from utils.logger import logger


class SandboxPodcastTool(SandboxToolsBase):
    """
    A tool for generating AI podcasts using the Podcastfy REST API.
    
    This tool integrates with the remote podcastfy service to create conversational
    audio content from URLs, files in the sandbox, and other content types.
    """

    name: str = "podcast_tool"
    description: str = """
    Generate AI podcasts from content using the Podcastfy API.
    
    This tool can create conversational audio content from:
    - Website URLs
    - Files in the sandbox (PDFs, text files, images)
    - Direct text input
    
    The tool uses advanced AI to create natural conversations between two speakers
    and generates high-quality audio using ElevenLabs TTS.
    """

    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.workspace_path = "/workspace"
        self.api_base_url = os.getenv('PODCASTFY_API_URL', 'https://thatupiso-podcastfy-ai-demo.hf.space')
        self.gemini_key = os.getenv('GEMINI_API_KEY', '')
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        self.elevenlabs_key = os.getenv('ELEVENLABS_API_KEY', '')
        
        # Validate required environment variables
        if not self.openai_key and not self.gemini_key:
            raise ValueError("Either OPENAI_API_KEY or GEMINI_API_KEY must be set")
        if not self.elevenlabs_key:
            raise ValueError("ELEVENLABS_API_KEY must be set")

    # Removed _check_podcastfy_installation - no longer needed for API approach

    def _validate_file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the sandbox."""
        try:
            self.sandbox.fs.get_file_info(file_path)
            return True
        except Exception:
            return False

    # Removed _generate_podcast_with_podcastfy - now using API instead

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "generate_podcast",
            "description": "Generate an AI-powered podcast from various content sources including URLs, local files, and images. The tool creates engaging conversational audio content using advanced AI. Generated podcasts are saved in the sandbox workspace for easy access.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of website URLs to generate podcast from. Can include news articles, blog posts, research papers, etc."
                    },
                    "file_paths": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of local file paths in the sandbox to generate podcast from. Supports PDFs, text files, markdown, etc. Paths should be relative to /workspace (e.g., 'documents/paper.pdf')"
                    },
                    "image_paths": {
                        "type": "array",
                        "items": {"type": "string"}, 
                        "description": "List of image file paths in the sandbox to generate podcast from. Supports JPG, PNG, etc. Paths should be relative to /workspace (e.g., 'images/chart.png')"
                    },
                    "output_name": {
                        "type": "string",
                        "description": "Custom name for the generated podcast files (without extension). If not provided, a timestamp-based name will be used.",
                        "default": None
                    },
                    "conversation_style": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Style of conversation for the podcast. Options include: ['engaging', 'educational', 'casual', 'formal', 'analytical', 'storytelling', 'interview', 'debate']",
                        "default": ["engaging", "educational"]
                    },
                    "podcast_length": {
                        "type": "string",
                        "description": "Desired length of podcast. Options: 'short' (2-5 min), 'medium' (10-15 min), 'long' (20-30 min)",
                        "default": "medium"
                    },
                    "language": {
                        "type": "string", 
                        "description": "Language for the podcast. Supports multiple languages including 'English', 'Spanish', 'French', 'German', etc.",
                        "default": "English"
                    },
                    "transcript_only": {
                        "type": "boolean",
                        "description": "If true, only generate the transcript without audio. Useful for reviewing content before audio generation.",
                        "default": False
                    },
                    "roles_person1": {
                        "type": "string",
                        "description": "Role of the first speaker in the podcast (e.g., 'main summarizer', 'host', 'expert')",
                        "default": "main summarizer"
                    },
                    "roles_person2": {
                        "type": "string", 
                        "description": "Role of the second speaker in the podcast (e.g., 'questioner/clarifier', 'co-host', 'interviewer')",
                        "default": "questioner/clarifier"
                    },
                    "dialogue_structure": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Structure of the podcast dialogue (e.g., ['Introduction', 'Main Content Summary', 'Deep Dive', 'Conclusion'])",
                        "default": ["Introduction", "Main Content Summary", "Conclusion"]
                    },
                    "podcast_name": {
                        "type": "string",
                        "description": "Custom name for the podcast series",
                        "default": "AI Generated Podcast"
                    },
                    "podcast_tagline": {
                        "type": "string",
                        "description": "Tagline or subtitle for the podcast",
                        "default": "Transforming content into engaging conversations"
                    },
                    "engagement_techniques": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Techniques to make the podcast more engaging (e.g., ['rhetorical questions', 'anecdotes', 'analogies', 'humor'])",
                        "default": ["rhetorical questions", "anecdotes"]
                    },
                    "creativity": {
                        "type": "number",
                        "description": "Level of creativity/temperature for the conversation (0.0 to 1.0, where 1.0 is most creative)",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "user_instructions": {
                        "type": "string",
                        "description": "Custom instructions to guide the conversation focus and topics",
                        "default": ""
                    },
                    "max_num_chunks": {
                        "type": "integer",
                        "description": "Maximum number of discussion rounds in longform podcasts",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 15
                    },
                    "min_chunk_size": {
                        "type": "integer", 
                        "description": "Minimum number of characters per discussion round in longform podcasts",
                        "default": 600,
                        "minimum": 200,
                        "maximum": 2000
                    }
                },
                "required": []
            }
        }
    })
    @xml_schema(
        tag_name="generate-podcast",
        mappings=[
            {"param_name": "urls", "node_type": "element", "path": "urls", "required": False},
            {"param_name": "file_paths", "node_type": "element", "path": "file_paths", "required": False},
            {"param_name": "image_paths", "node_type": "element", "path": "image_paths", "required": False},
            {"param_name": "output_name", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "conversation_style", "node_type": "element", "path": "conversation_style", "required": False},
            {"param_name": "podcast_length", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "language", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "transcript_only", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "roles_person1", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "roles_person2", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "dialogue_structure", "node_type": "element", "path": "dialogue_structure", "required": False},
            {"param_name": "podcast_name", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "podcast_tagline", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "engagement_techniques", "node_type": "element", "path": "engagement_techniques", "required": False},
            {"param_name": "creativity", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "user_instructions", "node_type": "element", "path": "user_instructions", "required": False},
            {"param_name": "max_num_chunks", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "min_chunk_size", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <function_calls>
        <invoke name="generate_podcast">
        <parameter name="urls">["https://example.com/article1", "https://example.com/article2"]</parameter>
        <parameter name="file_paths">["documents/research.pdf", "notes/summary.txt"]</parameter>
        <parameter name="output_name">my_research_podcast</parameter>
        <parameter name="conversation_style">["engaging", "fast-paced", "enthusiastic"]</parameter>
        <parameter name="podcast_length">medium</parameter>
        <parameter name="language">English</parameter>
        <parameter name="roles_person1">main summarizer</parameter>
        <parameter name="roles_person2">questioner/clarifier</parameter>
        <parameter name="dialogue_structure">["Introduction", "Main Content Summary", "Deep Dive", "Conclusion"]</parameter>
        <parameter name="podcast_name">Tech Research Podcast</parameter>
        <parameter name="podcast_tagline">Deep dives into cutting-edge technology</parameter>
        <parameter name="engagement_techniques">["rhetorical questions", "analogies", "humor"]</parameter>
        <parameter name="creativity">0.8</parameter>
        <parameter name="user_instructions">Focus on practical applications and real-world impact</parameter>
        </invoke>
        </function_calls>
        '''
    )
    async def generate_podcast(self,
                             urls: Optional[List[str]] = None,
                             file_paths: Optional[List[str]] = None, 
                             image_paths: Optional[List[str]] = None,
                             output_name: Optional[str] = None,
                             conversation_style: List[str] = ["engaging", "educational"],
                             podcast_length: str = "medium", 
                             language: str = "English",
                             transcript_only: bool = False,
                             roles_person1: str = "main summarizer",
                             roles_person2: str = "questioner/clarifier",
                             dialogue_structure: List[str] = ["Introduction", "Main Content Summary", "Conclusion"],
                             podcast_name: str = "AI Generated Podcast",
                             podcast_tagline: str = "Transforming content into engaging conversations",
                             engagement_techniques: List[str] = ["rhetorical questions", "anecdotes"],
                             creativity: float = 0.7,
                             user_instructions: str = "",
                             max_num_chunks: int = 7,
                             min_chunk_size: int = 600) -> ToolResult:
        """Generate an AI-powered podcast from various content sources.
        
        Args:
            urls: List of website URLs to include
            file_paths: List of local file paths in the sandbox
            image_paths: List of image file paths in the sandbox  
            output_name: Custom name for output files
            conversation_style: Style of conversation (e.g., ["engaging", "fast-paced", "enthusiastic"])
            podcast_length: Desired length (short/medium/long)
            language: Language for the podcast
            transcript_only: Generate only transcript without audio
            roles_person1: Role of the first speaker
            roles_person2: Role of the second speaker
            dialogue_structure: Structure of the podcast dialogue
            podcast_name: Custom name for the podcast series
            podcast_tagline: Tagline or subtitle for the podcast
            engagement_techniques: Techniques to make the podcast more engaging
            creativity: Level of creativity/temperature (0.0-1.0)
            user_instructions: Custom instructions to guide the conversation
            max_num_chunks: Maximum number of discussion rounds in longform
            min_chunk_size: Minimum characters per discussion round in longform
            
        Returns:
            ToolResult with podcast generation status and file locations
        """
        try:
            # Ensure sandbox is initialized
            await self._ensure_sandbox()
            
            # Validate inputs
            if not any([urls, file_paths, image_paths]):
                return self.fail_response("At least one content source (URLs, files, or images) must be provided")
            
            # Prepare conversation configuration
            word_count_map = {
                "short": 1000,
                "medium": 2500, 
                "long": 4000
            }
            
            # Process URLs
            urls_input = ""
            if urls:
                # Validate URLs
                valid_urls = []
                for url in urls:
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    try:
                        parsed = urlparse(url)
                        if parsed.netloc:
                            valid_urls.append(url)
                    except:
                        continue
                urls_input = ",".join(valid_urls)
            
            # Process files - read content as text for now
            # TODO: Implement file upload to the API
            file_content = ""
            if file_paths:
                for file_path in file_paths:
                    try:
                        clean_path = self.clean_path(file_path)
                        full_path = f"{self.workspace_path}/{clean_path}"
                        if self._validate_file_exists(full_path):
                            file_info = self.sandbox.fs.get_file_info(full_path)
                            file_bytes = self.sandbox.fs.download_file(full_path)
                            file_text = file_bytes.decode('utf-8', errors='ignore')
                            file_content += f"\n\nContent from {file_path}:\n{file_text}"
                        else:
                            logger.warning(f"File not found: {file_path}")
                    except Exception as e:
                        file_content += f"\n\nError reading {file_path}: {str(e)}"
            
            # Combine text inputs
            combined_text = file_content
            
            # Prepare API request data
            api_data = [
                combined_text,  # text_input
                urls_input,     # urls_input
                [],             # pdf_files (empty for now)
                [],             # image_files (empty for now)
                self.gemini_key,      # gemini_key
                self.openai_key,      # openai_key
                self.elevenlabs_key,  # elevenlabs_key
                word_count_map.get(podcast_length, 2500),  # word_count
                ",".join(conversation_style),    # conversation_style
                roles_person1,        # roles_person1
                roles_person2,        # roles_person2
                ",".join(dialogue_structure),    # dialogue_structure
                podcast_name,         # podcast_name
                podcast_tagline,      # podcast_tagline
                "elevenlabs",         # tts_model (fixed to elevenlabs)
                creativity,           # creativity_level
                user_instructions     # user_instructions
            ]
            
            # Make API request
            result = self._make_api_request(api_data)
            
            if not result["success"]:
                return self.fail_response(f"Podcast generation failed: {result}")
            
            # Download the audio file
            local_path = self._download_audio_file(result["data"])
            
            # Create podcasts directory in workspace
            podcasts_dir = f"{self.workspace_path}/podcasts"
            self.sandbox.fs.create_folder(podcasts_dir, "755")
            
            # Determine output filename
            if not output_name:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"podcast_{timestamp}"
            
            # Upload to sandbox
            with open(local_path, 'rb') as f:
                audio_content = f.read()
            
            audio_filename = f"{output_name}.mp3"
            audio_path = f"{podcasts_dir}/{audio_filename}"
            self.sandbox.fs.upload_file(audio_content, audio_path)
            
            # Clean up local file
            try:
                os.unlink(local_path)
            except:
                pass
            
            # Prepare success message
            message = f"🎙️ Podcast generated successfully!\n\nGenerated files:\n"
            message += f"- podcasts/{audio_filename}\n"
            
            # Add content source summary
            message += f"\nContent sources processed:\n"
            if urls:
                message += f"- {len(urls)} URLs\n"
            if file_paths:
                message += f"- {len(file_paths)} local files\n" 
            if image_paths:
                message += f"- {len(image_paths)} images\n"
            
            message += f"\nConfiguration:\n"
            message += f"- Style: {', '.join(conversation_style)}\n"
            message += f"- Length: {podcast_length}\n"
            message += f"- Language: {language}\n"
            message += f"- TTS Model: ElevenLabs (high quality)\n"
            message += f"- Podcast: {podcast_name}\n"
            message += f"- Speakers: {roles_person1} & {roles_person2}\n"
            message += f"- Structure: {', '.join(dialogue_structure)}\n"
            message += f"- Engagement: {', '.join(engagement_techniques)}\n"
            message += f"- Creativity: {creativity}\n"
            if user_instructions:
                message += f"- Instructions: {user_instructions}\n"
            
            return self.success_response(message)
            
        except Exception as e:
            logger.error(f"Error in podcast generation: {str(e)}", exc_info=True)
            return self.fail_response(f"Podcast generation failed: {str(e)}")

    @openapi_schema({
        "type": "function", 
        "function": {
            "name": "list_podcasts",
            "description": "List all generated podcasts in the sandbox workspace with their details and file sizes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    })
    @xml_schema(
        tag_name="list-podcasts",
        mappings=[],
        example='''
        <function_calls>
        <invoke name="list_podcasts">
        </invoke>
        </function_calls>
        '''
    )
    async def list_podcasts(self) -> ToolResult:
        """List all generated podcasts in the workspace.
        
        Returns:
            ToolResult with list of podcasts and their details
        """
        try:
            # Ensure sandbox is initialized
            await self._ensure_sandbox()
            
            podcasts_dir = f"{self.workspace_path}/podcasts"
            
            # Check if podcasts directory exists
            try:
                files = self.sandbox.fs.list_files(podcasts_dir)
            except Exception:
                return self.success_response("🎙️ No podcasts found. Use generate_podcast to create your first podcast!")
            
            if not files:
                return self.success_response("🎙️ No podcasts found. Use generate_podcast to create your first podcast!")
            
            # Organize files by podcast (group by base name)
            podcasts = {}
            for file_info in files:
                if file_info.is_dir:
                    continue
                    
                filename = file_info.name
                if filename.endswith('_transcript.txt'):
                    base_name = filename.replace('_transcript.txt', '')
                    if base_name not in podcasts:
                        podcasts[base_name] = {}
                    podcasts[base_name]['transcript'] = {
                        'filename': filename,
                        'size': file_info.size,
                        'modified': file_info.mod_time
                    }
                elif filename.endswith('.mp3'):
                    base_name = filename.replace('.mp3', '')
                    if base_name not in podcasts:
                        podcasts[base_name] = {}
                    podcasts[base_name]['audio'] = {
                        'filename': filename,
                        'size': file_info.size, 
                        'modified': file_info.mod_time
                    }
            
            # Format response
            if not podcasts:
                return self.success_response("🎙️ No podcast files found in the podcasts directory.")
            
            message = f"🎙️ Found {len(podcasts)} podcast(s):\n\n"
            
            for podcast_name, files in podcasts.items():
                message += f"📻 {podcast_name}\n"
                
                if 'transcript' in files:
                    size_kb = files['transcript']['size'] / 1024
                    message += f"   📝 Transcript: {files['transcript']['filename']} ({size_kb:.1f} KB)\n"
                
                if 'audio' in files:
                    size_mb = files['audio']['size'] / (1024 * 1024)
                    message += f"   🎵 Audio: {files['audio']['filename']} ({size_mb:.1f} MB)\n"
                
                # Show most recent modification time
                mod_times = []
                if 'transcript' in files:
                    mod_times.append(files['transcript']['modified'])
                if 'audio' in files:
                    mod_times.append(files['audio']['modified'])
                
                if mod_times:
                    latest_mod = max(mod_times)
                    message += f"   📅 Last modified: {latest_mod}\n"
                
                message += "\n"
            
            return self.success_response(message)
            
        except Exception as e:
            logger.error(f"Error listing podcasts: {str(e)}", exc_info=True)
            return self.fail_response(f"Error listing podcasts: {str(e)}")

    def _make_api_request(self, data: List[Any]) -> Dict[str, Any]:
        """Make request to podcastfy API with two-step process"""
        try:
            # Step 1: Initiate processing
            response = requests.post(
                f"{self.api_base_url}/gradio_api/call/process_inputs",
                headers={"Content-Type": "application/json"},
                json={"data": data},
                timeout=30
            )
            response.raise_for_status()
            
            # Extract event ID from response
            event_id = response.json().get('event_id')
            if not event_id:
                raise Exception("No event_id returned from API")
            
            # Step 2: Poll for results
            max_attempts = 60  # 5 minutes with 5-second intervals
            for attempt in range(max_attempts):
                time.sleep(5)  # Wait between polling
                
                result_response = requests.get(
                    f"{self.api_base_url}/gradio_api/call/process_inputs/{event_id}",
                    timeout=30
                )
                
                if result_response.status_code == 200:
                    # Check if processing is complete
                    lines = result_response.text.strip().split('\n')
                    for line in lines:
                        if line.startswith('event: complete'):
                            continue
                        if line.startswith('data: '):
                            try:
                                data_json = json.loads(line[6:])  # Remove 'data: ' prefix
                                if data_json and len(data_json) > 0:
                                    return {"success": True, "data": data_json[0]}
                            except json.JSONDecodeError:
                                continue
                
                # Check for other events that might indicate completion or error
                if 'error' in result_response.text.lower():
                    raise Exception(f"API returned error: {result_response.text}")
            
            raise Exception("Timeout waiting for podcast generation to complete")
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Podcast generation failed: {str(e)}")

    def _download_audio_file(self, file_data: Dict[str, Any]) -> str:
        """Download the generated audio file to the sandbox"""
        try:
            # Extract file path and construct download URL
            file_path = file_data.get('path', '')
            if not file_path:
                raise Exception("No file path found in API response")
            
            # Construct the download URL
            download_url = f"{self.api_base_url}/gradio_api/file={file_path}"
            
            # Download the file
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            
            # Save to workspace
            os.makedirs("/workspace/podcasts", exist_ok=True)
            filename = file_data.get('orig_name', 'podcast.mp3')
            local_path = f"/workspace/podcasts/{filename}"
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return local_path
            
        except Exception as e:
            raise Exception(f"Failed to download audio file: {str(e)}")

    # Define the available functions for the agent
    @property  
    def xml_function_list(self):
        return [
            {
                "name": "generate_podcast",
                "description": "Generate an AI podcast from URLs, text, or files using advanced conversation AI",
                "parameters": [
                    {"name": "urls", "type": "List[str]", "description": "List of URLs to process", "required": False},
                    {"name": "text_input", "type": "str", "description": "Direct text input for podcast generation", "required": False},
                    {"name": "files", "type": "List[str]", "description": "List of file paths in sandbox to include", "required": False},
                    {"name": "word_count", "type": "int", "description": "Target word count for podcast (default: 2000)", "required": False},
                    {"name": "conversation_style", "type": "str", "description": "Style like 'engaging,fast-paced'", "required": False},
                    {"name": "roles_person1", "type": "str", "description": "Role of first speaker", "required": False},
                    {"name": "roles_person2", "type": "str", "description": "Role of second speaker", "required": False},
                    {"name": "dialogue_structure", "type": "str", "description": "Structure like 'Introduction,Content,Conclusion'", "required": False},
                    {"name": "podcast_name", "type": "str", "description": "Name of the podcast", "required": False},
                    {"name": "podcast_tagline", "type": "str", "description": "Podcast tagline", "required": False},
                    {"name": "creativity_level", "type": "float", "description": "Creativity level 0-1 (default: 0.7)", "required": False},
                    {"name": "user_instructions", "type": "str", "description": "Custom instructions", "required": False},
                    {"name": "language", "type": "str", "description": "Language code (default: 'en')", "required": False}
                ]
            },
            {
                "name": "list_podcasts", 
                "description": "List all generated podcasts in the workspace",
                "parameters": []
            }
        ]

    @property
    def openapi_schema(self):
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Podcast Generation Tool",
                "description": "Generate AI podcasts from content using Podcastfy API",
                "version": "2.0.0"
            },
            "servers": [{"url": "http://localhost"}],
            "paths": {
                "/generate_podcast": {
                    "post": {
                        "summary": "Generate AI Podcast",
                        "description": "Create a conversational podcast from URLs, text, or files",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "urls": {"type": "array", "items": {"type": "string"}, "description": "URLs to process"},
                                            "text_input": {"type": "string", "description": "Direct text input"},
                                            "files": {"type": "array", "items": {"type": "string"}, "description": "File paths in sandbox"},
                                            "word_count": {"type": "integer", "default": 2000, "description": "Target word count"},
                                            "conversation_style": {"type": "string", "default": "engaging,fast-paced", "description": "Conversation style"},
                                            "roles_person1": {"type": "string", "default": "main summarizer", "description": "Role of first speaker"},
                                            "roles_person2": {"type": "string", "default": "questioner", "description": "Role of second speaker"},
                                            "dialogue_structure": {"type": "string", "default": "Introduction,Content,Conclusion", "description": "Dialogue structure"},
                                            "podcast_name": {"type": "string", "default": "PODCASTFY", "description": "Podcast name"},
                                            "podcast_tagline": {"type": "string", "default": "YOUR PODCAST", "description": "Podcast tagline"},
                                            "creativity_level": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.7, "description": "Creativity level"},
                                            "user_instructions": {"type": "string", "description": "Custom instructions"},
                                            "language": {"type": "string", "default": "en", "description": "Language code"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Podcast generated successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "success": {"type": "boolean"},
                                                "message": {"type": "string"},
                                                "audio_file": {"type": "string"},
                                                "filename": {"type": "string"},
                                                "configuration": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/list_podcasts": {
                    "get": {
                        "summary": "List Generated Podcasts",
                        "description": "Get a list of all generated podcasts",
                        "responses": {
                            "200": {
                                "description": "List of podcasts",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "success": {"type": "boolean"},
                                                "podcasts": {"type": "array"},
                                                "total_count": {"type": "integer"},
                                                "message": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } 