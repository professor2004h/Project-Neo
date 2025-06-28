import os
import json
import tempfile
import subprocess
import asyncio
import datetime
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from agentpress.tool import ToolResult, openapi_schema, xml_schema
from sandbox.tool_base import SandboxToolsBase
from agentpress.thread_manager import ThreadManager
from utils.logger import logger


class SandboxPodcastTool(SandboxToolsBase):
    """Tool for generating AI-powered podcasts from various content sources using podcastfy.
    
    Supports generating podcasts from:
    - Website URLs 
    - Local files in the sandbox (PDFs, text files, images)
    - File URLs 
    - Multiple content sources combined
    
    Generated podcasts are saved in the sandbox for easy access.
    """

    def __init__(self, project_id: str, thread_manager: ThreadManager):
        super().__init__(project_id, thread_manager)
        self.workspace_path = "/workspace"
        
    def _check_podcastfy_installation(self) -> bool:
        """Check if podcastfy is installed and install if needed."""
        try:
            import podcastfy
            return True
        except ImportError:
            logger.info("Installing podcastfy library...")
            try:
                subprocess.run([
                    "pip", "install", "podcastfy==0.4.1"
                ], check=True, capture_output=True)
                logger.info("Podcastfy installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install podcastfy: {e}")
                return False

    def _validate_file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the sandbox."""
        try:
            self.sandbox.fs.get_file_info(file_path)
            return True
        except Exception:
            return False

    async def _generate_podcast_with_podcastfy(self, 
                                             urls: Optional[List[str]] = None,
                                             file_paths: Optional[List[str]] = None,
                                             image_paths: Optional[List[str]] = None,
                                             conversation_config: Optional[Dict[str, Any]] = None,
                                             tts_model: str = "openai",
                                             transcript_only: bool = False) -> Dict[str, Any]:
        """Generate podcast using podcastfy library."""
        
        # Import podcastfy after ensuring it's installed
        try:
            from podcastfy.client import generate_podcast
        except ImportError as e:
            logger.error(f"Failed to import podcastfy: {e}")
            raise Exception("Podcastfy library not available")

        # Prepare generation parameters
        generation_params = {}
        
        # Add URLs if provided
        if urls:
            generation_params["urls"] = urls
            
        # Handle local files by downloading them to temp directory for podcastfy
        temp_files = []
        if file_paths:
            temp_dir = tempfile.mkdtemp()
            for file_path in file_paths:
                try:
                    # Download file from sandbox
                    file_content = self.sandbox.fs.download_file(file_path)
                    
                    # Create temp file with same extension
                    file_name = os.path.basename(file_path)
                    temp_file_path = os.path.join(temp_dir, file_name)
                    
                    with open(temp_file_path, 'wb') as f:
                        f.write(file_content)
                    
                    temp_files.append(temp_file_path)
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue
            
            if temp_files:
                if not generation_params.get("urls"):
                    generation_params["urls"] = temp_files
                else:
                    generation_params["urls"].extend(temp_files)
        
        # Handle image paths
        if image_paths:
            temp_dir = tempfile.mkdtemp() if not temp_files else os.path.dirname(temp_files[0])
            temp_image_files = []
            
            for image_path in image_paths:
                try:
                    clean_path = self.clean_path(image_path)
                    full_path = f"{self.workspace_path}/{clean_path}"
                    
                    if self._validate_file_exists(full_path):
                        # Download image from sandbox
                        image_content = self.sandbox.fs.download_file(full_path)
                        
                        # Create temp file
                        image_name = os.path.basename(image_path)
                        temp_image_path = os.path.join(temp_dir, image_name)
                        
                        with open(temp_image_path, 'wb') as f:
                            f.write(image_content)
                        
                        temp_image_files.append(temp_image_path)
                        
                except Exception as e:
                    logger.error(f"Error processing image {image_path}: {e}")
                    continue
            
            if temp_image_files:
                generation_params["image_paths"] = temp_image_files

        # Set conversation config if provided
        if conversation_config:
            generation_params["conversation_config"] = conversation_config
            
        # Set TTS model
        generation_params["tts_model"] = tts_model
        
        # Set transcript only flag
        generation_params["transcript_only"] = transcript_only
        
        # Generate podcast
        try:
            logger.info("Generating podcast with podcastfy...")
            result = generate_podcast(**generation_params)
            
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            if image_paths and 'temp_image_files' in locals():
                for temp_file in temp_image_files:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            return {"status": "error", "error": str(e)}

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
                    "tts_model": {
                        "type": "string",
                        "description": "Text-to-speech model to use. Options: 'openai' (default), 'elevenlabs' (higher quality but requires API key)", 
                        "default": "openai"
                    },
                    "transcript_only": {
                        "type": "boolean",
                        "description": "If true, only generate the transcript without audio. Useful for reviewing content before audio generation.",
                        "default": False
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
            {"param_name": "tts_model", "node_type": "attribute", "path": ".", "required": False},
            {"param_name": "transcript_only", "node_type": "attribute", "path": ".", "required": False}
        ],
        example='''
        <function_calls>
        <invoke name="generate_podcast">
        <parameter name="urls">["https://example.com/article1", "https://example.com/article2"]</parameter>
        <parameter name="file_paths">["documents/research.pdf", "notes/summary.txt"]</parameter>
        <parameter name="output_name">my_research_podcast</parameter>
        <parameter name="conversation_style">["educational", "analytical"]</parameter>
        <parameter name="podcast_length">medium</parameter>
        <parameter name="language">English</parameter>
        <parameter name="tts_model">openai</parameter>
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
                             tts_model: str = "openai",
                             transcript_only: bool = False) -> ToolResult:
        """Generate an AI-powered podcast from various content sources.
        
        Args:
            urls: List of website URLs to include
            file_paths: List of local file paths in the sandbox
            image_paths: List of image file paths in the sandbox  
            output_name: Custom name for output files
            conversation_style: Style of conversation
            podcast_length: Desired length (short/medium/long)
            language: Language for the podcast
            tts_model: TTS model to use (openai/elevenlabs)
            transcript_only: Generate only transcript without audio
            
        Returns:
            ToolResult with podcast generation status and file locations
        """
        try:
            # Ensure sandbox is initialized
            await self._ensure_sandbox()
            
            # Validate inputs
            if not any([urls, file_paths, image_paths]):
                return self.fail_response("At least one content source (URLs, files, or images) must be provided")
            
            # Check and install podcastfy if needed
            if not self._check_podcastfy_installation():
                return self.fail_response("Failed to install podcastfy library")
            
            # Prepare conversation configuration
            word_count_map = {
                "short": 1000,
                "medium": 2500, 
                "long": 4000
            }
            
            conversation_config = {
                "word_count": word_count_map.get(podcast_length, 2500),
                "conversation_style": conversation_style,
                "output_language": language,
                "podcast_name": "AI Generated Podcast",
                "podcast_tagline": "Transforming content into engaging conversations"
            }
            
            # Validate file paths and prepare them
            validated_file_paths = []
            if file_paths:
                for file_path in file_paths:
                    clean_path = self.clean_path(file_path)
                    full_path = f"{self.workspace_path}/{clean_path}"
                    if self._validate_file_exists(full_path):
                        validated_file_paths.append(full_path)
                    else:
                        logger.warning(f"File not found: {file_path}")
            
            # Generate podcast
            result = await self._generate_podcast_with_podcastfy(
                urls=urls,
                file_paths=validated_file_paths if validated_file_paths else None,
                image_paths=image_paths,
                conversation_config=conversation_config,
                tts_model=tts_model,
                transcript_only=transcript_only
            )
            
            if result["status"] == "error":
                return self.fail_response(f"Podcast generation failed: {result['error']}")
            
            # Process the generated files
            generated_result = result["result"]
            
            # Create podcasts directory in workspace
            podcasts_dir = f"{self.workspace_path}/podcasts"
            self.sandbox.fs.create_folder(podcasts_dir, "755")
            
            # Determine output filename
            if not output_name:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"podcast_{timestamp}"
            
            saved_files = []
            
            # Handle transcript file (if generated)
            if isinstance(generated_result, tuple) and len(generated_result) >= 1:
                transcript_file = generated_result[0]
                if transcript_file and os.path.exists(transcript_file):
                    # Read transcript content
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        transcript_content = f.read()
                    
                    # Save to sandbox
                    transcript_filename = f"{output_name}_transcript.txt"
                    transcript_path = f"{podcasts_dir}/{transcript_filename}"
                    self.sandbox.fs.upload_file(transcript_content.encode('utf-8'), transcript_path)
                    saved_files.append(f"podcasts/{transcript_filename}")
            
            # Handle audio file (if generated)
            if not transcript_only:
                if isinstance(generated_result, tuple) and len(generated_result) >= 2:
                    audio_file = generated_result[1]
                elif isinstance(generated_result, str) and generated_result.endswith(('.mp3', '.wav')):
                    audio_file = generated_result
                else:
                    audio_file = None
                
                if audio_file and os.path.exists(audio_file):
                    # Read audio content
                    with open(audio_file, 'rb') as f:
                        audio_content = f.read()
                    
                    # Save to sandbox
                    audio_filename = f"{output_name}.mp3"
                    audio_path = f"{podcasts_dir}/{audio_filename}"
                    self.sandbox.fs.upload_file(audio_content, audio_path)
                    saved_files.append(f"podcasts/{audio_filename}")
            
            # Prepare success message
            if transcript_only:
                message = f"🎙️ Podcast transcript generated successfully!\n\nGenerated files:\n"
            else:
                message = f"🎙️ Podcast generated successfully!\n\nGenerated files:\n"
            
            for file_path in saved_files:
                message += f"- {file_path}\n"
            
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
            message += f"- TTS Model: {tts_model}\n"
            
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