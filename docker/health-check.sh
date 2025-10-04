#!/bin/bash

# Magentic-UI Health Check Script
# This script checks the health of all services in the deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE=${1:-docker-compose.prod.yml}
MAX_RETRIES=30
RETRY_INTERVAL=10

echo "🏥 Magentic-UI Health Check"
echo "=========================="

# Function to check service health
check_service_health() {
    local service_name=$1
    local health_url=$2
    local retries=0
    
    echo -n "Checking $service_name... "
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
            return 0
        fi
        
        retries=$((retries + 1))
        if [ $retries -lt $MAX_RETRIES ]; then
            echo -n "."
            sleep $RETRY_INTERVAL
        fi
    done
    
    echo -e "${RED}✗ Unhealthy${NC}"
    return 1
}

# Function to check database connectivity
check_database() {
    echo -n "Checking PostgreSQL... "
    
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U magentic -d magentic_ui > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
        return 0
    else
        echo -e "${RED}✗ Connection failed${NC}"
        return 1
    fi
}

# Function to check Valkey/Redis
check_valkey() {
    echo -n "Checking Valkey... "
    
    if docker-compose -f "$COMPOSE_FILE" exec -T valkey valkey-cli ping | grep -q "PONG"; then
        echo -e "${GREEN}✓ Connected${NC}"
        return 0
    else
        echo -e "${RED}✗ Connection failed${NC}"
        return 1
    fi
}

# Main health check sequence
main() {
    local all_healthy=true
    
    echo "Checking infrastructure services..."
    
    if ! check_database; then
        all_healthy=false
    fi
    
    if ! check_valkey; then
        all_healthy=false
    fi
    
    echo ""
    echo "Checking application services..."
    
    if ! check_service_health "Magentic Core" "http://localhost:8081/health"; then
        all_healthy=false
    fi
    
    if ! check_service_health "Voice Backend" "http://localhost:8765/health"; then
        all_healthy=false
    fi
    
    if ! check_service_health "Frontend" "http://localhost:3000"; then
        all_healthy=false
    fi
    
    echo ""
    echo "=========================="
    
    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}🎉 All services are healthy!${NC}"
        echo ""
        echo "Access points:"
        echo "  • Web UI: http://localhost:3000"
        echo "  • Core API: http://localhost:8081"
        echo "  • Voice WebSocket: ws://localhost:8765"
        echo "  • Database: localhost:5432"
        echo "  • Cache: localhost:6379"
        exit 0
    else
        echo -e "${RED}❌ Some services are unhealthy${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  • Check logs: docker-compose -f $COMPOSE_FILE logs [service]"
        echo "  • Restart services: docker-compose -f $COMPOSE_FILE restart"
        echo "  • Check environment: cat .env"
        exit 1
    fi
}

# Run health check
main
