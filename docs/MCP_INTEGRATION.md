# MCP (Model Context Protocol) Integration

This document outlines the MCP server integration for Magentic-UI, providing enhanced capabilities through external tool servers.

## 🚀 **MCP Integration Overview**

MCP servers extend Magentic-UI with specialized capabilities:

- **Cartesia**: Advanced voice cloning and TTS
- **HeyGen**: AI avatar video generation  
- **Browser Tools**: Web automation and scraping
- **Custom Servers**: Extensible framework for additional tools

## 📋 **Configuration**

### MCP Server Configuration (`mcp-config.yaml`)

```yaml
mcp_servers:
  cartesia:
    description: "Advanced voice cloning and TTS capabilities"
    server_params:
      type: "HttpServerParams"
      base_url: "https://api.cartesia.ai"
      api_key_env: "CARTESIA_API_KEY"
    capabilities:
      - voice_cloning
      - text_to_speech
      - voice_conversion
    integration_points:
      - voice_backend
      - ios_app
      
  heygen:
    description: "AI avatar video generation"
    server_params:
      type: "HttpServerParams"
      base_url: "https://api.heygen.com"
      api_key_env: "HEYGEN_API_KEY"
    capabilities:
      - avatar_video_generation
      - template_management
    integration_points:
      - magentic_core
      - frontend
```

### Environment Variables

```bash
# Required for MCP integration
CARTESIA_API_KEY=your_cartesia_key_here
HEYGEN_API_KEY=your_heygen_key_here
MCP_SERVER_PORT=8766
WEBHOOK_SECRET_KEY=your_webhook_secret
```

## 🔧 **Integration Points**

### Voice Backend Integration

The voice backend includes MCP webhook handlers for:

- **Cartesia Events**: Voice cloning completion, TTS processing
- **HeyGen Events**: Video generation completion, avatar creation
- **Status Monitoring**: Health checks and connection status

### Webhook Endpoints

- `POST /webhooks/cartesia/processing` - Cartesia event notifications
- `POST /webhooks/heygen/completion` - HeyGen event notifications  
- `GET /webhooks/health` - Health check endpoint
- `GET /webhooks/status` - MCP integration status

## 🎯 **Enhanced Capabilities**

### Voice Enhancement with Cartesia

```python
# Voice cloning capability
voice_result = await mcp_manager.call_cartesia_voice_clone(
    audio_file_path="user_voice.wav",
    voice_name="user_custom_voice",
    language="en",
    mode="similarity"
)

# Enhanced TTS with cloned voice
audio_data = await mcp_manager.call_cartesia_text_to_speech(
    text="Hello, this is your cloned voice!",
    voice_id=voice_result["voice_id"]
)
```

### Avatar Video Generation with HeyGen

```python
# Generate avatar video
video_result = await mcp_manager.call_heygen_generate_avatar_video(
    avatar_id="professional_avatar_1",
    voice_id="user_voice",
    input_text="Welcome to Magentic-UI!",
    title="System Introduction"
)
```

## 🔄 **Agent Configuration**

MCP-enhanced agents with specialized capabilities:

### Voice Enhancement Agent
- **Capabilities**: Voice cloning, TTS, audio processing
- **Integration**: Cartesia MCP server
- **Use Cases**: Personalized voice responses, voice conversion

### Video Generation Agent  
- **Capabilities**: Avatar videos, template management
- **Integration**: HeyGen MCP server
- **Use Cases**: Video responses, presentations, tutorials

### Web Automation Agent
- **Capabilities**: Browser control, form automation, scraping
- **Integration**: Browser Tools MCP server
- **Use Cases**: Complex web tasks, data extraction

## 🚀 **Deployment with Docker**

MCP integration is included in the Docker deployment:

```bash
# Deploy with MCP integration
./deploy.sh

# Check MCP status
curl http://localhost:8765/webhooks/status
```

### Docker Environment

```yaml
# docker-compose.prod.yml includes MCP environment
voice-backend:
  environment:
    - CARTESIA_API_KEY=${CARTESIA_API_KEY}
    - HEYGEN_API_KEY=${HEYGEN_API_KEY}
    - MCP_SERVER_PORT=8766
```

## 📊 **Monitoring & Observability**

### Health Checks

- **MCP Server Status**: Connection health for each server
- **Webhook Processing**: Event processing metrics
- **API Rate Limits**: Usage tracking and limits

### Logging

```python
# MCP integration logging
logger.info(f"MCP server {name} connected successfully")
logger.info(f"Processing {event_type} webhook from {server}")
logger.error(f"MCP server {name} connection failed: {error}")
```

## 🔮 **Future Enhancements**

### Planned MCP Integrations

1. **Database Tools**: Advanced query and analysis capabilities
2. **File Processing**: Document analysis and generation
3. **Communication**: Email, Slack, and messaging integrations
4. **AI Services**: Additional LLM and AI model integrations

### AutoGen v0.4 Integration

The MCP framework is designed to seamlessly integrate with the planned AutoGen v0.4 upgrade, providing:

- **Declarative Agent Configuration**: YAML-based agent definitions
- **Tool Discovery**: Automatic MCP server capability detection
- **Dynamic Routing**: Intelligent tool selection based on task requirements

## 🛠️ **Development**

### Adding New MCP Servers

1. **Update Configuration**: Add server details to `mcp-config.yaml`
2. **Create Webhook Handler**: Add endpoint in `mcp_webhook_handler.py`
3. **Implement Integration**: Add server calls in `mcp_integration.py`
4. **Update Documentation**: Document new capabilities

### Testing MCP Integration

```bash
# Test webhook endpoints
curl -X POST http://localhost:8765/webhooks/cartesia/processing \
  -H "Content-Type: application/json" \
  -d '{"event_type": "voice.cloned", "voice_id": "test_voice"}'

# Check integration status
curl http://localhost:8765/webhooks/status
```

This MCP integration provides a robust foundation for extending Magentic-UI with specialized AI and automation capabilities, supporting the evolution toward a comprehensive multi-agent business system.
