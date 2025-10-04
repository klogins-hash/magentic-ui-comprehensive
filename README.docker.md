# 🐳 Docker Quick Start

**One-command deployment for the complete Magentic-UI multi-agent system.**

## 🚀 Instant Deployment

```bash
# 1. Clone repository
git clone https://github.com/microsoft/magentic-ui.git
cd magentic-ui

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, GROQ_API_KEY)

# 3. Deploy everything
./deploy.sh
```

**That's it!** Your complete system will be running at:
- 🌐 **Web UI**: http://localhost:3000
- 🔧 **API**: http://localhost:8081  
- 🎤 **Voice**: ws://localhost:8765

## 📦 What Gets Deployed

- **Magentic-UI Core**: Multi-agent orchestration system
- **Voice Backend**: Pipecat + Groq voice processing
- **Web Frontend**: React interface with proxy routing
- **PostgreSQL**: Database with pgvector and AGE extensions
- **Valkey**: High-performance Redis-compatible cache
- **Monitoring**: Prometheus + Grafana (optional)

## 🛠️ Management Commands

```bash
./deploy.sh dev      # Development environment
./deploy.sh stop     # Stop all services
./deploy.sh restart  # Restart services
./deploy.sh logs     # View logs
./deploy.sh health   # Health check
./deploy.sh clean    # Clean up everything
```

## 📋 Requirements

- **Docker 20.10+** and **Docker Compose 2.0+**
- **8GB RAM** minimum (16GB recommended)
- **API Keys**: OpenAI and Groq (for voice features)

## 🔧 Configuration

Edit `.env` file for:
- API keys (OpenAI, Groq, Azure)
- Database passwords
- Service ports
- Feature toggles

## 📚 Full Documentation

- **[Complete Deployment Guide](docs/DOCKER_DEPLOYMENT.md)**
- **[Monorepo Architecture](docs/MONOREPO.md)**
- **[Voice System](docs/VOICE_SYSTEM.md)**
- **[Development Guide](docs/DEVELOPMENT.md)**

## 🆘 Need Help?

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View specific service logs
docker-compose -f docker-compose.prod.yml logs magentic-core

# Restart problematic service
docker-compose -f docker-compose.prod.yml restart magentic-core
```

**Ready to build the future of multi-agent systems? Deploy now! 🚀**
