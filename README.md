# 🚀 UdyamAI - AI-Powered Micro-Entrepreneurship Platform

UdyamAI is a state-of-the-art, AI-powered platform designed to empower micro-entrepreneurs in rural and semi-urban regions. It performs hyper-localized business feasibility studies, detailed financial calculations, geo-spatial market analysis, and government scheme matching to evaluate viability and simplify the path to capital.

---

## 🌟 Core Features

- **💡 Multi-Criteria Scheme Matching Engine**: Matches entrepreneur profiles against NSFDC, Central, and State (e.g., Maharashtra) schemes. Calculates exact subsidy amounts, contribution margins, and maximum loan availability.
- **🗺️ Localized Geographic & Market Analysis**: Uses PostGIS coordinates and radial searches to gauge nearby village populations, local competitors, market hubs, and infrastructural facilities.
- **📊 Business Feasibility Scorer & SWOT Advisor**: Generates a unified risk rating, opportunities checklist, and automated SWOT (Strengths, Weaknesses, Opportunities, Threats) matrices.
- **🧮 Interactive Financial Planners**: Calculators for project costs, EMI streams, moratorium variations, working capital limits, cash flow statements, break-even limits, and repayment margins.
- **💬 Multilingual AI Advisor**: RAG-enhanced interactive chatbot supporting English, Hindi (हिंदी), and Marathi (मराठी) to answer complex regulatory, financial, and policy queries with citations.
- **📄 PDF Business Plan Generator**: Renders beautifully formatted feasibility and financial reports ready to present to banks.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, Tailwind CSS, TypeScript, Zustand |
| **Backend** | FastAPI, Python 3.11, SQLModel / SQLAlchemy, Pydantic v2 |
| **Database** | PostgreSQL, PostGIS extension |
| **AI / RAG** | OpenAI / Google Gemini API, Vector Embeddings |
| **Containers & Proxy** | Docker & Docker Compose (V2), Nginx |
| **Linting** | Ruff (Python), ESLint (TypeScript) |

---

## 📁 Directory Structure Overview

```
UdyamAI/
├── .github/workflows/       # CI/CD pipeline definitions
├── docs/                    # System architecture, schemas, and specs
├── frontend/                # Next.js web application
│   └── src/                 # Source code (pages, components, lib)
├── backend/                 # FastAPI web services and analysis modules
│   ├── app/                 # Application code
│   └── tests/               # Backend test suite (pytest)
├── data/                    # Raw/processed geographic and market demographic data
├── knowledge_base/          # Scheme PDFs, policy files, guidelines for RAG
├── scripts/                 # Data importing, scheme ingestion, and RAG indexing scripts
└── infrastructure/          # Dockerfiles, Nginx configurations, database schemas
```

---

## ⚡ Getting Started

### 📋 Prerequisites

Ensure you have the following installed on your local machine:
- [Docker & Docker Compose V2](https://www.docker.com/products/docker-desktop) — use `docker compose` (space, not hyphen)
- [Node.js 18+](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Make](https://www.gnu.org/software/make/) (for running Makefile commands)

---

### 🔑 1. Environment Configuration

1. Copy the example environment file at the root:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` to supply your API keys and configuration parameters:
   - **`ENV`**: Set to `"production"` in production deployments, or `"development"` / `"test"` for local dev.
   - **`DATABASE_URL`**: DB connection string.
   - **`OPENAI_API_KEY`** or **`GEMINI_API_KEY`**: LLM API tokens for the advisor.
   - **`SECRET_KEY`**: JWT secret for authentication.

> [!IMPORTANT]
> **Production Security Mandate**:
> * If **`ENV`** is set to `"production"`, you **must** explicitly supply a strong, custom value for **`SECRET_KEY`** (e.g. generated via `openssl rand -hex 32`). If `SECRET_KEY` is missing in a production environment, the backend will raise a `ValueError` validation error and fail to boot.
> * In `"development"` or `"test"` modes, the application will fallback to a documented fallback key (`dev_secret_key_fallback`) if `SECRET_KEY` is omitted, though explicit configuration is still highly recommended.


---

### 🐳 2. Quickstart with Docker Compose

To spin up all services (Frontend, Backend, PostgreSQL with PostGIS) together:

```bash
# Build and start all containers in detached mode
docker compose up -d --build

# Verify services are healthy
docker compose ps
```

The services will be accessible at:
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000) (Swagger docs at `/docs`)
- **Nginx Gateway**: [http://localhost](http://localhost) (Proxies `/api` to backend, `/` to frontend)

> **Note:** Services use health checks — the backend won't start until the database is ready, and the frontend won't start until the backend is healthy.

---

### 💻 3. Manual Development Setup

If you prefer to run services individually for debugging:

#### A. Database Initialization
Spin up only the database container:
```bash
docker compose up -d database
```

#### B. Backend Setup
1. Create a virtual environment and activate it:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install ruff  # For linting (optional, also used in CI)
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### C. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install Node dependencies:
   ```bash
   npm ci    # Deterministic install from lockfile
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

---

## ⚙️ Data Ingestion & Ingest Pipeline

To initialize geo-demographic profiles and scheme databases, use the provided scripts.

### 🗺️ Ingesting Geographic & Market Data
Ensure your database is running and run the import scripts:
```bash
# Activate virtual environment in backend, then run:
python scripts/data/import_locations.py
python scripts/data/import_population.py
python scripts/data/import_markets.py
```

### 📚 RAG Knowledge Base Ingestion
To parse and index PDFs or scheme policies placed inside `knowledge_base/schemes/`:
```bash
python scripts/rag/ingest_documents.py
python scripts/rag/rebuild_embeddings.py
```

---

## 🔄 CI/CD Pipeline

Every push to `main`/`dev` and every pull request to `main` triggers automated checks:

### Frontend CI (`.github/workflows/frontend.yml`)
| Step | What it checks |
|---|---|
| Install dependencies | `npm ci` — deterministic install from lockfile |
| Lint | `npm run lint` — ESLint catches code style and error issues |
| Typecheck | `tsc --noEmit` — TypeScript strict mode catches type errors |
| Build | `npm run build` — Next.js compilation validates the full build |

### Backend CI (`.github/workflows/backend.yml`)
| Step | What it checks |
|---|---|
| Install dependencies | `pip install` + `ruff` |
| Lint | `ruff check` + `ruff format --check` — Python code style and formatting |
| Import validation | `python -c "from app.main import app"` — catches syntax/import errors |
| Tests | `pytest -v` — runs the backend test suite |

### E2E / Integration Tests (`.github/workflows/tests.yml`)
| Step | What it checks |
|---|---|
| Build images | `docker compose build` — validates Dockerfiles build correctly |
| Start services | `docker compose up -d` — spins up full stack with health checks |
| Health checks | Waits for database and backend to report healthy |
| Integration tests | `pytest` inside the running backend container |
| Teardown | `docker compose down -v` — always cleans up (even on failure) |

---

## 🧪 Testing

### Running All Tests
```bash
make test
```

### Running Backend Tests Only
```bash
cd backend && pytest -v
```

### Running Frontend Tests Only
```bash
cd frontend && npm test
```

---

## 🔍 Code Quality & Linting

This project enforces code quality through automated linting in CI and optional pre-commit hooks.

### Linting

```bash
# Lint everything (frontend + backend)
make lint

# Lint only backend
cd backend && ruff check . && ruff format --check .

# Lint only frontend
cd frontend && npm run lint
```

### Auto-format

```bash
# Auto-format everything
make format

# Auto-format only backend
cd backend && ruff format .
```

### Type Checking

```bash
# Check TypeScript types
make typecheck
# or
cd frontend && npx tsc --noEmit
```

### Pre-commit Hooks (Optional)

Install pre-commit hooks to get local feedback before every commit:

```bash
pip install pre-commit
pre-commit install
```

This will automatically run Ruff (Python) and ESLint (TypeScript) on changed files.

### Tools Used

| Tool | Language | Purpose |
|---|---|---|
| **Ruff** | Python | Linting + formatting |
| **ESLint** | TypeScript/JavaScript | Linting |
| **TypeScript** | TypeScript | Type checking (strict mode) |
| **pytest** | Python | Testing |
| **Jest** | TypeScript/JavaScript | Testing |

---

## ❓ Troubleshooting

| Problem | Solution |
|---|---|
| `docker-compose: command not found` | Use `docker compose` (V2 syntax, no hyphen) |
| `pytest` shows 0 tests | Ensure you're in the `backend/` directory — tests are in `backend/tests/` |
| Frontend build fails with type errors | Run `npx tsc --noEmit` to see all type errors |
| `npm ci` fails | Delete `node_modules` and `package-lock.json`, then run `npm install` to regenerate the lockfile |
| Port 5432 already in use | Stop local PostgreSQL or change the port mapping in `docker-compose.yml` |
| Backend can't connect to database | Run `docker compose ps` to verify the database container is healthy before the backend starts |
| Ruff not found | Install it: `pip install ruff` |
| Pre-commit hooks not running | Run `pre-commit install` after cloning the repo |

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
