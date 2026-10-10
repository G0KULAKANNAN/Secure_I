# QuantumShield

**Quantum-Vulnerable Cryptography Discovery and PQC Migration Prioritisation Platform**

QuantumShield is a cybersecurity web application built to help organizations discover potentially quantum-vulnerable cryptographic mechanisms (such as RSA, ECC, and Diffie-Hellman), collect traceable evidence, evaluate risk using explainable mathematical formulas, and prioritize migration to official NIST Post-Quantum Cryptography (PQC) standards (such as ML-KEM, ML-DSA, and SLH-DSA).

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
├── backend/                    # Python Flask Modular REST API
│   ├── app.py                  # Application factory (create_app)
│   ├── config.py               # Central configuration (dev, test, prod)
│   ├── requirements.txt        # Pinned Python dependencies
│   ├── quantumshield/
│   │   ├── extensions.py       # CORS & Database extensions
│   │   ├── api/                # Versioned REST API endpoints (/api/v1/)
│   │   │   ├── health.py       # Health check & version metadata
│   │   │   └── assets.py       # Asset Inventory CRUD, search & filter API
│   │   ├── core/               # Constants, exceptions & validation
│   │   ├── models/             # Domain data models
│   │   │   └── asset.py        # Asset data model and validation rules
│   │   ├── storage/            # SQLite repository layer
│   │   │   ├── database.py     # SQLite connection & idempotent schema init
│   │   │   └── repositories.py # Parameterised SQL AssetRepository
│   │   ├── services/           # Application service layer
│   │   ├── scanner/            # X.509, Source & TLS scanner engines (Stages 3-5)
│   │   ├── risk/               # Explainable risk calculation engine (Stage 7)
│   │   ├── migration/          # NIST PQC recommendation & planner (Stages 8-9)
│   │   └── reports/            # Audit & CSV/JSON report generator (Stage 10)
│   └── tests/                  # Automated pytest suite
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_database.py
│       └── test_assets.py
│
├── frontend/                   # React + TypeScript + Vite + Tailwind CSS
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.ts          # Vite build config with backend API proxy
│   ├── tailwind.config.js      # Deep midnight navy theme tokens
│   └── src/
│       ├── main.tsx            # Application DOM root
│       ├── App.tsx             # React-Router setup for all 8 views
│       ├── api/                # Typed API clients (health, assets)
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

## Technology Stack

- **Frontend**:
  - React 18, TypeScript, Vite
  - Tailwind CSS (Deep midnight navy `#0a0e17` theme with electric cyan and violet accents)
  - Lucide Icons
  - Chart.js (Dashboard visualizations)
  - React Router DOM (Client-side routing)
- **Backend**:
  - Python 3.11+ (Flask Application Factory)
  - SQLite with `PRAGMA foreign_keys = ON;` and parameterized queries
  - Python `cryptography` library for X.509 certificate parsing
  - Python `ssl` and `socket` for authorized TLS inspection
  - Pytest (Automated backend testing)

---

## Asset Inventory Database Schema (SQLite)

The `assets` table persists all registered cryptographic assets with strict check constraints:

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | Unique asset identifier (e.g. `ast_xxxx`) |
| `name` | TEXT | NOT NULL | Asset display name |
| `asset_type` | TEXT | NOT NULL CHECK (server, website, application, certificate, database, other) | Category of asset |
| `environment`| TEXT | NOT NULL CHECK (development, testing, staging, production) | Deployment stage |
| `hostname` | TEXT | NULL | Fully qualified domain name or internal host |
| `ip_address` | TEXT | NULL | Host IP address (IPv4 / IPv6) |
| `owner` | TEXT | NULL | Responsible team or individual |
| `description`| TEXT | NULL | Cryptographic scope and notes |
| `criticality`| TEXT | NOT NULL DEFAULT 'medium' CHECK (low, medium, high, critical) | Business impact level |
| `status` | TEXT | NOT NULL DEFAULT 'active' CHECK (active, inactive, under_review) | Operational state |
| `created_at` | TEXT | NOT NULL | ISO 8601 UTC timestamp |
| `updated_at` | TEXT | NOT NULL | ISO 8601 UTC timestamp |

---

## Asset REST API Endpoints

All endpoints support both `/api/v1/assets` and `/api/assets` route conventions:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/assets` | List assets (supports `search`, `asset_type`, `environment`, `criticality`, `status`, `limit`, `offset`) |
| `GET` | `/api/v1/assets/<id>` | Retrieve a single asset by ID (404 if missing) |
| `POST` | `/api/v1/assets` | Register a new asset (201 Created with JSON payload) |
| `PUT` | `/api/v1/assets/<id>` | Update an existing asset (200 OK) |
| `DELETE` | `/api/v1/assets/<id>` | Delete an asset permanently (200 OK) |

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

# Run automated tests
python -m pytest tests/ -v

# Start the Flask API server (runs on http://127.0.0.1:5000)
python app.py
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

## Development Roadmap

| Milestone | Description | Status |
|---|---|---|
| **Stage 1** | **Frontend/Backend Foundation, API Factory & UI/UX** | **Completed** |
| **Stage 2** | **Database Models & Cryptographic Asset Inventory** | **Completed** |
| **Stage 3** | X.509 Certificate Scanner (PEM/DER) | Planned |
| **Stage 4** | Source Code & Configuration Static Scanner | Planned |
| **Stage 5** | Authorised TLS Endpoint Scanner (with SSRF guard) | Planned |
| **Stage 6** | Unified Findings, Correlation & Evidence Store | Planned |
| **Stage 7** | Explainable Risk Assessment Engine | Planned |
| **Stage 8** | PQC Migration Recommendation Engine (NIST FIPS 203/204/205) | Planned |
| **Stage 9** | Migration Task Planner & Dependency Tracking | Planned |
| **Stage 10**| Interactive Dashboard Charts & Audit Reports | Planned |
| **Stage 11**| Security Hardening & Integration Test Suite | Planned |
| **Stage 12**| Complete Documentation & Hackathon Demonstration | Planned |

---

## Git Workflow

Follow conventional commit formats:
- `chore: initialize QuantumShield web application`
- `feat: implement database and asset inventory`
- `test: add unit and integration test coverage`
