"""
MeetingBaaS Integration Tool

Sends bots to join online meetings (Zoom, Teams, Google Meet) for transcription.
Uses MeetingBaaS API ($0.69/hour) as the backend service.

Example usage:
- User enters meeting URL (e.g., zoom.us/j/123456789)
- Bot joins meeting automatically
- Records and transcribes in real-time
- Returns transcript when meeting ends
"""

import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional
from agentpress import SandboxToolsBase


class MeetingBotTool(SandboxToolsBase):
    """
    Tool for joining online meetings with a transcription bot.
    
    Uses MeetingBaaS API to:
    1. Send bot to join meeting via URL
    2. Record and transcribe meeting audio
    3. Return transcript and metadata
    """
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('MEETINGBAAS_API_KEY')
        self.base_url = 'https://api.meetingbaas.com'  # Remove /v1 suffix
        
    async def start_meeting_bot(self, meeting_url: str, bot_name: str = "Transcription Bot", webhook_url: str = None) -> Dict[str, Any]:
        """
        Start a meeting bot to join and transcribe the meeting.
        
        Args:
            meeting_url: URL of the meeting (Zoom, Teams, Meet, etc.)
            bot_name: Name to display for the bot in the meeting
            webhook_url: URL to receive real-time webhook events
            
        Returns:
            Dictionary with bot_id and status
        """
        
        if not self.api_key:
            raise ValueError("MEETINGBAAS_API_KEY environment variable not set")
            
        headers = {
            'x-meeting-baas-api-key': self.api_key,  # Correct header format
            'Content-Type': 'application/json'
        }
        
        payload = {
            'meeting_url': meeting_url,
            'bot_name': bot_name,
            'recording_mode': 'speaker_view',  # Required field
            'reserved': False,  # Join immediately
            'speech_to_text': {
                'provider': 'Default'  # Required speech-to-text config
            },
            'automatic_leave': {
                'waiting_room_timeout': 600  # 10 minutes timeout
            }
        }
        
        # Add webhook URL for real-time updates (replaces polling!)
        if webhook_url:
            payload['webhook_url'] = webhook_url
        
        print(f"[MEETING BOT TOOL] Making request to: {self.base_url}/bots")
        print(f"[MEETING BOT TOOL] Headers: {headers}")
        print(f"[MEETING BOT TOOL] Payload: {payload}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/bots',
                    headers=headers,
                    json=payload
                ) as response:
                    
                    print(f"[MEETING BOT TOOL] Response status: {response.status}")
                    response_text = await response.text()
                    print(f"[MEETING BOT TOOL] Response body: {response_text}")
                    
                    if response.status in [200, 201]:  # Accept both 200 and 201
                        try:
                            result = await response.json()
                            print(f"[MEETING BOT TOOL] Parsed JSON: {result}")
                            
                            # Try different possible field names for bot ID
                            bot_id = result.get('bot_id') or result.get('id') or result.get('botId')
                            
                            return {
                                'success': True,
                                'bot_id': bot_id,
                                'status': 'joining',
                                'meeting_url': meeting_url,
                                'message': f'Bot "{bot_name}" is joining the meeting...'
                            }
                        except Exception as json_error:
                            print(f"[MEETING BOT TOOL] JSON parsing error: {json_error}")
                            return {
                                'success': False,
                                'error': f'Failed to parse response: {str(json_error)}',
                                'status_code': response.status
                            }
                    else:
                        return {
                            'success': False,
                            'error': f'API returned {response.status}: {response_text}',
                            'status_code': response.status
                        }
        except Exception as request_error:
            print(f"[MEETING BOT TOOL] Request error: {request_error}")
            return {
                'success': False,
                'error': f'Request failed: {str(request_error)}'
            }
    
    async def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        """
        Get the current status of a meeting bot.
        
        Args:
            bot_id: ID of the bot to check
            
        Returns:
            Dictionary with bot status and transcript if available
        """
        
        headers = {
            'x-meeting-baas-api-key': self.api_key,  # Correct header format
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{self.base_url}/bots/{bot_id}',
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'status': result.get('status'),
                        'transcript': result.get('transcript', ''),
                        'participants': result.get('participants', []),
                        'duration': result.get('duration_seconds', 0),
                        'recording_url': result.get('recording_url')
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to get bot status: {await response.text()}'
                    }
    
    async def stop_meeting_bot(self, bot_id: str) -> Dict[str, Any]:
        """
        Stop a meeting bot and get final transcript.
        
        Args:
            bot_id: ID of the bot to stop
            
        Returns:
            Dictionary with final transcript and metadata
        """
        
        headers = {
            'x-meeting-baas-api-key': self.api_key,  # Correct header format
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f'{self.base_url}/bots/{bot_id}',
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    # MeetingBaaS returns {"ok": true} for DELETE requests
                    if result.get('ok'):
                        return {
                            'success': True,
                            'message': 'Bot successfully removed from meeting',
                            'transcript': '',  # Will be provided via webhook
                            'participants': [],
                            'duration': 0
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Bot removal not confirmed'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to stop bot: {await response.text()}'
                    }

    async def join_meeting_and_transcribe(self, meeting_url: str, bot_name: str = "AI Transcription Bot") -> str:
        """
        High-level function to join a meeting and return when transcript is ready.
        
        This is the main function called by the agent.
        
        Args:
            meeting_url: URL of the meeting to join
            bot_name: Display name for the bot
            
        Returns:
            String with meeting transcript and summary
        """
        
        try:
            # Validate meeting URL
            if not meeting_url or not isinstance(meeting_url, str):
                return "Error: Please provide a valid meeting URL"
                
            supported_platforms = ['zoom.us', 'teams.microsoft.com', 'meet.google.com', 'webex.com']
            if not any(platform in meeting_url.lower() for platform in supported_platforms):
                return f"Error: Meeting URL should be from supported platforms: {', '.join(supported_platforms)}"
            
            # Start the bot
            start_result = await self.start_meeting_bot(meeting_url, bot_name)
            
            if not start_result.get('success'):
                return f"Failed to start meeting bot: {start_result.get('error', 'Unknown error')}"
            
            bot_id = start_result['bot_id']
            
            # Wait for bot to join and start recording
            await asyncio.sleep(10)  # Give bot time to join
            
            # Check status
            status_result = await self.get_bot_status(bot_id)
            
            if status_result.get('success'):
                status = status_result.get('status')
                if status == 'recording':
                    return f"✅ Meeting bot successfully joined! Bot ID: {bot_id}\n\nThe bot is now recording and transcribing the meeting. You can check the status or stop the bot anytime.\n\nTo get the transcript later, use the bot ID: {bot_id}"
                elif status == 'joining':
                    return f"🔄 Bot is still joining the meeting... Bot ID: {bot_id}\n\nPlease wait a moment for the bot to fully join."
                elif status == 'failed':
                    return f"❌ Bot failed to join the meeting. This could be due to:\n- Meeting room restrictions\n- Invalid URL\n- Meeting hasn't started yet\n\nBot ID: {bot_id}"
                else:
                    return f"Bot status: {status}. Bot ID: {bot_id}"
            else:
                return f"Could not get bot status: {status_result.get('error')}"
                
        except Exception as e:
            return f"Error starting meeting bot: {str(e)}"

    async def get_meeting_transcript(self, bot_id: str) -> str:
        """
        Get the current or final transcript from a meeting bot.
        
        Args:
            bot_id: ID of the bot to get transcript from
            
        Returns:
            String with transcript and metadata
        """
        
        try:
            status_result = await self.get_bot_status(bot_id)
            
            if not status_result.get('success'):
                return f"Error getting transcript: {status_result.get('error')}"
            
            status = status_result.get('status')
            transcript = status_result.get('transcript', '')
            participants = status_result.get('participants', [])
            duration = status_result.get('duration', 0)
            
            if not transcript:
                if status == 'recording':
                    return "Meeting is still in progress. No transcript available yet."
                elif status == 'joining':
                    return "Bot is still joining the meeting. No transcript available yet."
                else:
                    return f"No transcript available. Bot status: {status}"
            
            # Format the response
            response = f"📋 **Meeting Transcript**\n\n"
            response += f"**Status:** {status.title()}\n"
            response += f"**Duration:** {duration // 60}m {duration % 60}s\n"
            response += f"**Participants:** {', '.join(participants) if participants else 'Not available'}\n\n"
            response += f"**Transcript:**\n{transcript}\n"
            
            if status == 'completed':
                response += "\n✅ Meeting has ended. This is the final transcript."
            elif status == 'recording':
                response += "\n🔄 Meeting is ongoing. This is a partial transcript."
            
            return response
            
        except Exception as e:
            return f"Error getting transcript: {str(e)}"

    async def stop_meeting_recording(self, bot_id: str) -> str:
        """
        Stop a meeting bot and get the final transcript.
        
        Args:
            bot_id: ID of the bot to stop
            
        Returns:
            String with final transcript and summary
        """
        
        try:
            stop_result = await self.stop_meeting_bot(bot_id)
            
            if not stop_result.get('success'):
                return f"Error stopping bot: {stop_result.get('error')}"
            
            transcript = stop_result.get('transcript', '')
            summary = stop_result.get('summary', '')
            action_items = stop_result.get('action_items', [])
            participants = stop_result.get('participants', [])
            duration = stop_result.get('duration', 0)
            
            response = f"🛑 **Meeting Recording Stopped**\n\n"
            response += f"**Duration:** {duration // 60}m {duration % 60}s\n"
            response += f"**Participants:** {', '.join(participants) if participants else 'Not available'}\n\n"
            
            if summary:
                response += f"**Summary:**\n{summary}\n\n"
            
            if action_items:
                response += f"**Action Items:**\n"
                for item in action_items:
                    response += f"• {item}\n"
                response += "\n"
            
            if transcript:
                response += f"**Full Transcript:**\n{transcript}"
            else:
                response += "No transcript was generated."
            
            return response
            
        except Exception as e:
            return f"Error stopping meeting bot: {str(e)}"


# Tool registration for agentpress
tool = MeetingBotTool() 