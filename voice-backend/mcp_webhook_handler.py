"""
MCP Webhook Handler for Magentic-UI Voice Backend
Handles webhooks from MCP servers (Cartesia, HeyGen, etc.)
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

# Create router for MCP webhooks
mcp_router = APIRouter(prefix="/webhooks", tags=["mcp"])

@mcp_router.post("/cartesia/processing")
async def handle_cartesia_webhook(request: Request):
    """Handle Cartesia voice processing webhooks"""
    try:
        payload = await request.json()
        event_type = payload.get("event_type")
        
        logger.info(f"Received Cartesia webhook: {event_type}")
        
        if event_type == "voice.cloned":
            voice_id = payload.get("voice_id")
            voice_name = payload.get("voice_name")
            logger.info(f"Voice cloned successfully: {voice_name} -> {voice_id}")
            
            # Store voice mapping for future use
            # This could be stored in a database or cache
            
        elif event_type == "tts.completed":
            audio_url = payload.get("audio_url")
            request_id = payload.get("request_id")
            logger.info(f"TTS completed for request: {request_id}")
            
            # Handle completed TTS processing
            
        return {"status": "success", "processed": event_type}
        
    except Exception as e:
        logger.error(f"Error processing Cartesia webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mcp_router.post("/heygen/completion")
async def handle_heygen_webhook(request: Request):
    """Handle HeyGen video generation webhooks"""
    try:
        payload = await request.json()
        event_type = payload.get("event_type")
        
        logger.info(f"Received HeyGen webhook: {event_type}")
        
        if event_type == "video.completed":
            video_id = payload.get("video_id")
            video_url = payload.get("video_url")
            logger.info(f"Video generation completed: {video_id}")
            
            # Handle completed video generation
            # Could notify connected clients via WebSocket
            
        elif event_type == "avatar.created":
            avatar_id = payload.get("avatar_id")
            avatar_name = payload.get("avatar_name")
            logger.info(f"Avatar created: {avatar_name} -> {avatar_id}")
            
            # Handle new avatar creation
            
        return {"status": "success", "processed": event_type}
        
    except Exception as e:
        logger.error(f"Error processing HeyGen webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mcp_router.get("/health")
async def webhook_health():
    """Health check endpoint for MCP webhooks"""
    return {"status": "healthy", "service": "mcp_webhooks"}

# MCP Integration Status
mcp_status = {
    "cartesia": {"connected": False, "last_event": None},
    "heygen": {"connected": False, "last_event": None},
    "browser_tools": {"connected": False, "last_event": None}
}

@mcp_router.get("/status")
async def get_mcp_status():
    """Get MCP integration status"""
    return mcp_status

def update_mcp_status(server: str, connected: bool, event: str = None):
    """Update MCP server status"""
    if server in mcp_status:
        mcp_status[server]["connected"] = connected
        if event:
            mcp_status[server]["last_event"] = event
