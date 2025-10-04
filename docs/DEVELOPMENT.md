# Development Guide

This document provides guidance for developers working on Magentic-UI.

## Development Setup

### Prerequisites

- Python 3.10+
- Docker Desktop
- Node.js 18+
- PostgreSQL (for database features)

### Quick Start

```bash
# Clone and setup
git clone https://github.com/microsoft/magentic-ui.git
cd magentic-ui

# Install dependencies
uv venv --python=3.12 .venv
source .venv/bin/activate
uv sync --all-extras

# Build frontend
cd frontend
yarn install
yarn build
cd ..

# Run development server
magentic-ui --port 8081
```

## Project Structure

```text
magentic-ui/
├── src/                    # Core Python package
├── frontend/              # React/Gatsby web UI
├── ios-app/              # iOS native app
├── voice-backend/        # Voice processing backend
├── docker/               # Docker configurations
├── docs/                 # Documentation
├── experiments/          # Research experiments
└── tests/               # Test suites
```

## Development Workflows

### Testing

```bash
# Run test suite
pytest tests/

# Run specific test
python test_voice_system.py

# Run comprehensive tests
python functional_test_suite.py
```

### Database Development

```bash
# Setup local database
docker-compose up -d postgres

# Run migrations
python enhanced_db_integration.py

# Test optimizations
python valkey_performance_benchmark.py
```

### Voice System Development

```bash
# Start voice backend
cd voice-backend
python main.py

# Run iOS simulator (requires Xcode)
cd ios-app
open MagenticVoice.xcodeproj
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.

## Architecture Documents

- [Multi-Agent Business Architecture](../MULTI_AGENT_BUSINESS_ARCHITECTURE.md)
- [Voice System Architecture](VOICE_SYSTEM.md)
- [Database Optimizations](DATABASE_OPTIMIZATIONS.md)
