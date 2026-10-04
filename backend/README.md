# Personalized AI Health Assistant — Backend Service

FastAPI-powered asynchronous backend service for preliminary disease-risk assessment, AI-assisted health navigation, and healthcare facilities lookup.

---

## Architecture Overview

```text
backend/
│
├── app/
│   ├── main.py              # Application entry point, CORS, OpenAPI metadata
│   ├── api/
│   │   ├── dependencies.py  # Dependency injection (e.g. DB session)
│   │   └── routes/
│   │       ├── health.py    # Health check endpoint (/api/health)
│   │       └── __init__.py  # Route aggregation
│   │
│   ├── core/
│   │   ├── config.py        # Pydantic BaseSettings management (.env loader)
│   │   ├── database.py      # SQLAlchemy engine, session maker, Base
│   │   └── security.py      # Password hashing (bcrypt) and JWT encoding
│   │
│   ├── schemas/
│   │   ├── health.py        # Pydantic request/response models
│   │   └── __init__.py
│   │
│   ├── models/              # SQLAlchemy ORM models (Phase 2)
│   ├── services/            # Business logic layer (Phase 3+)
│   ├── ai/                  # AI/LLM integration (Phase 5+)
│   ├── prediction/          # ML model & risk scoring (Phase 7+)
│   ├── healthcare/          # Healthcare provider locator & maps (Phase 12)
│   └── utils/               # Common helper utilities
│
├── tests/
│   └── test_health.py       # Pytest test cases
│
├── requirements.txt         # Production & development dependencies
├── .env.example             # Configuration template
├── .env                     # Local configuration (uncommitted)
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.13)
- PostgreSQL (for Phase 2+ persistent database)

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env` and configure parameters:
```bash
cp .env.example .env
```

### 5. Run the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Verify Endpoints
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 7. Run Unit Tests
```bash
pytest tests/ -v
```

---

## Safety & Medical Disclaimer
This backend service is part of an academic prototype intended strictly for preliminary health-risk assessment and healthcare navigation assistance. It does not provide medical diagnoses, treatment recommendations, or prescriptions. Always consult a licensed healthcare professional for medical conditions.
