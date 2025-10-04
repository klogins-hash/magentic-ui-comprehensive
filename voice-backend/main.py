#!/usr/bin/env python3
"""
Magentic Voice Backend - Groq-Only Pipeline
iPhone app backend with voice and text support
"""

import os
import asyncio
import json
import base64
import tempfile
from datetime import datetime
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import MCP webhook handler
from mcp_webhook_handler import mcp_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Groq client
from groq import Groq
from pydantic import BaseModel
from typing import Optional

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class VoiceMessage(BaseModel):
    type: str  # "voice" or "text"
    content: str
    timestamp: Optional[str] = None
    user_id: Optional[str] = "frank"

class TaskDelegation(BaseModel):
    description: str
    priority: str = "normal"
    user_id: str = "frank"

class MagenticVoiceBackend:
    """Groq-only voice backend for iPhone app"""
    
    def __init__(self):
        self.groq_client = groq_client
        self.autogen_base_url = "http://magentic-ui:8081"  # Connect to existing Magentic-UI
        self.active_tasks = {}
        
        # Groq model configurations
        self.stt_model = "whisper-large-v3"
        self.llm_model = "llama-3.3-70b-versatile"
        self.tts_model = "playai-tts"
        self.tts_voice = "Fritz-PlayAI"
        
        logger.info("🚀 Magentic Voice Backend initialized with Groq-only pipeline")
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Convert speech to text using Groq Whisper"""
        try:
            # Create a temporary file for audio data
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe with Groq Whisper
            with open(temp_file_path, "rb") as audio_file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.stt_model,
                    language="en"
                )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            return transcription.text.strip()
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""
    
    async def process_with_llm(self, message: str) -> tuple[str, bool]:
        """Process message with Groq LLM and determine if delegation needed"""
        try:
            system_prompt = """You are Frank's personal AI integrator. You help him manage tasks and delegate work to his AutoGen team.

DELEGATION RULES:
- If Frank asks you to CREATE, GENERATE, MAKE, BUILD, DESIGN, ANALYZE, RESEARCH, WRITE, DEVELOP, or AUTOMATE something complex, respond with: "DELEGATE: [task description]"
- For simple questions, status checks, or casual conversation, respond directly
- Keep all responses brief and actionable
- Be friendly but professional

Examples:
- "Create a video about our product" → "DELEGATE: Create a video about our product"
- "How's my team doing?" → "Let me check your team status for you"
- "What time is it?" → "It's [current time]"
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            response = self.groq_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.1,
                max_tokens=150
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Check if delegation is needed
            needs_delegation = response_text.startswith("DELEGATE:")
            if needs_delegation:
                task_description = response_text.replace("DELEGATE:", "").strip()
                return task_description, True
            else:
                return response_text, False
                
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "Sorry, I had trouble processing that. Please try again.", False
    
    async def synthesize_speech(self, text: str) -> bytes:
        """Convert text to speech using Groq TTS"""
        try:
            response = self.groq_client.audio.speech.create(
                model=self.tts_model,
                voice=self.tts_voice,
                input=text,
                response_format="wav"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""
    
    async def delegate_to_autogen(self, task_description: str) -> str:
        """Delegate task to existing AutoGen team"""
        try:
            async with httpx.AsyncClient() as client:
                # Try to connect to existing Magentic-UI
                response = await client.post(
                    f"{self.autogen_base_url}/api/chat",
                    json={
                        "message": task_description,
                        "conversation_id": f"voice_task_{datetime.now().timestamp()}"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = f"task_{datetime.now().timestamp()}"
                    self.active_tasks[task_id] = {
                        "description": task_description,
                        "status": "delegated",
                        "created_at": datetime.now().isoformat()
                    }
                    return f"I've assigned that to your AutoGen team. Task ID: {task_id}"
                else:
                    return "I had trouble connecting to your AutoGen team. They might be busy."
                    
        except Exception as e:
            logger.error(f"AutoGen delegation error: {e}")
            return "I couldn't reach your AutoGen team right now. Please try again later."
    
    async def process_message(self, message: str, is_voice: bool = True) -> Dict[str, Any]:
        """Main message processing pipeline"""
        logger.info(f"Processing {'voice' if is_voice else 'text'} message: {message[:50]}...")
        
        # Process with LLM
        response_text, needs_delegation = await self.process_with_llm(message)
        
        if needs_delegation:
            # Delegate to AutoGen team
            delegation_response = await self.delegate_to_autogen(response_text)
            final_response = delegation_response
        else:
            final_response = response_text
        
        # Prepare response
        result = {
            "type": "text",
            "content": final_response,
            "timestamp": datetime.now().isoformat(),
            "needs_delegation": needs_delegation
        }
        
        # Add audio if voice mode
        if is_voice:
            audio_data = await self.synthesize_speech(final_response)
            if audio_data:
                import base64
                result["audio"] = base64.b64encode(audio_data).decode()
                result["type"] = "voice"
        
        return result
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of delegated task"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        else:
            return {"error": "Task not found"}

# Initialize backend
backend = MagenticVoiceBackend()

# FastAPI app
app = FastAPI(title="Magentic Voice Backend", version="1.0.0")

# CORS for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your iOS app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Magentic Voice Backend",
        "groq_models": {
            "stt": backend.stt_model,
            "llm": backend.llm_model,
            "tts": backend.tts_model
        }
    }

@app.post("/api/text")
async def process_text_message(message: VoiceMessage):
    """Process text message from iOS app"""
    try:
        result = await backend.process_message(message.content, is_voice=False)
        return result
    except Exception as e:
        logger.error(f"Text processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice")
async def process_voice_message(message: VoiceMessage):
    """Process voice message from iOS app"""
    try:
        result = await backend.process_message(message.content, is_voice=True)
        return result
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a delegated task"""
    return backend.get_task_status(task_id)

@app.get("/api/tasks")
async def list_tasks():
    """List all active tasks"""
    return {"tasks": backend.active_tasks}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication with iOS app"""
    await websocket.accept()
    logger.info("iOS app connected via WebSocket")
    
    try:
        while True:
            # Receive message from iOS app
            data = await websocket.receive_json()
            
            message_type = data.get("type", "text")
            content = data.get("content", "")
            
            if message_type == "voice":
                # Handle voice message
                result = await backend.process_message(content, is_voice=True)
            elif message_type == "text":
                # Handle text message
                result = await backend.process_message(content, is_voice=False)
            elif message_type == "ping":
                # Handle ping for connection health
                result = {"type": "pong", "timestamp": datetime.now().isoformat()}
            else:
                result = {"type": "error", "content": "Unknown message type"}
            
            # Send response back to iOS app
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        logger.info("iOS app disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY environment variable is required")
        exit(1)
    
    logger.info("🎤 Starting Magentic Voice Backend...")
    logger.info(f"📱 iOS app can connect to: ws://localhost:8000/ws")
    logger.info(f"🔧 AutoGen team URL: {backend.autogen_base_url}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
