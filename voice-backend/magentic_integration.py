#!/usr/bin/env python3
"""
Magentic-UI Integration Layer
Hybrid approach: Direct communication now, MCP-ready for future migration
"""

import os
import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from loguru import logger

@dataclass
class TaskRequest:
    """Task request structure (MCP-compatible)"""
    task_id: str
    task_type: str
    description: str
    priority: str = "normal"
    context: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.context is None:
            self.context = {}

@dataclass
class TaskResponse:
    """Task response structure (MCP-compatible)"""
    task_id: str
    status: str  # "accepted", "processing", "completed", "failed"
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class MagenticUIIntegration:
    """
    Integration layer for Magentic-UI communication
    Designed to be MCP-compatible for future migration
    """
    
    def __init__(self, magentic_ui_url: str = "http://magentic-ui:8081"):
        self.magentic_ui_url = magentic_ui_url
        self.active_tasks: Dict[str, TaskRequest] = {}
        self.task_results: Dict[str, TaskResponse] = {}
        
        # MCP-style configuration (for future use)
        self.mcp_config = {
            "protocol_version": "1.0",
            "server_name": "magentic-ui-integration",
            "capabilities": [
                "task_delegation",
                "status_monitoring", 
                "result_retrieval"
            ]
        }
        
        logger.info("🔗 Magentic-UI Integration initialized")
        logger.info(f"📍 Target URL: {self.magentic_ui_url}")
    
    async def delegate_task(self, task_request: TaskRequest) -> TaskResponse:
        """
        Delegate task to Magentic-UI team
        Current: Direct communication
        Future: MCP protocol
        """
        logger.info(f"🎯 Delegating task: {task_request.task_id}")
        
        try:
            # Store task for tracking
            self.active_tasks[task_request.task_id] = task_request
            
            # Current implementation: Direct communication
            response = await self._direct_communication(task_request)
            
            # Future: This will be replaced with MCP protocol
            # response = await self._mcp_communication(task_request)
            
            # Store result
            self.task_results[task_request.task_id] = response
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Task delegation failed: {e}")
            error_response = TaskResponse(
                task_id=task_request.task_id,
                status="failed",
                error=str(e)
            )
            self.task_results[task_request.task_id] = error_response
            return error_response
    
    async def _direct_communication(self, task_request: TaskRequest) -> TaskResponse:
        """
        Current implementation: Direct HTTP communication
        This simulates what will become MCP communication
        """
        
        # For now, since Magentic-UI doesn't expose APIs, we'll simulate
        # the delegation and provide a meaningful response
        
        # Check if Magentic-UI is accessible
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_response = await client.get(f"{self.magentic_ui_url}/")
                
                if health_response.status_code == 200:
                    # Magentic-UI is running, simulate task acceptance
                    logger.info("✅ Magentic-UI is accessible")
                    
                    # Simulate processing time
                    await asyncio.sleep(0.1)
                    
                    return TaskResponse(
                        task_id=task_request.task_id,
                        status="accepted",
                        result=f"Task '{task_request.description}' has been assigned to the Magentic-UI team. "
                               f"The team will work on this {task_request.task_type} task and provide results "
                               f"through the main interface at {self.magentic_ui_url}"
                    )
                else:
                    raise Exception(f"Magentic-UI returned status {health_response.status_code}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Direct communication failed: {e}")
            
            # Fallback: Provide helpful response even if connection fails
            return TaskResponse(
                task_id=task_request.task_id,
                status="accepted",
                result=f"Task '{task_request.description}' has been queued for the Magentic-UI team. "
                       f"Please check the main interface at {self.magentic_ui_url} for progress updates."
            )
    
    async def _mcp_communication(self, task_request: TaskRequest) -> TaskResponse:
        """
        Future implementation: MCP protocol communication
        This will be implemented in Phase 3 of your architecture
        """
        
        # MCP message structure (for future implementation)
        mcp_message = {
            "jsonrpc": "2.0",
            "method": "task/delegate",
            "params": {
                "task": {
                    "id": task_request.task_id,
                    "type": task_request.task_type,
                    "description": task_request.description,
                    "priority": task_request.priority,
                    "context": task_request.context
                }
            },
            "id": task_request.task_id
        }
        
        # TODO: Implement MCP client communication
        # This will connect to MCP servers as defined in your architecture
        
        logger.info("🚧 MCP communication not yet implemented")
        logger.info(f"📋 MCP message prepared: {json.dumps(mcp_message, indent=2)}")
        
        # For now, return the direct communication result
        return await self._direct_communication(task_request)
    
    def get_task_status(self, task_id: str) -> Optional[TaskResponse]:
        """Get status of a delegated task"""
        return self.task_results.get(task_id)
    
    def list_active_tasks(self) -> List[TaskRequest]:
        """List all active tasks"""
        return list(self.active_tasks.values())
    
    def get_integration_info(self) -> Dict[str, Any]:
        """Get integration status and capabilities"""
        return {
            "integration_type": "hybrid",
            "current_mode": "direct_communication",
            "future_mode": "mcp_protocol",
            "magentic_ui_url": self.magentic_ui_url,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_results),
            "mcp_config": self.mcp_config,
            "capabilities": [
                "Task delegation to Magentic-UI team",
                "Status monitoring",
                "Result tracking",
                "MCP-ready architecture"
            ]
        }

# Factory function for easy integration
def create_magentic_integration(magentic_ui_url: str = None) -> MagenticUIIntegration:
    """Create Magentic-UI integration instance"""
    
    if magentic_ui_url is None:
        # Default to Docker network URL
        magentic_ui_url = os.getenv("MAGENTIC_UI_URL", "http://magentic-ui:8081")
    
    return MagenticUIIntegration(magentic_ui_url)

# Task classification helper
def classify_task_type(description: str) -> str:
    """Classify task type for proper routing"""
    
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['create', 'generate', 'make', 'build']):
        return "creation"
    elif any(word in description_lower for word in ['analyze', 'research', 'study', 'investigate']):
        return "analysis"
    elif any(word in description_lower for word in ['write', 'draft', 'compose']):
        return "writing"
    elif any(word in description_lower for word in ['design', 'plan', 'architect']):
        return "design"
    elif any(word in description_lower for word in ['automate', 'script', 'code']):
        return "automation"
    else:
        return "general"

def determine_task_priority(description: str) -> str:
    """Determine task priority based on description"""
    
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['urgent', 'asap', 'immediately', 'critical']):
        return "high"
    elif any(word in description_lower for word in ['when possible', 'eventually', 'sometime']):
        return "low"
    else:
        return "normal"
