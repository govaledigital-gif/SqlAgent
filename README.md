# SQL Architect - The Data Agent

An AI-powered SQL query translator that converts natural language descriptions into optimized MySQL queries. Built with FastAPI, React, Google Gemini API, and Docker with enterprise-grade security.

## Features

- 🤖 **AI-Powered SQL Generation**: Translate natural language prompts to optimized SQL
- 🔐 **Enterprise Security**: Zero-hardcoded credentials, comprehensive audit logging
- 🚀 **Scalable Architecture**: Hexagonal architecture ready for multi-tenancy
- 📊 **Query History**: Track all generated queries per user
- 🔑 **JWT Authentication**: Secure user authentication with bcrypt
- ⚡ **Redis Caching**: High-performance schema caching
- 📝 **SQL Validation**: Whitelist-based command validation, SQL injection prevention
- 🎯 **Rate Limiting**: Per-IP rate limiting to prevent abuse
- 📋 **Audit Trail**: Structured logging with automatic sensitive data masking

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
# Add your OPENAI_API_KEY to back/.env

# Frontend
cp frontend/.env.example frontend/.env
```

3. **Start all services**
```bash
docker-compose up --build
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MySQL**: localhost:3306

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

## 📚 API Endpoints

### Generate SQL
```
POST /api/v1/generate-sql
Content-Type: application/json

{
  "prompt": "Get all users who made purchases in the last 30 days",
  "schema": null  // Optional, auto-fetched if not provided
}

Response:
{
  "query": "SELECT DISTINCT u.* FROM users u JOIN orders o ON u.id = o.user_id WHERE o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
}
```

### Get Database Schema
```
GET /api/v1/schema

Response:
{
  "tables": ["users", "orders", "products"],
  "schema": "Database Schema:\n\nTable: users\n  - id: INTEGER NOT NULL\n..."
}
```

### List Tables
```
GET /api/v1/tables

Response:
{
  "tables": ["users", "orders", "products"]
}
```

### Get Table Schema
```
GET /api/v1/schema/{table_name}

Response:
{
  "table": "users",
  "schema": "Table: users\n  - id: INTEGER NOT NULL\n..."
}
```

## 🔧 Configuration

### Backend Environment Variables
```env
DATABASE_URL=mysql+pymysql://root:root@db/projects_db
OPENAI_API_KEY=sk-...
```

### Frontend Environment Variables
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## 🤖 How It Works

1. **User Input**: User describes desired SQL query in natural language via React UI
2. **Schema Fetch**: Backend retrieves current database schema from MySQL
3. **AI Processing**: LangChain + GPT-4 generates optimized SQL from description + schema
4. **Response**: Generated SQL is returned and displayed in frontend with copy option
5. **User Action**: User can copy SQL and execute it in their database

## 📦 Tech Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: MySQL 8.0
- **AI**: LangChain + OpenAI GPT-4
- **Server**: Uvicorn

### Frontend
- **Library**: React 18
- **HTTP Client**: Axios
- **Routing**: React Router v6

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose

## 🎯 Features

✅ Convert natural language to SQL queries  
✅ Automatic database schema detection  
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