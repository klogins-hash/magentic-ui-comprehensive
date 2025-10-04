# Docker Deployment Guide

Complete guide for deploying Magentic-UI using Docker containers in development and production environments.

## 🚀 Quick Start

### Prerequisites

- **Docker Engine 20.10+**
- **Docker Compose 2.0+**
- **8GB RAM minimum** (16GB recommended)
- **20GB disk space** for images and data

### One-Command Deployment

```bash
# Clone and deploy
git clone https://github.com/microsoft/magentic-ui.git
cd magentic-ui

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Deploy production stack
make docker-deploy
```

## 📋 Deployment Options

### Production Deployment

```bash
# Full production stack with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Basic production stack
docker-compose -f docker-compose.prod.yml up -d

# Check health
./docker/health-check.sh
```

### Development Deployment

```bash
# Development stack with hot reload
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps
```

## 🔧 Configuration

### Environment Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   cp voice-backend/.env.example voice-backend/.env
   ```

2. **Configure API keys**:
   ```bash
   # Required
   OPENAI_API_KEY=your_openai_key_here
   GROQ_API_KEY=your_groq_key_here
   
   # Optional
   AZURE_OPENAI_API_KEY=your_azure_key
   ```

3. **Security settings**:
   ```bash
   # Change default passwords
   POSTGRES_PASSWORD=your_secure_password
   SECRET_KEY=your_secret_key
   GRAFANA_PASSWORD=your_grafana_password
   ```

### Service Configuration

#### Core Application
- **Port**: 8081
- **Health**: `http://localhost:8081/health`
- **API**: `http://localhost:8081/api`

#### Voice Backend
- **Port**: 8765 (WebSocket)
- **Health**: `http://localhost:8765/health`
- **Protocol**: WebSocket

#### Frontend
- **Port**: 3000
- **URL**: `http://localhost:3000`
- **Proxy**: Routes to core and voice services

#### Database Services
- **PostgreSQL**: Port 5432
- **Valkey/Redis**: Port 6379
- **Monitoring**: Ports 9090 (Prometheus), 3001 (Grafana)

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Magentic Core  │    │  Voice Backend  │
│   (React/Nginx) │    │   (Python)      │    │   (Pipecat)     │
│   Port: 3000    │    │   Port: 8081    │    │   Port: 8765    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐
         │   PostgreSQL    │    │     Valkey      │
         │   (Database)    │    │    (Cache)      │
         │   Port: 5432    │    │   Port: 6379    │
         └─────────────────┘    └─────────────────┘
```

## 🔍 Monitoring & Observability

### Health Checks

```bash
# Automated health check
./docker/health-check.sh

# Manual service checks
curl http://localhost:8081/health  # Core API
curl http://localhost:8765/health  # Voice Backend
curl http://localhost:3000         # Frontend
```

### Monitoring Stack

Access monitoring services:

- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3001` (admin/admin)

Enable monitoring:
```bash
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Service-specific logs
docker-compose -f docker-compose.prod.yml logs -f magentic-core
docker-compose -f docker-compose.prod.yml logs -f voice-backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Real-time logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

## 🛠️ Operations

### Starting Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Start specific service
docker-compose -f docker-compose.prod.yml up -d magentic-core

# Start with build
docker-compose -f docker-compose.prod.yml up -d --build
```

### Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (⚠️ Data loss)
docker-compose -f docker-compose.prod.yml down -v

# Stop specific service
docker-compose -f docker-compose.prod.yml stop magentic-core
```

### Scaling Services

```bash
# Scale core service
docker-compose -f docker-compose.prod.yml up -d --scale magentic-core=3

# Scale voice backend
docker-compose -f docker-compose.prod.yml up -d --scale voice-backend=2
```

### Updates & Maintenance

```bash
# Update images
docker-compose -f docker-compose.prod.yml pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U magentic magentic_ui > backup.sql

# Database restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U magentic magentic_ui < backup.sql
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
docker info

# Check compose file syntax
docker-compose -f docker-compose.prod.yml config

# Check resource usage
docker system df
```

#### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres psql -U magentic -d magentic_ui -c "SELECT 1;"

# Reset database (⚠️ Data loss)
docker-compose -f docker-compose.prod.yml down -v
docker volume rm magentic-ui_postgres_data
```

#### Memory Issues
```bash
# Check container resource usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Advanced > Memory

# Clean up unused resources
docker system prune -a
```

#### Network Issues
```bash
# Check network connectivity
docker-compose -f docker-compose.prod.yml exec magentic-core curl -f http://postgres:5432

# Recreate network
docker-compose -f docker-compose.prod.yml down
docker network prune
docker-compose -f docker-compose.prod.yml up -d
```

### Performance Tuning

#### Database Optimization
```bash
# Increase shared_buffers
echo "shared_buffers = 256MB" >> postgresql.conf

# Enable connection pooling
echo "max_connections = 200" >> postgresql.conf
```

#### Cache Optimization
```bash
# Increase Valkey memory
docker-compose -f docker-compose.prod.yml exec valkey valkey-cli CONFIG SET maxmemory 1gb
```

## 🔒 Security Considerations

### Production Security

1. **Change default passwords**
2. **Use environment variables for secrets**
3. **Enable SSL/TLS termination**
4. **Configure firewall rules**
5. **Regular security updates**

### SSL/TLS Setup

```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/private.key \
  -out docker/ssl/certificate.crt

# Update nginx configuration
# Add SSL configuration to docker/nginx.conf
```

## 📊 Resource Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 8GB
- **Disk**: 20GB
- **Network**: 1Mbps

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Disk**: 50GB+ SSD
- **Network**: 10Mbps+

### Production Requirements
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Disk**: 100GB+ SSD
- **Network**: 100Mbps+

## 🌐 Cloud Deployment

### AWS ECS
```bash
# Use provided ECS task definitions
aws ecs create-cluster --cluster-name magentic-ui
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/magentic-ui
gcloud run deploy --image gcr.io/PROJECT-ID/magentic-ui --platform managed
```

### Azure Container Instances
```bash
# Deploy container group
az container create --resource-group myResourceGroup \
  --file docker-compose.prod.yml
```

This deployment setup provides a robust, scalable foundation for your Magentic-UI multi-agent system!
