# QuantumShield

**Automation-First Cryptographic Exposure Discovery and PQC Migration Prioritisation Platform**

QuantumShield is an automation-first cybersecurity platform built to help organizations discover potentially quantum-vulnerable cryptographic mechanisms (such as RSA, ECC, and Diffie-Hellman), collect traceable evidence, evaluate risk using explainable mathematical formulas, and prioritize migration to official NIST Post-Quantum Cryptography (PQC) standards (such as ML-KEM, ML-DSA, and SLH-DSA).

> [!IMPORTANT]
> **Quantum Vulnerability & Risk Disclaimer**:
> - Identification of a potential quantum vulnerability is **not proof of compromise** or immediate system breach.
> - Prioritization scores and risk estimates **do not forecast or predict when a cryptographically relevant quantum computer will become available**.
> - QuantumShield provides defensive risk assessment and structured migration planning based on empirical evidence and NIST PQC guidance.

---

## Architecture Overview

QuantumShield follows a modular, decoupled cybersecurity application architecture:

```
quantumshield/
├── backend/                    # Python Flask Modular REST API & Automation Engine
│   ├── app.py                  # Application factory (create_app)
│   ├── config.py               # Central configuration (dev, test, prod)
│   ├── requirements.txt        # Pinned Python dependencies
│   ├── quantumshield/
│   │   ├── extensions.py       # CORS & Database extensions
│   │   ├── api/                # Versioned REST API endpoints (/api/v1/)
│   │   │   ├── health.py       # Health check & version metadata
│   │   │   ├── assets.py       # Asset Inventory CRUD, search & filter API
│   │   │   └── jobs.py         # Persistent scan job lifecycle & worker queue API
│   │   ├── core/               # Constants, exceptions & validation
│   │   ├── models/             # Domain data models
│   │   │   ├── asset.py        # Asset data model and validation rules
│   │   │   └── job.py          # ScanJob data model and status state machine
│   │   ├── storage/            # SQLite repository layer
│   │   │   ├── database.py     # SQLite connection & idempotent schema init
│   │   │   ├── repositories.py # Parameterised SQL AssetRepository
│   │   │   └── job_repository.py# Parameterised SQL JobRepository & queue manager
│   │   ├── services/           # Background workers & automation services
│   │   │   └── job_worker.py   # Thread-safe BackgroundJobManager & worker pool
│   │   ├── scanner/            # X.509, Source & TLS scanner engines (Milestone 2)
│   │   ├── risk/               # Explainable risk calculation engine
│   │   ├── migration/          # NIST PQC recommendation & planner
│   │   └── reports/            # Audit & CSV/JSON report generator
│   └── tests/                  # Automated pytest suite
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_database.py
│       ├── test_assets.py
│       └── test_jobs.py
│
├── frontend/                   # React + TypeScript + Vite + Tailwind CSS
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.ts          # Vite build config with backend API proxy
│   ├── tailwind.config.js      # Deep midnight navy theme tokens
│   └── src/
│       ├── main.tsx            # Application DOM root
│       ├── App.tsx             # React-Router setup for all 8 views
│       ├── api/                # Typed API clients (health, assets, jobs)
│       ├── components/         # Layout & common UI components
│       └── pages/              # Overview, Assets, Scanner, Findings, etc.
│
├── sample_data/                # Sample test assets & configurations
├── docs/                       # Architecture, threat model, & risk model specs
├── .gitignore
├── .env.example
├── README.md
├── SECURITY.md
└── CONTRIBUTING.md
```

---

## Persistent Job Queue & Worker Architecture

Long-running scans run asynchronously without blocking Flask HTTP request handlers:

```
[Client / API Request]
         │  POST /api/v1/jobs
         ▼
[ScanJob Created (status='queued')] ──► SQLite (scan_jobs table)
         │
         ▼ (thread wake event)
[BackgroundJobManager] (Bounded Worker Threads: max_workers=3)
         │  claims job atomically (status='running', started_at)
         ▼
[Scanner / Handler Execution] (bounded timeouts & exponential backoff)
         │
         ├── Success ──► status='completed', progress=100%, completed_at
         │
         └── Failure ──► retry_count < max_retries ? status='queued' : status='failed'
```

- **Restart Recovery**: Stale jobs left in `running` status after an unexpected server restart are detected and recovered on startup.
- **Safety**: Atomic claiming in SQLite prevents duplicate worker threads from processing the same job.

---

## API Endpoints

### 1. Health & Metadata
- `GET /api/v1/health` (and `/api/health`): Service status, uptime, Python version.
- `GET /api/v1/version` (and `/api/version`): Version metadata and quantum risk disclaimer.

### 2. Asset Inventory
- `GET /api/v1/assets`: List assets (supports `search`, `asset_type`, `environment`, `criticality`, `status`, `limit`, `offset`).
- `GET /api/v1/assets/<id>`: Retrieve single asset.
- `POST /api/v1/assets`: Create asset.
- `PUT /api/v1/assets/<id>`: Update asset.
- `DELETE /api/v1/assets/<id>`: Delete asset.

### 3. Persistent Scan Jobs & Worker Engine
- `GET /api/v1/worker/status` (and `/api/worker/status`): Real-time worker engine health, thread pool activity, queue depth, and uptime metrics.
- `GET /api/v1/jobs` (and `/api/jobs`): List scan jobs (filters: `asset_id`, `status`, `job_type`, `limit`, `offset`).
- `GET /api/v1/jobs/<job_id>` (and `/api/jobs/<job_id>`): Retrieve specific job details, progress, output, and error payload.
- `POST /api/v1/jobs` (and `/api/jobs`): Enqueue a background job (`health_check`, `asset_validation`, `certificate_scan`, `tls_scan`, `static_scan`).
- `POST /api/v1/jobs/<job_id>/cancel` (and `/api/jobs/<job_id>/cancel`): Cooperatively cancel a pending, queued, or running job.
- `POST /api/v1/jobs/<job_id>/retry` (and `/api/jobs/<job_id>/retry`): Retry a failed or cancelled job with exponential backoff.

---

## Quickstart & Installation

### Prerequisites

- **Python**: 3.11 or newer (Python 3.13 tested)
- **Node.js**: v18 or newer (v22 tested) with npm

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run automated tests (all 33 unit and lifecycle tests pass)
python -m pytest tests/ -v

# Start the Flask API server with background workers
python app.py

# Optional: Run worker independently as a standalone daemon
python worker.py --workers 3
```

### 2. Frontend Setup

In a separate terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server (runs on http://localhost:5173)
npm run dev
```

The frontend will automatically proxy `/api/*` requests to the Flask backend running on port 5000.

---

## Automation Roadmap

1. **Milestone 1**: **Persistent Background Job Processing and Worker Framework** (**Completed**)
2. **Milestone 2**: Scan Orchestration (Certificate, TLS, Static Configuration)
3. **Milestone 3**: Scheduling & Asset Automation Policies
4. **Milestone 4**: Finding Deduplication & Change Detection
5. **Milestone 5**: Automatic Risk & PQC Recommendations
6. **Milestone 6**: Event Processing & Notification Engine
7. **Milestone 7**: Automation Control Center & Dashboard
8. **Milestone 8**: Security & Integration Test Suite
9. **Milestone 9**: Operational Documentation & Deployment
