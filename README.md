# Medieval Text MMO RPG

A comprehensive medieval fantasy text-based massively multiplayer online role-playing game built with modern web technologies. Experience turn-based combat, skill-based character progression, guild systems, and large-scale content in a persistent open world.

## 🎮 Game Features

### Core Gameplay
- **Turn-based Combat**: Strategic 1v1 battles and large-scale boss encounters with auto-complete functionality
- **Classless Progression**: Skill-based character development across Combat, Gathering, Crafting, and Social categories
- **Open World**: Coordinate-based world system supporting thousands of concurrent players
- **Dynamic Quests**: Mix of procedurally generated tasks and handcrafted storylines

### Social Systems
- **Guilds**: Comprehensive guild management with roles, permissions, and activities
- **Parties**: Group formation for adventures and shared objectives
- **Mentorship**: Experienced players guide newcomers through structured programs
- **Real-time Chat**: Multiple channels including global, local, guild, party, and private messaging
- **PvP Systems**: Competitive combat with rankings and territory control

### Economic Features
- **Advanced Crafting**: Complex item creation with quality tiers and specializations
- **Resource Gathering**: Multiple gathering skills with rare material discovery
- **Trading Systems**: Player-to-player trading and NPC merchants
- **Auction House**: Server-wide marketplace for item exchange

### Endgame Content
- **Raid Encounters**: Large-scale PvE content requiring coordination
- **Territory Control**: Guild-based area ownership with strategic benefits
- **Seasonal Events**: Limited-time content with exclusive rewards
- **Achievement System**: Comprehensive progression tracking

## 🚀 Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **SQLModel**: Modern ORM with Pydantic integration
- **PostgreSQL**: Primary database for persistent data
- **Redis**: Caching and session management
- **WebSocket**: Real-time communication
- **Celery**: Background task processing
- **Docker**: Containerized deployment

### Frontend
- **React**: Modern UI framework
- **TypeScript**: Type-safe JavaScript development
- **Material-UI**: Component library for consistent design
- **WebSocket Client**: Real-time game updates

### Infrastructure
- **Docker Compose**: Development environment orchestration
- **Nginx**: Reverse proxy and load balancing
- **Monitoring**: Comprehensive logging and metrics
- **Authentication**: JWT-based security with role management

## 📋 Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.11+** (for local development)
- **Node.js 18+** and **npm/yarn** (for frontend development)
- **PostgreSQL 15+** (if running without Docker)
- **Redis 7+** (if running without Docker)

## 🛠️ Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/YourUsername/text-rpg.git
   cd text-rpg
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python scripts/init_game_data.py
   ```

5. **Access the application**
   - Game Interface: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Admin Panel: http://localhost:8000/admin

### Local Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📚 Project Documentation

### Core Documentation
- **[Game Design Document](GAME_DESIGN_DOCUMENT.md)**: Complete technical specification
- **[Technical Diagrams](TECHNICAL_DIAGRAMS.md)**: Mermaid diagrams for system architecture
- **[Implementation Guide](PROJECT_IMPLEMENTATION_GUIDE.md)**: Development roadmap and team structure

### Development Planning
- **[GitHub Issues Breakdown](GITHUB_ISSUES_BREAKDOWN.md)**: Issues #1-17 (Infrastructure & Social Systems)
- **[Additional GitHub Issues](GITHUB_ISSUES_ADDITIONAL.md)**: Issues #18-35 (Advanced Features & Polish)

## 🏗️ Project Structure

```
text-rpg/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API route definitions
│   │   │   ├── core/              # Core configuration and security
│   │   │   ├── models/            # SQLModel database models
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── services/          # Business logic services
│   │   │   └── utils/             # Utility functions
│   │   ├── alembic/               # Database migrations
│   │   ├── tests/                 # Backend tests
│   │   └── requirements.txt       # Python dependencies
│   ├── frontend/                   # React frontend application
│   │   ├── src/
│   │   │   ├── components/        # React components
│   │   │   ├── pages/             # Page components
│   │   │   ├── services/          # API services
│   │   │   ├── stores/            # State management
│   │   │   └── utils/             # Utility functions
│   │   ├── public/                # Static assets
│   │   └── package.json           # Node.js dependencies
│   ├── docker-compose.yml         # Docker orchestration
│   ├── .env.example               # Environment variables template
│   └── docs/                      # Additional documentation
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## 🚀 Deployment

### Production Deployment
1. Set up production environment variables
2. Configure PostgreSQL and Redis instances
3. Build and deploy Docker containers
4. Run database migrations
5. Set up monitoring and logging

### Environment Variables
Key environment variables required:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing secret
- `ENVIRONMENT`: Deployment environment (development/staging/production)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new features
- Update documentation as needed
- Follow conventional commit messages

## 🐛 Issue Tracking

This project uses GitHub Issues for tracking bugs, features, and development tasks:

- **Bug Reports**: Use the bug report template
- **Feature Requests**: Use the feature request template  
- **Development Tasks**: Reference the project milestones

## 📈 Development Timeline

The project is structured in 6 main epics over 10-12 months:

1. **Infrastructure & Setup** (4-6 weeks)
2. **Core Foundation** (8-12 weeks)
3. **Social Systems** (8-10 weeks)
4. **Advanced Features** (10-12 weeks)
5. **Polish & Scale** (6-8 weeks)
6. **Documentation & DevOps** (Ongoing)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Performance Targets

- Support 10,000+ concurrent players
- Sub-100ms API response times
- 99.9% uptime
- Real-time chat with <50ms latency
- Daily automated backups

## 📞 Support

- **Documentation**: Check the docs/ directory
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for general questions

---

**Ready to embark on your medieval adventure?** Follow the Quick Start guide above and join the realm! 