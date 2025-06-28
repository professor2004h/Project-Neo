"""
MeetingBaaS API Service

Simple API client for MeetingBaaS meeting transcription service.
Handles bot creation, status monitoring, and webhook events.
"""

import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional


class MeetingBaaSService:
    """
    Service for interacting with MeetingBaaS API.
    
    Provides methods to:
    1. Send bots to join meetings
    2. Monitor bot status
    3. Stop bots and get transcripts
    """
    
    def __init__(self):
        self.api_key = os.getenv('MEETINGBAAS_API_KEY')
        self.base_url = 'https://api.meetingbaas.com'
        
    async def start_meeting_bot(self, meeting_url: str, bot_name: str = "Omni Operator", webhook_url: str = None) -> Dict[str, Any]:
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
            'recording_mode': 'audio_only',  # Required field
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
        
        print(f"[MEETING BAAS] Making request to: {self.base_url}/bots")
        print(f"[MEETING BAAS] Headers: {headers}")
        print(f"[MEETING BAAS] Payload: {payload}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/bots',
                    headers=headers,
                    json=payload
                ) as response:
                    
                    print(f"[MEETING BAAS] Response status: {response.status}")
                    response_text = await response.text()
                    print(f"[MEETING BAAS] Response body: {response_text}")
                    
                    if response.status in [200, 201]:  # Accept both 200 and 201
                        try:
                            result = await response.json()
                            print(f"[MEETING BAAS] Parsed JSON: {result}")
                            
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
                            print(f"[MEETING BAAS] JSON parsing error: {json_error}")
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
            print(f"[MEETING BAAS] Request error: {request_error}")
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


# Service instance for API usage
meeting_baas_service = MeetingBaaSService() 