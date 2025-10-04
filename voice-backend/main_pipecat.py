#!/usr/bin/env python3
"""
Magentic Voice Backend - Pipecat + Groq Pipeline
Real voice processing with Pipecat framework
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import (
    AudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    EndFrame,
    StartFrame
)
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.groq import GroqSTTService, GroqLLMService, GroqTTSService
from pipecat.transports.websocket import WebsocketTransport
from pipecat.vad.silero import SileroVADAnalyzer

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoGenDelegationProcessor(FrameProcessor):
    """Custom processor to handle AutoGen delegation"""
    
    def __init__(self, autogen_url: str = "http://magentic-ui:8081"):
        super().__init__()
        self.autogen_url = autogen_url
        self.active_tasks = {}
    
    async def process_frame(self, frame, direction: FrameDirection):
        """Process frames and handle delegation logic"""
        
        if isinstance(frame, TextFrame):
            text = frame.text.lower()
            
            # Check if this needs delegation to AutoGen
            delegation_keywords = [
                'create', 'generate', 'make', 'build', 'design',
                'analyze', 'research', 'write', 'develop', 'automate'
            ]
            
            needs_delegation = any(keyword in text for keyword in delegation_keywords)
            
            if needs_delegation:
                # Delegate to AutoGen team
                task_id = await self.delegate_to_autogen(frame.text)
                response_text = f"I've assigned that to your AutoGen team. Task ID: {task_id}"
                
                # Create response frame
                response_frame = TextFrame(response_text)
                await self.push_frame(response_frame, direction)
                return
        
        # Pass through other frames
        await self.push_frame(frame, direction)
    
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

class MagenticVoicePipeline:
    """Main Pipecat pipeline for voice processing"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Initialize services
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
        
        # Custom processors
        self.delegation_processor = AutoGenDelegationProcessor()
        
        # VAD for voice activity detection
        self.vad = SileroVADAnalyzer()
        
        logger.info("🚀 Pipecat pipeline initialized with Groq services")
    
    async def create_pipeline(self, transport) -> Pipeline:
        """Create the main processing pipeline"""
        
        # LLM context for conversation management
        context = OpenAILLMContext(
            messages=[
                {
                    "role": "system", 
                    "content": """You are Frank's personal AI integrator. You help him manage tasks and delegate work to his AutoGen team.

Keep responses brief and actionable. Be friendly but professional.

For simple questions, status checks, or casual conversation, respond directly.
For complex tasks that need creation, generation, analysis, or automation, the delegation processor will handle routing to the AutoGen team."""
                }
            ]
        )
        
        # Create pipeline with proper ordering
        pipeline = Pipeline([
            transport.input(),           # Audio input from WebSocket
            self.vad,                   # Voice activity detection
            self.stt_service,           # Speech to text
            context,                    # Conversation context
            self.llm_service,           # Language model processing
            self.delegation_processor,   # AutoGen delegation logic
            self.tts_service,           # Text to speech
            transport.output(),         # Audio output to WebSocket
        ])
        
        return pipeline
    
    async def run_pipeline(self, websocket: WebSocket):
        """Run the pipeline for a WebSocket connection"""
        try:
            # Create WebSocket transport
            transport = WebsocketTransport(websocket)
            
            # Create pipeline
            pipeline = await self.create_pipeline(transport)
            
            # Create and run task
            task = PipelineTask(pipeline, PipelineParams())
            runner = PipelineRunner()
            
            logger.info("🎤 Starting voice pipeline for client")
            await runner.run(task)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise

# FastAPI app for HTTP endpoints and WebSocket
app = FastAPI(title="Magentic Voice Backend - Pipecat", version="1.0.0")

# CORS for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
voice_pipeline = None

@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    global voice_pipeline
    try:
        voice_pipeline = MagenticVoicePipeline()
        logger.info("✅ Pipecat voice pipeline ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipeline: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Magentic Voice Backend - Pipecat",
        "framework": "pipecat-ai",
        "groq_models": {
            "stt": "whisper-large-v3",
            "llm": "llama-3.3-70b-versatile",
            "tts": "playai-tts"
        },
        "features": [
            "Real-time voice processing",
            "AutoGen delegation",
            "Voice activity detection",
            "WebSocket transport"
        ]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for voice processing"""
    await websocket.accept()
    logger.info("📱 iOS app connected via WebSocket")
    
    try:
        if voice_pipeline:
            await voice_pipeline.run_pipeline(websocket)
        else:
            logger.error("Voice pipeline not initialized")
            await websocket.close(code=1011, reason="Pipeline not ready")
            
    except WebSocketDisconnect:
        logger.info("📱 iOS app disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=f"Error: {str(e)}")

@app.get("/api/status")
async def get_status():
    """Get pipeline status"""
    return {
        "pipeline_ready": voice_pipeline is not None,
        "active_connections": 0,  # Could track this
        "uptime": "running",
        "services": {
            "stt": "groq-whisper",
            "llm": "groq-llama",
            "tts": "groq-playai",
            "vad": "silero"
        }
    }

@app.get("/api/tasks")
async def get_tasks():
    """Get active AutoGen tasks"""
    if voice_pipeline and voice_pipeline.delegation_processor:
        return {"tasks": voice_pipeline.delegation_processor.active_tasks}
    return {"tasks": {}}

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY environment variable is required")
        exit(1)
    
    logger.info("🎤 Starting Magentic Voice Backend with Pipecat...")
    logger.info("📱 iOS app can connect to: ws://localhost:8000/ws")
    logger.info("🔧 AutoGen team URL: http://magentic-ui:8081")
    
    uvicorn.run(
        "main_pipecat:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
