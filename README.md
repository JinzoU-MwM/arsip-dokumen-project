# AI-Driven Legal Document Automation System

A comprehensive AI-powered legal document automation platform that automatically processes legal documents from local folders, classifies them using advanced AI, validates completeness, and uploads them to organized Google Drive folders with real-time WhatsApp notifications.

## 🚀 Phase 1 Implementation Status: ✅ COMPLETE

### ✅ Completed Phase 1 Tasks

- [x] **T001**: Created complete microservices project structure
- [x] **T002**: Initialized Python FastAPI projects (Document Watcher, AI Processor)
- [x] **T003**: Initialized Node.js TypeScript project (Notification Service)
- [x] **T004**: Initialized React TypeScript project structure (Web Dashboard)
- [x] **T005**: Configured Docker containers for all services
- [x] **T006**: Set up docker-compose.yml for local development
- [x] **T007**: Configured linting and formatting tools (flake8, ESLint, Prettier)
- [x] **T008**: Set up comprehensive .gitignore and .dockerignore

### 🏗️ Architecture Overview

#### Implemented Services

1. **Document Watcher Service** (Port 8001)
   - Monitors local folders for new legal documents
   - Triggers AI processing pipeline
   - Handles file events and queuing

2. **AI Processing Service** (Port 8002)
   - Document classification using AI models
   - OCR processing with Tesseract
   - NLP processing for entity extraction
   - Ollama LLM integration for advanced analysis

3. **Notification Service** (Port 8005)
   - WhatsApp notifications via WAHA
   - Email notifications (template)
   - Template management system
   - Rate limiting and retry logic

#### Infrastructure Components

- **PostgreSQL Database** (Port 5432) - Primary data storage
- **Redis Cache** (Port 6379) - Caching and session management
- **Ollama LLM** (Port 11434) - Local AI processing
- **WAHA WhatsApp** (Port 3000) - WhatsApp Business API
- **Prometheus** (Port 9090) - Monitoring and metrics
- **Grafana** (Port 3001) - Visualization dashboards

## 🛠️ Quick Start

### Prerequisites

1. **Docker & Docker Compose**
   ```bash
   # Install Docker and Docker Compose
   # Verify installation
   docker --version
   docker-compose --version
   ```

2. **Git**
   ```bash
   git --version
   ```

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd arsip-dokumen-project
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your specific configurations
   ```

3. **Create watched directories**
   ```bash
   mkdir -p watched queue
   ```

4. **Start the development environment**
   ```bash
   # Start all services
   docker-compose up -d

   # View logs
   docker-compose logs -f

   # Stop all services
   docker-compose down
   ```

### Access Points

Once running, access the services at:

- **Document Watcher API**: http://localhost:8001
- **AI Processing API**: http://localhost:8002
- **Notification API**: http://localhost:8005
- **Prometheus Monitoring**: http://localhost:9090
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)
- **pgAdmin (Database)**: http://localhost:5050
- **Redis Commander**: http://localhost:8081

### Development Workflow

1. **Start development environment**
   ```bash
   # Use override for development with hot reload
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up
   ```

2. **Code quality checks**
   ```bash
   # Python services
   flake8 services/document-watcher/app
   flake8 services/ai-processor/app

   # Node.js service
   cd services/notification-service
   npm run lint
   npm run format
   ```

3. **Testing**
   ```bash
   # Run tests for each service
   docker-compose exec document-watcher python -m pytest
   cd services/notification-service && npm test
   ```

## 📁 Project Structure

```
arsip-dokumen-project/
├── services/                     # Microservices
│   ├── document-watcher/         # File monitoring service
│   ├── ai-processor/             # AI/ML processing service
│   ├── notification-service/     # WhatsApp/email notifications
│   ├── google-drive-service/     # Google Drive integration
│   ├── validation-engine/        # Compliance validation
│   ├── audit-service/           # Logging & compliance
│   └── web-dashboard/           # Web interface
├── shared/                      # Shared libraries
├── infrastructure/              # DevOps & deployment
├── tests/                      # Integration & E2E tests
├── config/                     # Configuration files
├── docs/                       # Documentation
├── specs/001-title-ai-driven/   # Feature specifications
├── docker-compose.yml          # Production deployment
├── docker-compose.override.yml # Development override
└── .env.example                # Environment template
```

## 🔧 Configuration

### Environment Variables

Key environment variables to configure:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legal_automation

# AI Services
OLLAMA_MODEL=llama3:70b
OLLAMA_URL=http://localhost:11434

# WhatsApp
WAHA_API_KEY=your-waha-api-key
WAHA_SESSION=default

# File Monitoring
WATCH_FOLDER_1=D:/Download Legalitas
WATCH_FOLDER_2=D:/Documents/Legal/Queue
```

### Service Configuration

Each service has its own configuration:

- **Document Watcher**: Monitors local folders, triggers processing
- **AI Processor**: Uses Ollama for document analysis and classification
- **Notification Service**: Sends WhatsApp notifications via WAHA

## 🚀 Next Steps (Phase 2)

Phase 2 will focus on:

1. **Complete remaining microservices** (Validation Engine, Google Drive Service, Audit Service)
2. **Implement Web Dashboard** with React/TypeScript
3. **Add comprehensive testing** (unit, integration, e2e)
4. **Set up CI/CD pipeline**
5. **Implement security and compliance features**

## 📊 System Capabilities

### Current Features

- ✅ File monitoring with watchdog
- ✅ AI document classification
- ✅ OCR processing
- ✅ WhatsApp notifications
- ✅ Containerized deployment
- ✅ Monitoring and logging
- ✅ Development environment setup

### Target Capabilities (Full Implementation)

- 🎯 10+ document categories with >95% accuracy
- 🎯 >1000 documents/hour processing
- 🎯 <30 seconds processing time
- 🎯 SOC2 Type II compliance
- 🎯 Multi-AI collaboration
- 🎯 Real-time collaboration
- 🎯 Advanced analytics dashboard

## 🤝 Contributing

1. Follow the coding standards (flake8, ESLint, Prettier)
2. Write tests for new features
3. Update documentation
4. Use semantic commit messages
5. Ensure all services pass health checks

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For support and questions:

1. Check the [documentation](./docs/)
2. Review [issues](../../issues)
3. Contact the development team

---

**Status**: Phase 1 Complete ✅ | **Next**: Begin Phase 2 Implementation