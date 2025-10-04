"""
MCP (Model Context Protocol) Server Integration for Magentic-UI Voice Backend
Integrates with Cartesia, HeyGen, and other MCP servers for enhanced capabilities
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import aiohttp
import yaml

logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    description: str
    base_url: str
    api_key_env: str
    capabilities: List[str]
    integration_points: List[str]

class MCPServerManager:
    """Manages connections and interactions with MCP servers"""
    
    def __init__(self, config_path: str = "mcp-config.yaml"):
        self.config_path = config_path
        self.servers: Dict[str, MCPServerConfig] = {}
        self.active_connections: Dict[str, aiohttp.ClientSession] = {}
        self.load_config()
    
    def load_config(self):
        """Load MCP server configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Look in parent directory
                config_file = Path("../mcp-config.yaml")
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            for name, server_config in config.get('mcp_servers', {}).items():
                self.servers[name] = MCPServerConfig(
                    name=name,
                    description=server_config['description'],
                    base_url=server_config['server_params']['base_url'],
                    api_key_env=server_config['server_params']['api_key_env'],
                    capabilities=server_config['capabilities'],
                    integration_points=server_config['integration_points']
                )
            
            logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            self.servers = {}
    
    async def initialize_connections(self):
        """Initialize connections to all configured MCP servers"""
        for name, server in self.servers.items():
            try:
                session = aiohttp.ClientSession(
                    base_url=server.base_url,
                    headers={
                        "Authorization": f"Bearer {self._get_api_key(server.api_key_env)}",
                        "Content-Type": "application/json"
                    }
                )
                
                # Test connection
                async with session.get("/health") as response:
                    if response.status == 200:
                        self.active_connections[name] = session
                        logger.info(f"Connected to MCP server: {name}")
                    else:
                        logger.warning(f"MCP server {name} health check failed: {response.status}")
                        await session.close()
                        
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {name}: {e}")
    
    def _get_api_key(self, env_var: str) -> str:
        """Get API key from environment variable"""
        import os
        return os.getenv(env_var, "")
    
    async def call_cartesia_voice_clone(self, audio_file_path: str, voice_name: str, 
                                      language: str = "en", mode: str = "similarity") -> Dict[str, Any]:
        """Clone a voice using Cartesia MCP server"""
        if "cartesia" not in self.active_connections:
            raise Exception("Cartesia MCP server not connected")
        
        session = self.active_connections["cartesia"]
        
        # Read audio file
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        data = aiohttp.FormData()
        data.add_field('file', audio_data, filename=Path(audio_file_path).name)
        data.add_field('name', voice_name)
        data.add_field('language', language)
        data.add_field('mode', mode)
        
        try:
            async with session.post("/voice/clone", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Voice cloned successfully: {voice_name}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Voice cloning failed: {error}")
                    raise Exception(f"Voice cloning failed: {error}")
                    
        except Exception as e:
            logger.error(f"Cartesia voice clone error: {e}")
            raise
    
    async def call_cartesia_text_to_speech(self, text: str, voice_id: str, 
                                         output_format: Dict[str, Any] = None) -> bytes:
        """Generate speech using Cartesia TTS"""
        if "cartesia" not in self.active_connections:
            raise Exception("Cartesia MCP server not connected")
        
        session = self.active_connections["cartesia"]
        
        if output_format is None:
            output_format = {
                "container": "wav",
                "sample_rate": 16000,
                "encoding": "pcm_s16le"
            }
        
        payload = {
            "transcript": text,
            "voice": {"id": voice_id},
            "output_format": output_format,
            "model_id": "sonic-2"
        }
        
        try:
            async with session.post("/tts", json=payload) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    logger.info(f"TTS generated successfully for voice: {voice_id}")
                    return audio_data
                else:
                    error = await response.text()
                    logger.error(f"TTS generation failed: {error}")
                    raise Exception(f"TTS generation failed: {error}")
                    
        except Exception as e:
            logger.error(f"Cartesia TTS error: {e}")
            raise
    
    async def call_heygen_generate_avatar_video(self, avatar_id: str, voice_id: str, 
                                              input_text: str, title: str = "") -> Dict[str, Any]:
        """Generate avatar video using HeyGen MCP server"""
        if "heygen" not in self.active_connections:
            raise Exception("HeyGen MCP server not connected")
        
        session = self.active_connections["heygen"]
        
        payload = {
            "avatar_id": avatar_id,
            "voice_id": voice_id,
            "input_text": input_text,
            "title": title
        }
        
        try:
            async with session.post("/v2/video/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Avatar video generation started: {result.get('video_id')}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Avatar video generation failed: {error}")
                    raise Exception(f"Avatar video generation failed: {error}")
                    
        except Exception as e:
            logger.error(f"HeyGen avatar video error: {e}")
            raise
    
    async def get_heygen_avatar_groups(self, include_public: bool = False) -> List[Dict[str, Any]]:
        """Get available avatar groups from HeyGen"""
        if "heygen" not in self.active_connections:
            raise Exception("HeyGen MCP server not connected")
        
        session = self.active_connections["heygen"]
        
        params = {"include_public": include_public}
        
        try:
            async with session.get("/v1/avatar.list", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Retrieved {len(result.get('data', []))} avatar groups")
                    return result.get('data', [])
                else:
                    error = await response.text()
                    logger.error(f"Failed to get avatar groups: {error}")
                    raise Exception(f"Failed to get avatar groups: {error}")
                    
        except Exception as e:
            logger.error(f"HeyGen avatar groups error: {e}")
            raise
    
    async def setup_webhooks(self, base_url: str):
        """Setup webhooks for MCP server notifications"""
        webhook_configs = [
            {
                "server": "heygen",
                "url": f"{base_url}/webhooks/heygen/completion",
                "events": ["video.completed", "avatar.created"]
            },
            {
                "server": "cartesia", 
                "url": f"{base_url}/webhooks/cartesia/processing",
                "events": ["voice.cloned", "tts.completed"]
            }
        ]
        
        for webhook_config in webhook_configs:
            server_name = webhook_config["server"]
            if server_name in self.active_connections:
                session = self.active_connections[server_name]
                
                payload = {
                    "url": webhook_config["url"],
                    "events": webhook_config["events"]
                }
                
                try:
                    async with session.post("/webhooks/endpoints", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Webhook setup successful for {server_name}: {result}")
                        else:
                            logger.warning(f"Webhook setup failed for {server_name}: {response.status}")
                            
                except Exception as e:
                    logger.error(f"Webhook setup error for {server_name}: {e}")
    
    async def close_connections(self):
        """Close all MCP server connections"""
        for name, session in self.active_connections.items():
            try:
                await session.close()
                logger.info(f"Closed connection to MCP server: {name}")
            except Exception as e:
                logger.error(f"Error closing connection to {name}: {e}")
        
        self.active_connections.clear()

# Enhanced Voice Processor with MCP Integration
class EnhancedVoiceProcessor:
    """Voice processor with MCP server capabilities"""
    
    def __init__(self, mcp_manager: MCPServerManager):
        self.mcp_manager = mcp_manager
        self.voice_cache: Dict[str, str] = {}  # Cache for cloned voice IDs
    
    async def process_voice_with_enhancement(self, audio_data: bytes, 
                                           enhancement_type: str = "clone") -> bytes:
        """Process voice with MCP server enhancements"""
        
        if enhancement_type == "clone":
            # Save audio to temp file
            temp_file = "/tmp/voice_input.wav"
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            # Clone voice using Cartesia
            voice_result = await self.mcp_manager.call_cartesia_voice_clone(
                audio_file_path=temp_file,
                voice_name=f"user_voice_{hash(audio_data)}",
                language="en",
                mode="similarity"
            )
            
            voice_id = voice_result.get('voice_id')
            if voice_id:
                self.voice_cache[f"user_{hash(audio_data)}"] = voice_id
                logger.info(f"Voice cloned and cached: {voice_id}")
            
            return audio_data  # Return original for now
        
        return audio_data
    
    async def generate_enhanced_response(self, text: str, user_voice_hash: str = None) -> bytes:
        """Generate TTS response using cloned voice if available"""
        
        # Use cloned voice if available
        if user_voice_hash and user_voice_hash in self.voice_cache:
            voice_id = self.voice_cache[user_voice_hash]
            logger.info(f"Using cloned voice for response: {voice_id}")
            
            return await self.mcp_manager.call_cartesia_text_to_speech(
                text=text,
                voice_id=voice_id
            )
        
        # Fallback to default voice processing
        logger.info("Using default voice processing")
        return text.encode()  # Placeholder
    
    async def create_avatar_video_response(self, text: str, avatar_id: str = None) -> Dict[str, Any]:
        """Create avatar video response using HeyGen"""
        
        if not avatar_id:
            # Get default avatar
            avatar_groups = await self.mcp_manager.get_heygen_avatar_groups()
            if avatar_groups:
                avatar_id = avatar_groups[0].get('avatar_id')
        
        if avatar_id:
            return await self.mcp_manager.call_heygen_generate_avatar_video(
                avatar_id=avatar_id,
                voice_id="default_voice",
                input_text=text,
                title="Magentic-UI Response"
            )
        
        raise Exception("No avatar available for video generation")

# Global MCP manager instance
mcp_manager = MCPServerManager()
enhanced_voice_processor = EnhancedVoiceProcessor(mcp_manager)

async def initialize_mcp_integration():
    """Initialize MCP integration for voice backend"""
    logger.info("Initializing MCP server integration...")
    await mcp_manager.initialize_connections()
    
    # Setup webhooks if base URL is available
    import os
    base_url = os.getenv('VOICE_BACKEND_BASE_URL', 'http://localhost:8765')
    await mcp_manager.setup_webhooks(base_url)
    
    logger.info("MCP integration initialized successfully")

async def cleanup_mcp_integration():
    """Cleanup MCP integration"""
    logger.info("Cleaning up MCP server integration...")
    await mcp_manager.close_connections()
    logger.info("MCP integration cleanup completed")
