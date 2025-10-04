# Monorepo Architecture

Magentic-UI is organized as a **monorepo** containing multiple related components that work together to provide a comprehensive multi-agent business system.

## 🏗️ Repository Structure

```text
magentic-ui/ (monorepo root)
├── src/magentic_ui/          # Core Python package
├── frontend/                 # React/Gatsby web UI  
├── ios-app/                  # iOS SwiftUI app
├── voice-backend/            # Python voice server
├── web-frontend/             # Additional web components
├── docker/                   # Container configurations
├── experiments/              # Research & development
├── docs/                     # Shared documentation
├── packages/                 # Package configurations
└── tools/                    # Build and development tools
```

## 📦 Component Overview

### Core Components
- **`src/magentic_ui/`**: Main Python package with AutoGen agents
- **`frontend/`**: Primary web interface (React/Gatsby)
- **`ios-app/`**: Native iOS application (SwiftUI)
- **`voice-backend/`**: Voice processing server (Pipecat + Groq)

### Supporting Components
- **`web-frontend/`**: Additional web components and utilities
- **`docker/`**: Container definitions and orchestration
- **`experiments/`**: Research prototypes and testing
- **`docs/`**: Comprehensive documentation

## 🚀 Development Workflow

### Quick Start
```bash
# Install all dependencies
make install

# Start development environment
make dev
# This starts:
# - Core UI: http://localhost:8081
# - Frontend Dev: http://localhost:8000
# - Voice Backend: ws://localhost:8765
```

### Individual Components
```bash
# Core package only
cd src && magentic-ui --port 8081

# Frontend development
cd frontend && yarn start

# Voice backend
cd voice-backend && python main.py

# iOS app (requires Xcode)
cd ios-app && open MagenticVoice.xcodeproj
```

## 🔧 Build System

### Unified Commands
- **`make install`**: Install dependencies for all components
- **`make build`**: Build all components
- **`make test`**: Run tests across all components
- **`make lint`**: Lint all code
- **`make clean`**: Clean build artifacts

### Turbo Integration
Uses Turborepo for optimized builds and caching:
```bash
# Build with dependency awareness
turbo build

# Test with parallelization
turbo test

# Development with watch mode
turbo dev
```

## 📋 Package Management

### Python Components
- **Core**: Uses `uv` for dependency management
- **Voice Backend**: Uses `pip` with `requirements.txt`
- Shared Python dependencies in root `pyproject.toml`

### JavaScript Components
- **Frontend**: Uses `yarn` for package management
- **Workspace**: Configured for monorepo package sharing
- Shared dev dependencies in root `package.json`

### iOS Component
- **iOS App**: Uses Xcode project with Swift Package Manager
- Independent dependency management
- Integrated build through Makefile

## 🔄 CI/CD Integration

### GitHub Actions
- **Multi-component testing**: Tests all components in parallel
- **Dependency caching**: Optimized for monorepo structure
- **Selective builds**: Only builds changed components
- **Cross-platform testing**: Python 3.10-3.12, Node.js 18+

### Docker Orchestration
- **Multi-stage builds**: Optimized container sizes
- **Component isolation**: Each component has its own container
- **Development compose**: Full stack development environment

## 🎯 Benefits of Monorepo Structure

### Development Benefits
- **Unified tooling**: Single set of development tools
- **Shared dependencies**: Avoid version conflicts
- **Atomic changes**: Cross-component changes in single PR
- **Consistent standards**: Unified linting, testing, formatting

### Deployment Benefits
- **Coordinated releases**: All components versioned together
- **Simplified CI/CD**: Single pipeline for entire system
- **Dependency tracking**: Clear component relationships
- **Rollback safety**: Consistent state across components

### Architecture Benefits
- **Component isolation**: Clear boundaries between services
- **Shared libraries**: Common utilities and types
- **Integration testing**: Full-stack testing capabilities
- **Documentation**: Centralized architecture documentation

## 🔮 Future Evolution

The monorepo structure supports the planned evolution to:

1. **AutoGen v0.4 Integration**: Seamless orchestrator updates
2. **MCP Server Expansion**: New tool integrations
3. **Railway Deployment**: Cloud-native infrastructure
4. **Agent-builds-Agent**: Self-improving system capabilities

This architecture provides the foundation for scaling from the current local development setup to a distributed, cloud-native multi-agent business system.
