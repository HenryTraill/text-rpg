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

### Frontend
- **React**: Modern UI framework
- **TypeScript**: Type-safe JavaScript development
- **Material-UI**: Component library for consistent design
- **WebSocket Client**: Real-time game updates

### Infrastructure
- **Process Manager**: Service orchestration with systemd/supervisor
- **Nginx**: Reverse proxy and load balancing
- **Monitoring**: Comprehensive logging and metrics
- **Authentication**: JWT-based security with role management

## 📋 Prerequisites

- **Python 3.11+**
- **PostgreSQL 15+**
- **Redis 7+**
- **Node.js 18+** and **npm/yarn**
- **Git**

## 🛠️ Quick Start

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YourUsername/text-rpg.git
   cd text-rpg
   ```

2. **Set up PostgreSQL Database**
   ```bash
   # Create database
   createdb text_rpg_db
   
   # Create user (optional)
   psql -c "CREATE USER text_rpg_user WITH PASSWORD 'your_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE text_rpg_db TO text_rpg_user;"
   ```

3. **Start Redis**
   ```bash
   redis-server
   ```

4. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis connection strings
   ```

6. **Initialize Database**
   ```bash
   alembic upgrade head
   python scripts/init_game_data.py
   ```

7. **Start Backend Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Frontend Setup (in new terminal)**
   ```bash
   cd frontend
   npm install
   npm start
   ```

9. **Access the application**
   - Game Interface: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Admin Panel: http://localhost:8000/admin

## 📚 Project Documentation

### Core Documentation
- **[Game Design Document](GAME_DESIGN_DOCUMENT.md)**: Complete technical specification
- **[Technical Diagrams](TECHNICAL_DIAGRAMS.md)**: Mermaid diagrams for system architecture
- **[Implementation Guide](PROJECT_IMPLEMENTATION_GUIDE.md)**: Development roadmap and team structure
- **[Development Setup](DEVELOPMENT_SETUP.md)**: Detailed setup instructions

### Development Planning
- **[GitHub Issues Breakdown](GITHUB_ISSUES_BREAKDOWN.md)**: Issues #1-17 (Infrastructure & Social Systems)
- **[Additional GitHub Issues](GITHUB_ISSUES_ADDITIONAL.md)**: Issues #18-35 (Advanced Features & Polish)

## 🏗️ Project Structure

```
text-rpg/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── api/               # API route definitions
│   │   ├── core/              # Core configuration and security
│   │   ├── models/            # SQLModel database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic services
│   │   └── utils/             # Utility functions
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   ├── scripts/               # Utility scripts
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variables template
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   ├── stores/            # State management
│   │   └── utils/             # Utility functions
│   ├── public/                # Static assets
│   └── package.json           # Node.js dependencies
├── docs/                      # Additional documentation
└── README.md                  # This file
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Set up test database
createdb text_rpg_test_db
# Run integration tests
cd backend
pytest tests/integration/ -v
```

## 🚀 Deployment

### Production Deployment
1. **Set up production servers**
   - PostgreSQL instance with proper configuration
   - Redis instance for caching and pub/sub
   - Application server (VPS or cloud instance)

2. **Configure environment**
   ```bash
   # Set production environment variables
   export DATABASE_URL="postgresql://user:pass@localhost:5432/text_rpg_prod"
   export REDIS_URL="redis://localhost:6379"
   export SECRET_KEY="your-production-secret-key"
   export ENVIRONMENT="production"
   ```

3. **Deploy backend**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Run migrations
   alembic upgrade head
   
   # Start with process manager
   gunicorn app.main:app --bind 0.0.0.0:8000 --workers 4
   ```

4. **Deploy frontend**
   ```bash
   # Build for production
   npm run build
   
   # Serve with nginx or static file server
   ```

5. **Set up reverse proxy (nginx)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location / {
           root /path/to/frontend/build;
           try_files $uri $uri/ /index.html;
       }
   }
   ```

### Environment Variables
Key environment variables required:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing secret
- `ENVIRONMENT`: Deployment environment (development/staging/production)
- `DEBUG`: Enable debug mode (false for production)

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