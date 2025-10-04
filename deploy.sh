#!/bin/bash

# Magentic-UI Easy Deployment Script
# This script provides a simple way to deploy the entire Magentic-UI stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
VOICE_ENV_FILE="voice-backend/.env"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Magentic-UI Deployment                   ║"
    echo "║              Multi-Agent Business System                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

setup_environment() {
    print_step "Setting up environment configuration..."
    
    # Main environment file
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "${ENV_FILE}.example" ]; then
            cp "${ENV_FILE}.example" "$ENV_FILE"
            print_success "Created $ENV_FILE from template"
        else
            print_error "No environment template found. Please create $ENV_FILE"
            exit 1
        fi
    else
        print_success "Environment file $ENV_FILE already exists"
    fi
    
    # Voice backend environment file
    if [ ! -f "$VOICE_ENV_FILE" ]; then
        if [ -f "${VOICE_ENV_FILE}.example" ]; then
            cp "${VOICE_ENV_FILE}.example" "$VOICE_ENV_FILE"
            print_success "Created $VOICE_ENV_FILE from template"
        else
            print_error "No voice backend environment template found"
            exit 1
        fi
    else
        print_success "Voice backend environment file already exists"
    fi
    
    # Check for required API keys
    if ! grep -q "your_.*_key_here" "$ENV_FILE" 2>/dev/null; then
        print_success "API keys appear to be configured"
    else
        echo -e "${YELLOW}"
        echo "⚠️  Please configure your API keys in $ENV_FILE:"
        echo "   - OPENAI_API_KEY (required)"
        echo "   - GROQ_API_KEY (required for voice system)"
        echo ""
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        echo -e "${NC}"
    fi
}

pull_images() {
    print_step "Pulling base images..."
    
    # Pull base images to speed up build
    docker pull python:3.11-slim
    docker pull node:18-alpine
    docker pull nginx:alpine
    docker pull pgvector/pgvector:pg15
    docker pull valkey/valkey:7.2-alpine
    
    print_success "Base images pulled"
}

build_services() {
    print_step "Building application services..."
    
    # Build with BuildKit for better performance
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    
    docker-compose -f "$COMPOSE_FILE" build --parallel
    
    print_success "Services built successfully"
}

start_services() {
    print_step "Starting services..."
    
    # Start infrastructure services first
    docker-compose -f "$COMPOSE_FILE" up -d postgres valkey
    
    # Wait for database to be ready
    print_step "Waiting for database to be ready..."
    sleep 10
    
    # Start application services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_success "All services started"
}

run_health_check() {
    print_step "Running health checks..."
    
    if [ -x "./docker/health-check.sh" ]; then
        ./docker/health-check.sh "$COMPOSE_FILE"
    else
        # Basic health check
        sleep 30
        
        if curl -f -s http://localhost:8081/health > /dev/null 2>&1; then
            print_success "Core service is healthy"
        else
            print_error "Core service health check failed"
        fi
        
        if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend service is healthy"
        else
            print_error "Frontend service health check failed"
        fi
    fi
}

show_access_info() {
    echo -e "${GREEN}"
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "Access your Magentic-UI system:"
    echo "  📱 Web Interface:    http://localhost:3000"
    echo "  🔧 Core API:         http://localhost:8081"
    echo "  🎤 Voice WebSocket:  ws://localhost:8765"
    echo "  🗄️  Database:        localhost:5432"
    echo "  💾 Cache:           localhost:6379"
    echo ""
    echo "Management commands:"
    echo "  📊 View logs:        docker-compose -f $COMPOSE_FILE logs -f"
    echo "  🔄 Restart:          docker-compose -f $COMPOSE_FILE restart"
    echo "  🛑 Stop:             docker-compose -f $COMPOSE_FILE down"
    echo "  🏥 Health check:     ./docker/health-check.sh"
    echo ""
    echo "📚 Documentation: ./docs/DOCKER_DEPLOYMENT.md"
    echo -e "${NC}"
}

cleanup_on_error() {
    print_error "Deployment failed. Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down
    exit 1
}

# Main deployment function
main() {
    print_header
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            setup_environment
            pull_images
            build_services
            start_services
            run_health_check
            show_access_info
            ;;
        "dev")
            COMPOSE_FILE="docker-compose.dev.yml"
            check_prerequisites
            setup_environment
            docker-compose -f "$COMPOSE_FILE" up -d --build
            print_success "Development environment started"
            ;;
        "stop")
            docker-compose -f "$COMPOSE_FILE" down
            print_success "Services stopped"
            ;;
        "restart")
            docker-compose -f "$COMPOSE_FILE" restart
            print_success "Services restarted"
            ;;
        "logs")
            docker-compose -f "$COMPOSE_FILE" logs -f
            ;;
        "health")
            ./docker/health-check.sh "$COMPOSE_FILE"
            ;;
        "clean")
            docker-compose -f "$COMPOSE_FILE" down -v
            docker system prune -f
            print_success "Cleanup completed"
            ;;
        *)
            echo "Usage: $0 {deploy|dev|stop|restart|logs|health|clean}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Full production deployment (default)"
            echo "  dev      - Start development environment"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  logs     - View service logs"
            echo "  health   - Run health checks"
            echo "  clean    - Stop services and clean up"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
