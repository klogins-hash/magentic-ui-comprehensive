#!/usr/bin/env python3
"""
Magentic Voice Backend - Simple Pipecat Implementation
Minimal working version with Groq services
"""

import os
import logging
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MagenticVoiceBackend:
    """Simplified voice backend with Pipecat integration"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Import Groq services
        try:
            from pipecat.services.groq.llm import GroqLLMService
            from pipecat.services.groq.stt import GroqSTTService  
            from pipecat.services.groq.tts import GroqTTSService
            
            self.stt_service = GroqSTTService(
                model="whisper-large-v3",
                api_key=self.groq_api_key
            )
            
            self.llm_service = GroqLLMService(
                model="llama-3.3-70b-versatile",
                api_key=self.groq_api_key
            )
            
            self.tts_service = GroqTTSService(
                model="playai-tts",
                voice="Fritz-PlayAI",
                api_key=self.groq_api_key
            )
            
            logger.info("🚀 Pipecat services initialized successfully")
            self.pipecat_available = True
            
        except ImportError as e:
            logger.warning(f"⚠️ Pipecat services not available: {e}")
            logger.info("📝 Falling back to basic text processing")
            self.pipecat_available = False
        
        self.autogen_url = "http://magentic-ui:8081"
        self.active_tasks = {}
    
    async def process_text_message(self, message: str) -> dict:
        """Process text message with delegation logic"""
        
        # Check if this needs delegation to AutoGen
        delegation_keywords = [
            'create', 'generate', 'make', 'build', 'design',
            'analyze', 'research', 'write', 'develop', 'automate'
        ]
        
        needs_delegation = any(keyword in message.lower() for keyword in delegation_keywords)
        
        if needs_delegation:
            # Delegate to AutoGen team
            task_id = await self.delegate_to_autogen(message)
            response_text = f"I've assigned '{message}' to your AutoGen team. Task ID: {task_id}"
        else:
            # Direct response
            if self.pipecat_available:
                # Use Pipecat LLM service if available
                try:
                    # For now, simple response - full pipeline integration later
                    response_text = f"Hello! You said: {message}. How can I help you today?"
                except Exception as e:
                    logger.error(f"Pipecat LLM error: {e}")
                    response_text = f"Hello! You said: {message}. How can I help you today?"
            else:
                response_text = f"Hello! You said: {message}. How can I help you today?"
        
        return {
            "type": "text",
            "content": response_text,
            "timestamp": datetime.now().isoformat(),
            "needs_delegation": needs_delegation,
            "pipecat_enabled": self.pipecat_available
        }
    
    async def delegate_to_autogen(self, task_description: str) -> str:
        """Delegate task to AutoGen team"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.autogen_url}/api/chat",
                    json={
                        "message": task_description,
                        "conversation_id": f"voice_task_{datetime.now().timestamp()}"
                    },
                    timeout=30.0
                )
                
                task_id = f"task_{datetime.now().timestamp()}"
                self.active_tasks[task_id] = {
                    "description": task_description,
                    "status": "delegated",
                    "created_at": datetime.now().isoformat()
                }
                return task_id
                
        except Exception as e:
            logger.error(f"AutoGen delegation error: {e}")
            return "error_connecting_to_team"
    
    async def process_voice_message(self, audio_data: bytes) -> dict:
        """Process voice message (placeholder for full implementation)"""
        
        if not self.pipecat_available:
            return {
                "type": "text",
                "content": "Voice processing requires Pipecat services. Please use text mode.",
                "timestamp": datetime.now().isoformat(),
                "error": "pipecat_not_available"
            }
        
        try:
            # TODO: Implement full voice pipeline
            # For now, return placeholder
            return {
                "type": "text",
                "content": "Voice processing is being implemented. Please use text mode for now.",
                "timestamp": datetime.now().isoformat(),
                "status": "voice_pipeline_in_development"
            }
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            return {
                "type": "text",
                "content": "Voice processing encountered an error. Please try again.",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# FastAPI app
app = FastAPI(title="Magentic Voice Backend - Pipecat Simple", version="1.0.0")

# CORS for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global backend instance
voice_backend = None

@app.on_event("startup")
async def startup_event():
    """Initialize backend on startup"""
    global voice_backend
    try:
        voice_backend = MagenticVoiceBackend()
        logger.info("✅ Magentic Voice Backend ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize backend: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Magentic Voice Backend - Pipecat Simple",
        "framework": "pipecat-ai",
        "version": "0.0.87",
        "pipecat_available": voice_backend.pipecat_available if voice_backend else False,
        "groq_models": {
            "stt": "whisper-large-v3",
            "llm": "llama-3.3-70b-versatile",
            "tts": "playai-tts"
        },
        "features": [
            "Text processing",
            "AutoGen delegation",
            "WebSocket transport",
            "Voice processing (in development)"
        ]
    }

@app.post("/api/text")
async def process_text(data: dict):
    """Process text message"""
    if not voice_backend:
        return {"error": "Backend not initialized"}
    
    message = data.get("content", "")
    return await voice_backend.process_text_message(message)

@app.get("/api/tasks")
async def get_tasks():
    """Get active AutoGen tasks"""
    if voice_backend:
        return {"tasks": voice_backend.active_tasks}
    return {"tasks": {}}

@app.get("/api/status")
async def get_status():
    """Get backend status"""
    return {
        "backend_ready": voice_backend is not None,
        "pipecat_available": voice_backend.pipecat_available if voice_backend else False,
        "active_tasks": len(voice_backend.active_tasks) if voice_backend else 0,
        "services": {
            "stt": "groq-whisper" if voice_backend and voice_backend.pipecat_available else "not_available",
            "llm": "groq-llama" if voice_backend and voice_backend.pipecat_available else "basic",
            "tts": "groq-playai" if voice_backend and voice_backend.pipecat_available else "not_available"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    logger.info("📱 iOS app connected via WebSocket")
    
    try:
        while True:
            # Receive message from iOS app
            data = await websocket.receive_json()
            
            message_type = data.get("type", "text")
            content = data.get("content", "")
            
            if message_type == "ping":
                # Handle ping for connection health
                response = {"type": "pong", "timestamp": datetime.now().isoformat()}
            elif message_type == "text":
                # Handle text message
                response = await voice_backend.process_text_message(content)
            elif message_type == "voice":
                # Handle voice message (placeholder)
                response = await voice_backend.process_voice_message(b"")  # Placeholder
            else:
                response = {"type": "error", "content": "Unknown message type"}
            
            # Send response back to iOS app
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        logger.info("📱 iOS app disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY environment variable is required")
        exit(1)
    
    logger.info("🎤 Starting Magentic Voice Backend with Pipecat...")
    logger.info("📱 iOS app can connect to: ws://localhost:8000/ws")
    logger.info("🔧 AutoGen team URL: http://magentic-ui:8081")
    
    uvicorn.run(
        "main_pipecat_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
