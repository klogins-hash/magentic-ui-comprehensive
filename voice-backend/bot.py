#!/usr/bin/env python3
"""
Magentic-UI Voice Bot using Pipecat Framework
Based on official Pipecat quickstart with Groq integration
"""

import asyncio
import os
import logging
from typing import Optional

# Pipecat core imports
from pipecat.frames.frames import TextFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame
)
from pipecat.services.groq import GroqSTTService, GroqLLMService, GroqTTSService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transports.services.helpers.daily_rest import DailyRESTHelper
from pipecat.vad.silero import SileroVADAnalyzer
from pipecat.processors.frameworks.rtvi import RTVIProcessor, RTVIConfig

# Additional imports
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MagenticBot:
    """Magentic-UI Voice Bot with AutoGen integration"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.daily_api_key = os.getenv("DAILY_API_KEY")
        self.autogen_base_url = os.getenv("AUTOGEN_BASE_URL", "http://magentic-core:8081")
        
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        logger.info("🚀 Initializing Magentic Voice Bot")

async def run_bot(room_url: Optional[str] = None):
    """Main bot function following Pipecat patterns"""
    
    # Create AI Services
    stt = GroqSTTService(
        api_key=os.getenv("GROQ_API_KEY"),
        model="whisper-large-v3"
    )
    
    llm = GroqLLMService(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile"
    )
    
    # Use Groq TTS if available, fallback to system TTS
    try:
        tts = GroqTTSService(
            api_key=os.getenv("GROQ_API_KEY"),
            voice="alloy"
        )
    except Exception as e:
        logger.warning(f"Groq TTS not available: {e}")
        # Fallback to a basic TTS
        from pipecat.services.openai import OpenAITTSService
        tts = OpenAITTSService(
            api_key=os.getenv("OPENAI_API_KEY", "dummy"),
            voice="alloy"
        )
    
    # Create conversation context
    messages = [
        {
            "role": "system",
            "content": """You are Frank's personal AI integrator for Magentic-UI. You help him manage tasks and delegate work to his AutoGen team.

DELEGATION RULES:
- If Frank asks you to CREATE, GENERATE, MAKE, BUILD, DESIGN, ANALYZE, RESEARCH, WRITE, DEVELOP, or AUTOMATE something complex, respond with: "DELEGATE: [task description]"
- For simple questions, status checks, or casual conversation, respond directly
- Keep all responses brief and actionable (under 50 words)
- Be friendly but professional

Examples:
- "Create a video about our product" → "DELEGATE: Create a video about our product"
- "How's my team doing?" → "Let me check your team status for you"
- "What time is it?" → "It's [current time]"
"""
        }
    ]
    
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)
    
    # Create transport
    if room_url:
        # Use provided Daily room URL
        transport = DailyTransport(
            room_url=room_url,
            token=None,
            bot_name="Magentic Voice Bot",
            params=DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            )
        )
    else:
        # Create new Daily room if API key available
        if os.getenv("DAILY_API_KEY"):
            daily_rest_helper = DailyRESTHelper(os.getenv("DAILY_API_KEY"))
            room = await daily_rest_helper.create_room()
            
            transport = DailyTransport(
                room_url=room.url,
                token=None,
                bot_name="Magentic Voice Bot",
                params=DailyParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    vad_enabled=True,
                    vad_analyzer=SileroVADAnalyzer(),
                )
            )
            
            logger.info(f"Created Daily room: {room.url}")
        else:
            # Fallback to WebSocket for development
            logger.warning("No DAILY_API_KEY provided, using WebSocket transport")
            from pipecat.transports.services.websocket import WebsocketServerTransport
            
            transport = WebsocketServerTransport(
                params=WebsocketServerTransport.InputParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    add_wav_header=True,
                    vad_enabled=True,
                    vad_analyzer=SileroVADAnalyzer(),
                ),
                host="0.0.0.0",
                port=8765
            )
            
            logger.info("WebSocket server will start on ws://localhost:8765")
    
    # Create RTVI processor
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
    
    # Create pipeline
    pipeline = Pipeline([
        transport.input(),              # Audio input
        rtvi,                          # RTVI protocol
        stt,                           # Speech-to-text
        context_aggregator.user(),     # Add user message to context
        llm,                           # Language model
        context_aggregator.assistant(), # Add assistant response to context
        tts,                           # Text-to-speech
        transport.output()             # Audio output
    ])
    
    # Create task
    task = PipelineTask(
        pipeline,
        params=PipelineTask.PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
        )
    )
    
    # Event handlers
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        logger.info(f"Participant joined: {participant}")
        # Send greeting
        await task.queue_frames([
            TextFrame("Hello! I'm your Magentic AI assistant. How can I help you today?")
        ])
    
    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        logger.info(f"Participant left: {participant}")
        await task.queue_frames([TextFrame("Goodbye!")])
    
    # Run the pipeline
    runner = PipelineRunner()
    
    logger.info("🎤 Magentic Voice Bot is ready!")
    if hasattr(transport, 'room_url'):
        logger.info(f"🌐 Daily room: {transport.room_url}")
    else:
        logger.info("🌐 WebSocket server: ws://localhost:8765")
    
    await runner.run(task)

async def main():
    """Main entry point"""
    
    # Check required environment variables
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY environment variable is required")
        return
    
    # Get room URL from environment
    room_url = os.getenv("DAILY_ROOM_URL")
    
    try:
        await run_bot(room_url)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
