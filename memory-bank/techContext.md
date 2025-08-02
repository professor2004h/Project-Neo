# Technical Context: Cambridge AI Tutor

## Technology Stack

### Backend Technologies

#### Core Framework
- **FastAPI 0.115+**: High-performance async web framework
- **Python 3.11+**: Modern Python with async/await support
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

#### Database & Storage
- **Supabase**: PostgreSQL database with Row Level Security
- **Redis 5.2+**: Caching and real-time features
- **Supabase Storage**: File storage for media content
- **Alembic**: Database migration management

#### AI & Machine Learning
- **LiteLLM 1.72+**: Unified interface for multiple LLM providers
- **OpenAI API**: GPT-4 for advanced text generation
- **Anthropic API**: Claude for alternative AI responses
- **Google Gemini API**: Additional AI provider option
- **Speech Recognition**: OpenAI Whisper for voice processing
- **Text-to-Speech**: OpenAI TTS for voice synthesis

#### Authentication & Security
- **Supabase Auth**: JWT-based authentication
- **Row Level Security (RLS)**: Database-level access control
- **JWT Validation**: Token verification without signature checks
- **Encryption**: AES-256 for sensitive data

### Frontend Technologies

#### Web Application
- **React 18+**: Component-based UI framework
- **TypeScript 5+**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **React Query**: Server state management
- **React Hook Form**: Form handling and validation

#### Mobile Applications
- **Flutter 3.0+**: Cross-platform mobile development
- **Dart**: Programming language for Flutter
- **Provider/Riverpod**: State management
- **Flutter Web**: Web support for mobile apps

#### Chrome Extension
- **Vanilla JavaScript**: Core extension functionality
- **React**: UI components for extension popup
- **Manifest V3**: Modern extension architecture
- **Content Scripts**: Website integration

### Infrastructure & DevOps

#### Containerization
- **Docker**: Application containerization
- **Docker Compose**: Local development environment
- **Multi-stage builds**: Optimized production images

#### Monitoring & Observability
- **Langfuse**: LLM tracing and monitoring
- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization

#### Background Processing
- **Dramatiq 1.18+**: Async task processing
- **Redis**: Message broker for background jobs
- **QStash**: Scheduled task management

## Development Setup

### Environment Configuration

#### Required Tools
```bash
# Python environment
python 3.11+
pip install poetry  # Dependency management

# Node.js environment
node 18+
npm install -g yarn  # Package manager

# Database
docker run -d --name redis redis:7-alpine
docker run -d --name postgres postgres:15

# Development tools
git
docker
docker-compose
```

#### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/cambridge_tutor
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Security
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key

# Monitoring
LANGFUSE_PUBLIC_KEY=your_langfuse_key
LANGFUSE_SECRET_KEY=your_langfuse_secret
SENTRY_DSN=your_sentry_dsn
```

### Project Structure

```
cambridge-ai-tutor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── tutor.py
│   │   │   │   ├── content.py
│   │   │   │   ├── progress.py
│   │   │   │   └── sync.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── curriculum.py
│   │   │   ├── progress.py
│   │   │   └── tutor.py
│   │   ├── services/
│   │   │   ├── tutor_service.py
│   │   │   ├── content_service.py
│   │   │   ├── progress_service.py
│   │   │   ├── sync_service.py
│   │   │   └── safety_service.py
│   │   ├── repositories/
│   │   │   ├── user_repository.py
│   │   │   ├── curriculum_repository.py
│   │   │   └── progress_repository.py
│   │   └── utils/
│   │       ├── llm_utils.py
│   │       ├── curriculum_utils.py
│   │       └── safety_utils.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── alembic/
│   │   └── versions/
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── web-app/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── utils/
│   │   ├── public/
│   │   └── package.json
│   ├── mobile-app/
│   │   ├── lib/
│   │   ├── assets/
│   │   └── pubspec.yaml
│   └── chrome-extension/
│       ├── src/
│       ├── public/
│       └── manifest.json
├── docs/
│   ├── api/
│   ├── deployment/
│   └── user-guides/
└── docker-compose.yml
```

## Technical Constraints

### Performance Requirements

#### Response Time Targets
- **AI Tutor Responses**: < 3 seconds
- **API Endpoints**: < 500ms for standard operations
- **Database Queries**: < 100ms for indexed operations
- **Real-time Updates**: < 200ms for WebSocket messages

#### Scalability Constraints
- **Concurrent Users**: Support 10,000+ simultaneous users
- **AI Service Calls**: Handle 1,000+ requests per minute
- **Database Connections**: Connection pooling for 100+ concurrent connections
- **File Storage**: Efficient handling of educational media content

### Security Constraints

#### Child Safety Requirements
- **Content Moderation**: Real-time inappropriate content detection
- **Age Verification**: Strict age-appropriate content delivery
- **Parental Controls**: Comprehensive oversight capabilities
- **Data Protection**: COPPA and GDPR compliance

#### Privacy Protection
- **Data Encryption**: AES-256 for all sensitive data
- **Access Controls**: Role-based permissions with parental oversight
- **Audit Logging**: Comprehensive activity tracking
- **Data Portability**: Easy export and deletion options

### Reliability Constraints

#### Availability Targets
- **Uptime**: 99.9% availability
- **Graceful Degradation**: Fallback content when AI unavailable
- **Offline Support**: Cached content for continued learning
- **Error Recovery**: Automatic retry mechanisms

#### Data Consistency
- **Cross-Platform Sync**: Real-time data synchronization
- **Conflict Resolution**: Last-write-wins with conflict detection
- **Data Integrity**: ACID compliance for critical operations
- **Backup Strategy**: Automated backups with point-in-time recovery

## Dependencies & Integrations

### External Services

#### AI Providers
- **OpenAI**: Primary LLM provider for text generation
- **Anthropic**: Alternative LLM for response diversity
- **Google Gemini**: Additional AI provider option
- **Speech Services**: OpenAI Whisper and TTS

#### Infrastructure Services
- **Supabase**: Database, authentication, and storage
- **Redis**: Caching and real-time features
- **Cloud Storage**: Media file storage and CDN
- **Monitoring**: Langfuse, Sentry, Prometheus

#### Educational Services
- **Cambridge Curriculum APIs**: Official curriculum data
- **Content Validation**: Automated curriculum alignment checks
- **Assessment Tools**: Progress tracking and evaluation

### Internal Dependencies

#### Service Dependencies
```python
# Core service dependencies
TutorService -> LLMService, CurriculumService, PersonalizationService
ContentService -> CurriculumService, MediaService, SafetyService
ProgressService -> AnalyticsService, RecommendationService
SyncService -> Redis, Database, EventBus
```

#### Data Dependencies
```python
# Database relationships
User -> ChildProfile (one-to-many)
ChildProfile -> LearningActivity (one-to-many)
CurriculumTopic -> LearningActivity (one-to-many)
TutorSession -> TutorMessage (one-to-many)
```

## Development Workflow

### Code Quality Standards

#### Python Development
- **Type Hints**: Comprehensive type annotations
- **Async/Await**: Non-blocking operations throughout
- **Error Handling**: Structured exception handling
- **Logging**: Structured logging with context

#### Frontend Development
- **TypeScript**: Strict type checking
- **Component Testing**: Unit tests for all components
- **Accessibility**: WCAG 2.1 AA compliance
- **Performance**: Code splitting and lazy loading

### Testing Strategy

#### Test Coverage Targets
- **Unit Tests**: 80%+ coverage for business logic
- **Integration Tests**: All API endpoints and service interactions
- **End-to-End Tests**: Critical user workflows
- **Performance Tests**: Load testing and response time validation

#### Testing Tools
- **Python**: pytest, pytest-asyncio, pytest-mock
- **Frontend**: Jest, React Testing Library, Cypress
- **API Testing**: pytest-httpx, requests-mock
- **Performance**: Locust, Artillery

### Deployment Strategy

#### Environment Management
- **Development**: Local Docker Compose setup
- **Staging**: Cloud deployment with test data
- **Production**: Multi-region deployment with load balancing

#### CI/CD Pipeline
- **Code Quality**: Automated linting and type checking
- **Testing**: Automated test suite execution
- **Security**: Vulnerability scanning and dependency updates
- **Deployment**: Automated deployment with rollback capabilities

## Technical Debt & Considerations

### Current Limitations
- **AI Response Quality**: Dependent on external LLM providers
- **Curriculum Updates**: Manual process for curriculum changes
- **Offline Functionality**: Limited offline capabilities
- **Multilingual Support**: Initial focus on English only

### Future Enhancements
- **Advanced AI**: Fine-tuned models for educational content
- **Curriculum Automation**: Automated curriculum update process
- **Enhanced Offline**: Full offline functionality with sync
- **Global Expansion**: Multi-language and multi-curriculum support

### Risk Mitigation
- **AI Service Failures**: Multiple provider fallback strategy
- **Data Loss**: Comprehensive backup and recovery procedures
- **Performance Issues**: Monitoring and auto-scaling
- **Security Breaches**: Regular security audits and penetration testing

This technical context provides the foundation for building a robust, scalable, and secure Cambridge AI Tutor platform that meets all performance, security, and reliability requirements. 