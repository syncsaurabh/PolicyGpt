# PolicyGPT Backend (Milestone 1)

Backend REST API for **PolicyGPT (PolicyGPT_Group_2)**, built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Alembic**, and **Pydantic**, featuring secure JWT authentication and Role-Based Access Control (RBAC).

---

## Technical Stack

- **Framework**: FastAPI
- **Language**: Python 3.12+
- **Database**: PostgreSQL (with SQLAlchemy 2.0 ORM)
- **Migrations**: Alembic
- **Data Validation & Settings**: Pydantic v2 & Pydantic Settings
- **Authentication**: OAuth2 / JWT (python-jose)
- **Password Security**: Bcrypt
- **Testing**: Pytest & HTTPX (TestClient)

---

## System Requirements

- Python 3.12 or newer
- PostgreSQL 14+ (or compatible Docker container)
- Git

---

## Installation & Setup

### 1. Navigate to the backend directory

```powershell
cd policy-gpt-backend
```

### 2. Create and activate a Python Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## Environment Configuration

Copy `.env.example` to `.env`:

```powershell
cp .env.example .env
```

Review or adjust `.env` variables as needed:

```env
PROJECT_NAME="PolicyGPT API"
VERSION="1.0.0"
API_V1_STR="/api/v1"
ENVIRONMENT="development"

# Secret key for JWT signing (change to a strong secret in production)
SECRET_KEY="dev-secret-key-change-in-production-policygpt"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
RESET_TOKEN_EXPIRE_MINUTES=15

# PostgreSQL Connection URL
DATABASE_URL="postgresql://postgres:password@localhost:5432/policygpt"

# Allowed CORS Origins for Angular Frontend
BACKEND_CORS_ORIGINS=["http://localhost:4200","http://127.0.0.1:4200"]
```

> **Note**: `.env` is listed in `.gitignore` and must never be committed to source control.

---

## Database Migrations (Alembic)

Ensure your PostgreSQL instance is running and the database `policygpt` exists:

```sql
CREATE DATABASE policygpt;
```

Run migrations to apply the initial schema:

```powershell
alembic upgrade head
```

To generate future migrations automatically when models change:

```powershell
alembic revision --autogenerate -m "description of changes"
```

To roll back a migration:

```powershell
alembic downgrade -1
```

---

## Running the Development Server

Start FastAPI with hot reload using Uvicorn:

```powershell
uvicorn app.main:app --reload --port 8000
```

The application will be accessible at:
- **API Base URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## Testing

Run the automated test suite with pytest:

```powershell
pytest -v
```

The test suite runs against an isolated SQLite test database and covers:
- System health checks
- User registration (valid input, duplicate email rejection, password criteria)
- Password hashing verification
- User authentication & login (JSON body and OAuth2 form data)
- JWT generation and claims validation
- Authenticated user profile retrieval (`GET /api/v1/users/me`) and safe updates (`PUT /api/v1/users/me`)
- Role-Based Access Control (RBAC) permissions (`ADMINISTRATOR`, `GOVERNMENT_OFFICIAL`, `CITIZEN`)
- Password reset foundation workflow (`forgot-password` and `reset-password`)

---

## API Documentation Summary

### Health Check
- `GET /health`: Health status check (`{"status": "ok"}`)

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Register a new user (`name`, `email`, `password`, `role`)
- `POST /api/v1/auth/login`: Authenticate and receive a signed JWT access token
- `POST /api/v1/auth/forgot-password`: Request password reset token
- `POST /api/v1/auth/reset-password`: Reset password using token

### Users & RBAC (`/api/v1/users`)
- `GET /api/v1/users/me`: Current authenticated user profile (Bearer token required)
- `PUT /api/v1/users/me`: Update profile fields (`name`)
- `GET /api/v1/users/admin/test`: Protected endpoint requiring `ADMINISTRATOR` role
- `GET /api/v1/users/government/test`: Protected endpoint requiring `GOVERNMENT_OFFICIAL` role

### User Roles
- `ADMINISTRATOR`
- `GOVERNMENT_OFFICIAL`
- `CITIZEN`
- `RESEARCHER`
- `ORGANIZATION`
- `GUEST_USER`

---

## Project Structure

```
policy-gpt-backend/
├── app/
│   ├── main.py                    # FastAPI entrypoint, CORS, routers, /health
│   ├── core/
│   │   ├── config.py              # Pydantic Settings & environment variables
│   │   ├── security.py            # Bcrypt hashing, JWT encode/decode, reset tokens
│   │   └── dependencies.py        # get_current_user, require_roles (RBAC)
│   ├── db/
│   │   ├── database.py            # SQLAlchemy engine, SessionLocal, Base, get_db
│   │   └── base.py                # Model registry for Alembic discovery
│   ├── models/
│   │   ├── user.py                # User model & UserRole enum
│   │   ├── policy.py              # Foundation model (Milestone 1 skeleton)
│   │   ├── scheme.py              # Foundation model (Milestone 1 skeleton)
│   │   ├── eligibility.py         # Foundation model (Milestone 1 skeleton)
│   │   ├── notification.py        # Foundation model (Milestone 1 skeleton)
│   │   ├── feedback.py            # Foundation model (Milestone 1 skeleton)
│   │   ├── report.py              # Foundation model (Milestone 1 skeleton)
│   │   ├── audit_log.py           # Foundation model (Milestone 1 skeleton)
│   │   └── search_history.py      # Foundation model (Milestone 1 skeleton)
│   ├── schemas/
│   │   ├── user.py                # UserRead, UserCreate, UserUpdate schemas
│   │   ├── auth.py                # Token, LoginRequest, PasswordReset schemas
│   │   ├── policy.py              # Foundation schemas
│   │   └── scheme.py              # Foundation schemas
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py            # /api/v1/auth routes
│   │       └── users.py           # /api/v1/users routes
│   └── services/
│       └── auth_service.py        # Business logic for auth, registration, login
├── alembic/
│   ├── env.py                     # Alembic env referencing Base.metadata & config
│   ├── script.py.mako
│   └── versions/                  # Initial migration revision
├── tests/
│   ├── conftest.py                # Test client & DB fixtures
│   ├── test_health.py             # Health check test
│   ├── test_auth.py               # Authentication tests
│   ├── test_users.py              # User profile tests
│   └── test_rbac.py               # RBAC permission tests
├── alembic.ini                    # Alembic configuration
├── .env.example                   # Example environment configuration
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Locked backend dependencies
└── README.md                      # Backend documentation
```
