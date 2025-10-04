#!/usr/bin/env python3
"""
Proper Pipecat Voice Backend for Magentic-UI
Real-time voice processing with WebRTC transport and Groq pipeline
"""

import asyncio
import os
import logging
from typing import Dict, Any
from datetime import datetime

# Pipecat imports
from pipecat.frames.frames import (
    Frame,
    AudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.groq import GroqSTTService, GroqLLMService, GroqTTSService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transports.services.helpers.daily_rest import DailyRESTHelper, DailyRoomObject
from pipecat.vad.silero import SileroVADAnalyzer
from pipecat.processors.frameworks.rtvi import RTVIProcessor, RTVIConfig
from pipecat.utils.utils import exp_smoothing

# Additional imports
import httpx
from loguru import logger

# Configure logging
logging.basicConfig(level=logging.INFO)

class MagenticVoiceBot:
    """Pipecat-powered voice bot for Magentic-UI integration"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.daily_api_key = os.getenv("DAILY_API_KEY") 
        self.autogen_base_url = os.getenv("AUTOGEN_BASE_URL", "http://magentic-core:8081")
        self.active_tasks = {}
        
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        logger.info("🚀 Initializing Magentic Voice Bot with Pipecat")
    
    def create_ai_services(self):
        """Create AI services for the pipeline"""
        
        # Speech-to-Text with Groq Whisper
        stt = GroqSTTService(
            api_key=self.groq_api_key,
            model="whisper-large-v3",
            language="en"
        )
        
        # Language Model with Groq
        llm = GroqLLMService(
            api_key=self.groq_api_key,
            model="llama-3.3-70b-versatile",
            params=GroqLLMService.InputParams(
                temperature=0.1,
                max_tokens=150,
                top_p=0.9
            )
        )
        
        # Text-to-Speech with Groq (fallback to system if not available)
        try:
            tts = GroqTTSService(
                api_key=self.groq_api_key,
                voice="alloy"  # Groq TTS voice
            )
        except Exception as e:
            logger.warning(f"Groq TTS not available, using system TTS: {e}")
            # Fallback to a different TTS service if needed
            from pipecat.services.openai import OpenAITTSService
            tts = OpenAITTSService(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                voice="alloy"
            )
        
        return stt, llm, tts
    
    def create_context_and_messages(self):
        """Create conversation context with system message"""
        
        system_message = """You are Frank's personal AI integrator for Magentic-UI. You help him manage tasks and delegate work to his AutoGen team.

DELEGATION RULES:
- If Frank asks you to CREATE, GENERATE, MAKE, BUILD, DESIGN, ANALYZE, RESEARCH, WRITE, DEVELOP, or AUTOMATE something complex, respond with: "DELEGATE: [task description]"
- For simple questions, status checks, or casual conversation, respond directly
- Keep all responses brief and actionable (under 50 words)
- Be friendly but professional
- Always acknowledge when you're delegating tasks

Examples:
- "Create a video about our product" → "DELEGATE: Create a video about our product"
- "How's my team doing?" → "Let me check your team status for you"
- "What time is it?" → "It's [current time]"
- "Build me a website" → "DELEGATE: Build a website with the specified requirements"
"""
        
        messages = [
            {
                "role": "system", 
                "content": system_message
            }
        ]
        
        context = OpenAILLMContext(messages)
        return context
    
    async def delegate_to_autogen(self, task_description: str) -> str:
        """Delegate task to AutoGen team via HTTP API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.autogen_base_url}/api/chat",
                    json={
                        "message": task_description,
                        "conversation_id": f"voice_task_{datetime.now().timestamp()}",
                        "source": "voice_backend"
                    }
                )
                
                if response.status_code == 200:
                    task_id = f"task_{datetime.now().timestamp()}"
                    self.active_tasks[task_id] = {
                        "description": task_description,
                        "status": "delegated",
                        "created_at": datetime.now().isoformat()
                    }
                    logger.info(f"Task delegated to AutoGen: {task_id}")
                    return f"I've assigned that to your AutoGen team. Task ID: {task_id}"
                else:
                    logger.warning(f"AutoGen delegation failed: {response.status_code}")
                    return "I had trouble connecting to your AutoGen team. They might be busy."
                    
        except Exception as e:
            logger.error(f"AutoGen delegation error: {e}")
            return "I couldn't reach your AutoGen team right now. Please try again later."
    
    async def process_llm_response(self, frame: Frame, context: OpenAILLMContext):
        """Process LLM response and handle delegation"""
        if isinstance(frame, TextFrame):
            response_text = frame.text.strip()
            
            # Check if delegation is needed
            if response_text.startswith("DELEGATE:"):
                task_description = response_text.replace("DELEGATE:", "").strip()
                delegation_response = await self.delegate_to_autogen(task_description)
                
                # Replace the frame content with delegation response
                frame.text = delegation_response
                logger.info(f"Delegated task: {task_description}")
        
        return frame
    
    async def create_transport(self, room_url: str = None):
        """Create Daily transport for WebRTC communication"""
        
        if room_url:
            # Use provided room URL
            transport = DailyTransport(
                room_url=room_url,
                token=None,  # Add token if needed
                bot_name="Magentic Voice Bot",
                params=DailyParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    vad_enabled=True,
                    vad_analyzer=SileroVADAnalyzer(),
                    vad_audio_passthrough=True
                )
            )
        else:
            # Create a new room if Daily API key is available
            if self.daily_api_key:
                daily_rest_helper = DailyRESTHelper(self.daily_api_key)
                room: DailyRoomObject = await daily_rest_helper.create_room()
                room_url = room.url
                
                transport = DailyTransport(
                    room_url=room_url,
                    token=None,
                    bot_name="Magentic Voice Bot",
                    params=DailyParams(
                        audio_in_enabled=True,
                        audio_out_enabled=True,
                        vad_enabled=True,
                        vad_analyzer=SileroVADAnalyzer(),
                        vad_audio_passthrough=True
                    )
                )
                
                logger.info(f"Created Daily room: {room_url}")
            else:
                # Fallback to WebSocket transport for development
                logger.warning("No DAILY_API_KEY provided, using WebSocket transport")
                from pipecat.transports.services.websocket import WebsocketServerTransport
                transport = WebsocketServerTransport(
                    params=WebsocketServerTransport.InputParams(
                        audio_in_enabled=True,
                        audio_out_enabled=True,
                        add_wav_header=True,
                        vad_enabled=True,
                        vad_analyzer=SileroVADAnalyzer(),
                        vad_audio_passthrough=True
                    ),
                    host="0.0.0.0",
                    port=8765
                )
        
        return transport
    
    async def run_bot(self, room_url: str = None):
        """Main bot execution function"""
        
        # Create AI services
        stt, llm, tts = self.create_ai_services()
        
        # Create context
        context = self.create_context_and_messages()
        context_aggregator = llm.create_context_aggregator(context)
        
        # Create transport
        transport = await self.create_transport(room_url)
        
        # Create RTVI processor for client communication
        rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
        
        # Create pipeline
        pipeline = Pipeline([
            transport.input(),              # Audio input from client
            rtvi,                          # RTVI protocol handling
            stt,                           # Speech-to-text
            context_aggregator.user(),     # Add user message to context
            llm,                           # Language model processing
            context_aggregator.assistant(), # Add assistant response to context
            tts,                           # Text-to-speech
            transport.output()             # Audio output to client
        ])
        
        # Create task with event handlers
        task = PipelineTask(
            pipeline,
            params=PipelineTask.PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True
            )
        )
        
        # Event handlers
        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            logger.info(f"First participant joined: {participant}")
            # Send greeting
            await task.queue_frames([
                TextFrame("Hello! I'm your Magentic AI assistant. How can I help you today?")
            ])
        
        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"Participant left: {participant}, reason: {reason}")
            await task.queue_frames([TextFrame("Goodbye!")])
        
        @transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            logger.info(f"Call state updated: {state}")
        
        # Start the pipeline
        runner = PipelineRunner()
        
        logger.info("🎤 Magentic Voice Bot is ready!")
        if hasattr(transport, 'room_url'):
            logger.info(f"🌐 Room URL: {transport.room_url}")
        elif hasattr(transport, 'port'):
            logger.info(f"🌐 WebSocket server: ws://localhost:{transport.port}")
        
        await runner.run(task)

async def main():
    """Main entry point"""
    
    # Check environment variables
    required_vars = ["GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # Create and run bot
    bot = MagenticVoiceBot()
    
    # Get room URL from environment or command line
    room_url = os.getenv("DAILY_ROOM_URL")
    
    try:
        await bot.run_bot(room_url)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
