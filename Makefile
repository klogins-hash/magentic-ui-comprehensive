# Magentic-UI Monorepo Makefile

.PHONY: help install build test lint clean dev docker

# Default target
help:
	@echo "Magentic-UI Monorepo Commands:"
	@echo "  install     Install all dependencies"
	@echo "  build       Build all components"
	@echo "  test        Run all tests"
	@echo "  lint        Lint all code"
	@echo "  dev         Start development servers"
	@echo "  clean       Clean all build artifacts"
	@echo "  docker      Build Docker containers"

# Install dependencies for all components
install:
	@echo "Installing Python dependencies..."
	uv sync --all-extras
	@echo "Installing frontend dependencies..."
	cd frontend && yarn install
	@echo "Installing voice backend dependencies..."
	cd voice-backend && pip install -r requirements.txt

# Build all components
build:
	@echo "Building core package..."
	uv build
	@echo "Building frontend..."
	cd frontend && yarn build
	@echo "Building Docker images..."
	cd docker && ./build-all.sh

# Run tests for all components
test:
	@echo "Running Python tests..."
	pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && yarn test
	@echo "Running voice system tests..."
	python test_voice_system.py

# Lint all code
lint:
	@echo "Linting Python code..."
	ruff check src/
	ruff format --check src/
	@echo "Linting frontend code..."
	cd frontend && yarn lint

# Start development servers
dev:
	@echo "Starting development environment..."
	@echo "Core UI: http://localhost:8081"
	@echo "Frontend Dev: http://localhost:8000" 
	@echo "Voice Backend: ws://localhost:8765"
	@make -j3 dev-core dev-frontend dev-voice

dev-core:
	magentic-ui --port 8081

dev-frontend:
	cd frontend && yarn start

dev-voice:
	cd voice-backend && python main.py

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist/ build/ .pytest_cache/ __pycache__/
	cd frontend && rm -rf build/ node_modules/.cache/
	docker system prune -f

# Docker operations
docker-build:
	@echo "Building Docker containers..."
	docker-compose -f docker-compose.prod.yml build --parallel

docker-deploy:
	@echo "Deploying production stack..."
	./deploy.sh deploy

docker-dev:
	@echo "Starting development environment..."
	./deploy.sh dev

docker-stop:
	@echo "Stopping services..."
	./deploy.sh stop

docker-logs:
	@echo "Viewing logs..."
	./deploy.sh logs

docker-health:
	@echo "Running health checks..."
	./deploy.sh health

docker-clean:
	@echo "Cleaning up Docker resources..."
	./deploy.sh clean

# Legacy docker command
docker: docker-build
