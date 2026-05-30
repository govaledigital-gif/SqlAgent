# Inventory Platform (MVP)

This repository now hosts a lightweight Inventory Management MVP. It provides authenticated CRUD for companies, warehouses and products, movement/receipt recording, stock overview and cycle counts. Built with FastAPI (backend), React (frontend), MySQL and Redis for caching.

## Features

- 🔐 **JWT Authentication**: Secure user authentication with bcrypt
- 🏢 **Companies & Warehouses**: Create and manage companies and warehouses
- 📦 **Products**: Add and list products
- 📥 **Movements / Receipts**: Record inventory movements and receipts
- 📊 **Stock Overview**: View current stock by product/location
- ✅ **Cycle Counts**: Create, record and close cycle counts with atomic adjustments
- ⚡ **Redis Caching**: Cache frequently accessed data
- 📋 **Audit Trail**: Structured logging for sensitive operations

## 📋 Project Structure

```
SqlAgent/
├── back/                    # Backend (Python/FastAPI)
│   ├── app/
│   │   ├── domain/         # Domain layer (User, QueryHistory)
│   │   ├── infrastructure/ # Infrastructure (repos, cache, logging)
│   │   ├── application/    # Application (controllers, services)
│   │   └── config/         # BaseSettings (centralized config)
│   ├── scripts/            # Validation & utility scripts
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── main.py
│   ├── .env                # Runtime secrets (git-ignored)
│   └── .env.example        # Configuration template
│
├── frontend/               # Frontend (React)
│   ├── src/
│   │   ├── components/
│   │   ├── controllers/
│   │   ├── services/
│   │   └── App.js
│   └── package.json
│
├── docker-compose.yml      # Multi-container orchestration
├── SECURITY.md             # Security architecture & best practices
└── README.md              # This file
```

## 🏗️ Architecture

### Hexagonal Architecture (Backend)

```
┌─────────────────────────────────────────┐
│  FastAPI Application (main.py)          │
├─────────────────────────────────────────┤
│  PORTS & ADAPTERS (app/application/)    │
│  - Controller: REST API                 │
│  - Service: Business logic              │
│  - Schemas: Validation                  │
│  - Auth: JWT & passwords                │
│  - Validator: SQL security              │
├─────────────────────────────────────────┤
│  DOMAIN (app/domain/)                   │
│  - User, QueryHistory entities          │
│  - Repository interfaces                │
├─────────────────────────────────────────┤
│  INFRASTRUCTURE (app/infrastructure/)   │
│  - Repositories (DB access)             │
│  - Cache (Redis)                        │
│  - Logging (Security logger)            │
│  - Audit (Middleware)                   │
├─────────────────────────────────────────┤
│  EXTERNAL SYSTEMS                       │
│  - MySQL, Redis, Google Gemini          │
└─────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Or locally: Python 3.11+, Node.js 18+, MySQL 8.0

### Quick Start with Docker

1. **Clone or setup the project**
```bash
cd SqlAgent
```

2. **Create environment files**
```bash
# Backend
cp back/.env.example back/.env

# Frontend
cp frontend/.env.example frontend/.env
```

3. **Start all services**
```bash
docker-compose up --build -d
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **MySQL**: localhost:3307

## 🚢 Deployment

The repository now includes a Docker publishing workflow for the backend and frontend images.

- On pushes to `main` or `master`, GitHub Actions builds and publishes both images to GHCR:
	- `ghcr.io/<owner>/sqlagent-backend`
	- `ghcr.io/<owner>/sqlagent-frontend`
- Images are tagged with the commit SHA and with `latest` on the default branch.

To run the stack locally with Docker Compose:
```bash
docker-compose up --build -d
```

For production, point `DATABASE_URL` to your managed MySQL instance and keep `REDIS_HOST`/`REDIS_PORT` aligned with the target environment.

## 🔒 Security

Security checks are split across CI and a dedicated workflow:

- `bandit` and `pip-audit` run in the main CI pipeline.
- Secret scanning runs in `.github/workflows/security.yml` through Gitleaks.

If you add a new secret or environment variable, update the relevant `.env.example` file instead of committing the secret itself.

### Local Development

#### Backend
```bash
cd back
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## 📚 API Overview

The backend exposes authenticated endpoints to manage inventory entities (companies, warehouses, products), to record movements and to manage cycle counts. Use the frontend Inventory UI for most operations.

## 🔧 Configuration

### Backend Environment Variables
```env
DATABASE_URL=mysql+pymysql://root:root@db/projects_db
```

### Frontend Environment Variables
```env
REACT_APP_API_URL=http://localhost:8001/api/v1
```

## 📦 Tech Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: MySQL 8.0
- **Server**: Uvicorn

### Frontend
- **Library**: React 18
- **HTTP Client**: Axios
- **Routing**: React Router v6

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose

## 🎯 Features

✅ Inventory management: companies/warehouses/products
✅ Movements/receipts and stock overview
✅ Cycle counts with atomic adjustments
✅ GPT-4 powered SQL optimization  
✅ Beautiful React UI with responsive design  
✅ Copy-to-clipboard functionality  
✅ Real-time table listing  
✅ API documentation (Swagger/OpenAPI)  
✅ CORS support for frontend communication  
✅ Docker containerization for easy deployment  

## 📝 Development Notes

### Adding New Endpoints
1. Define request/response models in `app/application/schemas.py`
2. Create service method in `app/application/service.py`
3. Add route handler in `app/application/controller.py`

### Extending Frontend Components
1. Create component in `src/components/`
2. Create corresponding controller in `src/controllers/` if needed
3. Use services from `src/services/` for API calls

## 🚨 Troubleshooting

### Database Connection Issues
- Ensure MySQL is running on port 3306
- Check DATABASE_URL in .env
- Verify credentials (default: root/root)

### OpenAI API Errors
- Verify OPENAI_API_KEY is set and valid
- Check API rate limits
- Ensure sufficient API credits

### Frontend-Backend Communication
- Check REACT_APP_API_URL in frontend .env
- Verify backend is running on port 8000
- Check browser console for CORS errors

## 📄 License

MIT License - feel free to use for your projects!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

---

**Made with ❤️ for the AI SQL generation revolution** 🚀