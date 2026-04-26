# Defect Management System

## 1. Project Overview

Defect Management System is a FastAPI backend for tracking vessel equipment defects during a guarantee or warranty workflow. It is built for administrators, guarantee department users, overseeing teams, and vendors who need to register vessels and equipment, report defects, assign work to vendors, update defect status, and preserve an audit history of defect activity.

Key value propositions:

- Role-based access control for Admin, GuaranteeDept, OverseeingTeam, and Vendor users.
- Vessel, vendor, equipment, and defect management through REST APIs.
- JWT-based authentication with access and refresh tokens.
- Automatic database table creation and seed data for roles and an initial admin account.
- Defect history logging for creation, vendor assignment, and status changes.
- In-progress feature branch work for OCR/LLM-based defect ingestion from PDFs, emails, and forms.

## 2. Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Table of Contents](#2-table-of-contents)
- [3. High-Level Architecture](#3-high-level-architecture)
- [4. Repository Structure](#4-repository-structure)
- [5. Core Functionality](#5-core-functionality)
- [6. Data Pipelines & Data Flow](#6-data-pipelines--data-flow)
- [7. API & Interface Reference](#7-api--interface-reference)
- [8. Configuration & Environment Variables](#8-configuration--environment-variables)
- [9. Local Development Setup](#9-local-development-setup)
- [10. Testing Strategy](#10-testing-strategy)
- [11. DevSecOps Pipeline](#11-devsecops-pipeline)
- [12. Infrastructure & IaC](#12-infrastructure--iac)
- [13. Observability](#13-observability)
- [14. Security & Compliance](#14-security--compliance)
- [15. Contributing](#15-contributing)
- [16. Changelog & Versioning](#16-changelog--versioning)
- [17. License](#17-license)

## 3. High-Level Architecture

The project is a containerized monolithic REST API. FastAPI exposes the HTTP interface, Pydantic schemas validate request and response payloads, SQLAlchemy models map domain entities to PostgreSQL tables, and Docker Compose runs the backend, PostgreSQL, and pgAdmin for local development.

```mermaid
flowchart TD
    Client[API client / Swagger UI] -->|HTTP + Bearer JWT| FastAPI[FastAPI application]
    FastAPI --> Routers[app/api routers]
    Routers --> Auth[app/core auth and security]
    Routers --> Schemas[app/schemas Pydantic contracts]
    Routers --> Services[app/services business helpers]
    Routers --> Models[app/models SQLAlchemy ORM]
    Services --> Models
    Models --> DB[(PostgreSQL defect_management)]
    FastAPI --> Seed[Startup seed: roles and admin]
    Seed --> DB
    PgAdmin[pgAdmin] --> DB
```

Layer mapping:

| Layer | Directories / files | Responsibility |
| --- | --- | --- |
| Presentation / interface | `app/api/`, `app/main.py` | REST routes, application startup, router registration |
| Business logic | `app/services/`, selected checks in `app/api/` | Defect history logging, role-gated workflow rules |
| Auth and security | `app/core/` | JWT creation/validation, password hashing, role requirements |
| Data access | `app/models/`, `app/db/` | SQLAlchemy models, engine/session management, seed data |
| Infrastructure | `Dockerfile`, `docker-compose.yml`, `.github/workflows/pipeline.yml` | Container build, local service orchestration, CI security pipeline |

External systems and third-party services:

- PostgreSQL 15, provided by Docker Compose.
- pgAdmin 4, provided by Docker Compose for database inspection.
- GitHub Actions for CI security checks.
- Safety, pip-audit, Bandit, Gitleaks, Docker Scout, Trivy, and OWASP ZAP in CI.
- In `feature/defect-ingestion-system`: Ollama, EasyOCR, Tesseract OCR, OpenCV, pypdf, pdf2image, Pillow, and NumPy are referenced by source files.
- No third-party business APIs or cloud services are referenced in the source code.

## 4. Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── pipeline.yml          # GitHub Actions DevSecOps pipeline
├── app/
│   ├── api/                      # FastAPI route modules
│   ├── core/                     # JWT auth, password hashing, role checks
│   ├── db/                       # SQLAlchemy base, session, dependency, seed data
│   ├── models/                   # SQLAlchemy ORM table definitions
│   ├── schemas/                  # Pydantic request/response contracts
│   ├── services/                 # Reusable business helpers; feature branch adds ingestion services
│   ├── init_db.py                # Manual table-creation helper
│   └── main.py                   # FastAPI application entry point
├── venv/                         # Local virtual environment; not application source
├── .env                          # Local environment variables; currently contains secrets
├── .gitignore                    # Git ignore rules
├── Dockerfile                    # Backend container image definition
├── docker-compose.yml            # Local PostgreSQL, backend, and pgAdmin stack
└── requirements.txt              # Python runtime dependencies
```

Significant source directories:

- `app/api/`: Route handlers for authentication, users, vessels, vendors, equipment, defects, and assignments.
- `app/models/`: Database schema expressed as SQLAlchemy ORM classes.
- `app/schemas/`: Pydantic models that define accepted request bodies and serialized responses.
- `app/core/`: Cross-cutting auth and password security helpers.
- `app/db/`: Database connection setup, request-scoped session dependency, and startup seed logic.
- `app/services/`: Shared defect-history logging.
- `app/services/ingestion/`: Present on `feature/defect-ingestion-system`; draft OCR, PDF, and LLM extraction services.

## 5. Core Functionality

### Authentication and Authorization

Implemented in `app/api/auth.py`, `app/core/auth.py`, and `app/core/security.py`.

Users log in with email and password. Passwords are verified with bcrypt via Passlib. Successful login returns an access token and refresh token. Protected endpoints use HTTP Bearer authentication and role checks through `get_current_user()` and `required_roles()`.

Visible limitations:

- `SECRET_KEY` is loaded directly from environment variables; there is no dedicated secrets manager integration.
- Token expiry values are hardcoded: 60 minutes for access tokens and 7 days for refresh tokens.
- `get_current_user()` catches all exceptions broadly and returns a generic `401`.

### User and Role Management

Implemented in `app/api/user.py`, `app/models/user.py`, `app/models/role.py`, `app/schemas/user.py`, and `app/db/seed.py`.

The application seeds four roles: `Admin`, `GuaranteeDept`, `OverseeingTeam`, and `Vendor`. It also seeds an initial admin account. Admin users can create, retrieve, update, and delete users.

Visible limitations:

- There is no endpoint to list all users.
- There is no endpoint to list roles.
- `organisation` is unique on the `users` table, which may prevent multiple users from belonging to the same organisation.

### Vessel Management

Implemented in `app/api/vessel.py`, `app/models/vessel.py`, and `app/schemas/vessel.py`.

Guarantee department users can create vessels. Guarantee department users can view all vessels; overseeing teams can view vessels for their own organisation. Vessel creation validates that the guarantee period date is not before the delivery date.

Visible limitations:

- `create_vessel()` does not set the `name` column even though `models.vessel.Vessel` defines it.
- One route checks for role name `Overseeing Team`, but seeded roles use `OverseeingTeam`.

### Vendor Management

Implemented in `app/api/vendor.py`, `app/models/vendor.py`, and `app/schemas/vendor.py`.

Admin and guarantee department users can create and update vendor master records. Admin, guarantee department, and overseeing team users can read vendor records. Admin users can delete vendors.

Visible limitations:

- The vendor master table is separate from vendor login accounts. Defect assignment uses a `User` with role `Vendor`, while equipment links to the `vendor` master table.
- `created_at` exists on the vendor model but is not set during vendor creation.

### Equipment Management

Implemented in `app/api/equipment.py`, `app/models/equipment.py`, `app/models/equipment_master.py`, and `app/schemas/equipment.py`.

Equipment is split into equipment types (`equipment_master`) and installed equipment instances (`equipment`). Guarantee department users can create equipment types and equipment records. Equipment records link a vessel, a vendor master record, an equipment type, and a serial number.

Visible limitations:

- Read access for equipment is limited to GuaranteeDept and OverseeingTeam.
- Equipment list endpoints do not filter by overseeing team organisation.

### Defect Management

Implemented in `app/api/defect.py`, `app/models/defect.py`, `app/schemas/defect.py`, and `app/services/history_logger.py`.

Overseeing team users create defects against equipment on vessels in their organisation. Defects start with status `OPEN`. Defect reads are role-scoped: GuaranteeDept sees all, OverseeingTeam sees organisation-scoped records, and Vendor sees only assigned defects. Status updates are role-gated:

- `ASSIGNED`: GuaranteeDept only.
- `IN_PROGRESS`, `RESOLVED`: Vendor only.
- `ACCEPTED`, `REJECTED`, `CLOSED`: GuaranteeDept only.

Visible limitations:

- Accepted statuses are not constrained with an enum.
- The status transition rules check role permissions but do not enforce a strict state machine.
- `cost_to_shipyard` and `date_of_liquidation` exist in the model but are not exposed in create/update schemas.

### Vendor Assignment and History

Implemented in `app/api/defect_assignment.py`, `app/models/vendor_assignment.py`, `app/models/defect_history.py`, `app/schemas/defect_assignment.py`, `app/schemas/defect_history.py`, and `app/services/history_logger.py`.

Guarantee department users assign an `OPEN` defect to a user whose role is `Vendor`. Assignment changes the defect status to `ASSIGNED` and logs both vendor assignment and status update history events.

Visible limitations:

- The router prefix is misspelled as `/assigments`.
- The list-all-assignments endpoint checks for `Guarantee Dept`, but seeded roles use `GuaranteeDept`.
- `VendorAssignment.assignment_date`, `status`, and `vessel_id` are defined in the model but not set by the assignment endpoint.

### In-Progress Feature Branch: Defect Ingestion System

Branch: `feature/defect-ingestion-system`.

This branch adds the start of an ingestion pipeline intended to accept defect reports from PDFs, emails, and structured forms, extract text, and convert that text into structured defect-report data with an offline LLM.

Files added or changed on the branch:

- `app/services/ingestion/pdf_handler.py`: Detects digital PDFs, extracts embedded text with `pypdf`, and falls back to OCR for scanned PDFs.
- `app/services/ingestion/ocr_service.py`: Uses EasyOCR as the primary OCR engine and Tesseract as a fallback when confidence is low.
- `app/services/ingestion/llm_service.py`: Uses Ollama with `llama3:8b-instruct-q4_K_M` to extract structured JSON from raw defect-report text.
- `app/services/ingestion/orchestrator.py`: Added but currently empty.
- `app/api/ingestion.py`: Added but currently empty.
- `app/schemas/ingestion.py`: Currently contains the draft ingestion API routes and request schemas.
- `app/main.py`: Imports and includes an `ingestion` router.
- `app/models/vendor_assignment.py`: Adds another `vendor_id` column in the branch diff, which conflicts with the existing `vendor_id` column already present on `main`.

Intended draft endpoints from the branch:

- `POST /ingestion/pdf`: Accepts a PDF upload and processes it through the ingestion orchestrator.
- `POST /ingestion/email`: Accepts an email subject, body, and optional base64 PDF attachments.
- `POST /ingestion/form`: Accepts structured form data.

Visible limitations before merge:

- The branch references `IngestionOrchestrator`, but `app/services/ingestion/orchestrator.py` is empty.
- `app/main.py` imports `ingestion` from `api`, but `app/api/ingestion.py` is empty while route code currently lives in `app/schemas/ingestion.py`.
- `llm_service.py` imports `DefectExtraction` from `app.schemas.ingestion`, but that schema is not defined in the branch version of `app/schemas/ingestion.py`.
- New dependencies such as `ollama`, `easyocr`, `pytesseract`, `opencv-python`, `pypdf`, `pdf2image`, `Pillow`, and `numpy` are referenced in code but are not added to `requirements.txt`.
- Tesseract and Poppler system binaries may be required at runtime for OCR/PDF conversion, but they are not installed in the Dockerfile.
- The branch does not yet persist extracted defect data into the existing `defect` tables.

## 6. Data Pipelines & Data Flow

On `main`, no batch, streaming, ETL, ELT, ML, queue-based, or event-driven data pipelines are implemented. Data flow is synchronous request/response REST traffic backed by PostgreSQL.

The `feature/defect-ingestion-system` branch introduces a draft manual ingestion pipeline. It is not complete enough to run end-to-end yet, but the intended flow is visible in the added services.

Primary application data flow:

```mermaid
flowchart LR
    Login[POST /auth/login] --> Token[Access + refresh token]
    Token --> CreateDefect[POST /defects/]
    CreateDefect --> Validate[Vessel, equipment, organisation validation]
    Validate --> Defect[(defect table)]
    CreateDefect --> History1[(defect_history CREATED)]
    Token --> Assign[POST /assigments/]
    Assign --> Assignment[(vendor_assignment table)]
    Assign --> StatusAssigned[(defect.status = ASSIGNED)]
    Assign --> History2[(defect_history VENDOR_ASSIGNED / STATUS_UPDATE)]
    Token --> UpdateStatus[PATCH /defects/{id}/status]
    UpdateStatus --> StatusChange[(defect table)]
    UpdateStatus --> History3[(defect_history STATUS_UPDATE)]
```

Draft ingestion pipeline on `feature/defect-ingestion-system`:

| Pipeline | Source | Transformations | Sink | Trigger | SLA / throughput |
| --- | --- | --- | --- | --- | --- |
| PDF defect ingestion | Uploaded PDF | Digital text extraction with `pypdf`; scanned PDF conversion with `pdf2image`; OCR with EasyOCR and Tesseract fallback; planned LLM extraction with Ollama | Currently returns extracted/structured data; no database write implemented | Manual REST call to `POST /ingestion/pdf` | Not specified |
| Email defect ingestion | Email subject/body and optional base64 PDF attachments | Planned orchestrator processing of body and attachments | Currently draft API only; no persistence shown | Manual REST call to `POST /ingestion/email` | Not specified |
| Form defect ingestion | Structured JSON form payload | Planned orchestrator processing | Currently draft API only; no persistence shown | Manual REST call to `POST /ingestion/form` | Not specified |

Most critical draft ingestion flow:

```mermaid
flowchart LR
    Upload[POST /ingestion/pdf] --> PDF[PDFHandler]
    PDF --> Digital[pypdf text extraction]
    Digital --> Meaningful{Meaningful text?}
    Meaningful -->|Yes| RawText[Raw text + confidence 1.0]
    Meaningful -->|No| Images[pdf2image pages]
    Images --> OCR[EasyOCR]
    OCR --> Confidence{Confidence >= 0.6?}
    Confidence -->|Yes| RawText
    Confidence -->|No| Tesseract[Tesseract fallback]
    Tesseract --> RawText
    RawText --> LLM[Ollama LLM extraction]
    LLM --> JSON[Structured defect JSON]
```

Data stores:

| Store | Technology | Schema highlights | Retention | Access patterns |
| --- | --- | --- | --- | --- |
| `defect_management` | PostgreSQL 15 | `users`, `role`, `vessel`, `vendor`, `equipment_master`, `equipment`, `defect`, `vendor_assignment`, `defect_history` | Not specified in code | Direct SQLAlchemy ORM reads/writes per API request |
| Docker volume `postgres_data` | Docker named volume | PostgreSQL data directory | Persists across container restarts until volume removal | Used by local Docker Compose database |
| Docker volume `pgadmin_data` | Docker named volume | pgAdmin state | Persists across container restarts until volume removal | Used by local pgAdmin service |

Data contracts:

- Request and response contracts are enforced by Pydantic schemas in `app/schemas/`.
- Database shape is enforced by SQLAlchemy models in `app/models/`.
- FastAPI generates OpenAPI documentation automatically at runtime.
- No Avro, Protobuf, JSON Schema files, or checked-in OpenAPI specification are present.
- On `feature/defect-ingestion-system`, the intended `DefectExtraction` Pydantic contract is referenced but not yet implemented.

## 7. API & Interface Reference

The public interface is a REST API served by FastAPI. When the application is running locally, generated docs are available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

All routes except `/`, `/auth/login`, and `/auth/refresh` require a Bearer token unless otherwise noted.

### Root

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | No | Health-style root message |

Response:

```json
{ "message": "API is running" }
```

### Auth

| Method | Path | Auth | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/auth/login` | No | `UserLogin` | Access and refresh token | `401` invalid credentials |
| `POST` | `/auth/refresh` | No | Query/body parameter `refresh_token: string` | New access token | `401` invalid token |

Login request:

```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

Login response:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

### Users

| Method | Path | Auth role | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/users/` | Admin | `UserCreate` | Message | `400`, `401`, `403` |
| `GET` | `/users/{user_id}` | Admin | None | `UserResponse` | `401`, `403` |
| `PATCH` | `/users/{user_id}` | Admin | `UserUpdate` | Message | `400`, `401`, `403`, `404` |
| `DELETE` | `/users/{user_id}` | Admin | None | Message | `400`, `401`, `403`, `404` |

Create user request:

```json
{
  "name": "Guarantee User",
  "email": "guarantee@example.com",
  "password": "change-me",
  "role_id": 2,
  "organisation": "Shipyard A"
}
```

User response:

```json
{
  "user_id": 1,
  "name": "Admin",
  "email": "admin@example.com",
  "role_id": 1,
  "organisation": "SYSTEM"
}
```

### Vessels

| Method | Path | Auth role | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/vessels/` | GuaranteeDept | `VesselCreate` | `VesselResponse` | `401`, `403`, validation errors |
| `GET` | `/vessels/` | GuaranteeDept, OverseeingTeam | None | List of `VesselResponse` | `400`, `401`, `403` |
| `GET` | `/vessels/{vessel_id}` | GuaranteeDept, OverseeingTeam intended | None | `VesselResponse` | `401`, `403`, `404` |

Create vessel request:

```json
{
  "series_name": "Series A",
  "shipyard_yard_number": 1001,
  "delivery_date": "2026-01-15",
  "status": "DELIVERED",
  "date_till_guarantee_period": "2027-01-15",
  "organisation": "Shipyard A"
}
```

### Vendors

| Method | Path | Auth role | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/vendors/` | Admin, GuaranteeDept | `VendorCreate` | `VendorResponse` | `400`, `401`, `403` |
| `GET` | `/vendors/?skip=0&limit=10` | Admin, GuaranteeDept, OverseeingTeam | None | List of `VendorResponse` | `401`, `403` |
| `GET` | `/vendors/{vendor_id}` | Admin, GuaranteeDept, OverseeingTeam | None | `VendorResponse` | `401`, `403`, `404` |
| `PATCH` | `/vendors/{vendor_id}` | Admin, GuaranteeDept | `VendorUpdate` | Message | `400`, `401`, `403`, `404` |
| `DELETE` | `/vendors/{vendor_id}` | Admin | None | Message | `401`, `403`, `404` |

Create vendor request:

```json
{
  "name": "Acme Marine",
  "email": "service@acme.example",
  "phone": "+1-555-0100",
  "address": "Dock 4"
}
```

### Equipment

| Method | Path | Auth role | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/equipment/types` | Admin, GuaranteeDept | `EquipmentTypeCreate` | `EquipmentTypeResponse` | `401`, `403` |
| `GET` | `/equipment/types` | Admin, GuaranteeDept, OverseeingTeam | None | List of `EquipmentTypeResponse` | `401`, `403` |
| `POST` | `/equipment/` | GuaranteeDept | `EquipmentCreate` | `EquipmentResponse` | `401`, `403`, `404` |
| `GET` | `/equipment/` | GuaranteeDept, OverseeingTeam | None | List of `EquipmentResponse` | `401`, `403` |
| `GET` | `/equipment/vessel/{vessel_id}` | GuaranteeDept, OverseeingTeam | None | List of `EquipmentResponse` | `401`, `403` |

Create equipment type request:

```json
{
  "name": "Pump",
  "manufacturer": "Acme Marine",
  "model_no": "PM-100"
}
```

Create equipment request:

```json
{
  "vessel_id": 1,
  "vendor_id": 1,
  "equipment_type_id": 1,
  "serial_no": "SN-001"
}
```

### Defects

| Method | Path | Auth role | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/defects/` | OverseeingTeam | `DefectCreate` | `DefectResponse` | `400`, `401`, `403`, `404` |
| `GET` | `/defects/` | Any authenticated role, role-scoped | None | List of `DefectResponse` | `401`, `403` |
| `GET` | `/defects/{defect_id}` | GuaranteeDept, matching OverseeingTeam, assigned Vendor | None | `DefectResponse` | `401`, `403`, `404` |
| `PATCH` | `/defects/{defect_id}/status` | Status-dependent | `DefectStatusUpdate` | Message | `401`, `403`, `404` |
| `GET` | `/defects/{defect_id}/history` | GuaranteeDept, matching OverseeingTeam, assigned Vendor | None | List of `DefectHistoryResponse` | `401`, `403`, `404` |

Create defect request:

```json
{
  "vessel_id": 1,
  "equipment_id": 1,
  "description": "Hydraulic pressure drops during operation"
}
```

Defect response:

```json
{
  "vessel_id": 1,
  "equipment_id": 1,
  "description": "Hydraulic pressure drops during operation",
  "status": "OPEN"
}
```

Update status request:

```json
{
  "status": "IN_PROGRESS"
}
```

### Assignments

The assignment router is currently mounted at the misspelled prefix `/assigments`.

| Method | Path | Auth role | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/assigments/` | GuaranteeDept | `AssignmentCreate` | `AssignmentResponse` | `400`, `401`, `403`, `404` |
| `GET` | `/assigments/` | Intended GuaranteeDept, currently checks `Guarantee Dept` | None | List of `AssignmentResponse` | `401`, `403` |
| `GET` | `/assigments/vendor_assignment` | Vendor | None | List of `AssignmentResponse` | `401`, `403` |

Assignment request:

```json
{
  "defect_id": 1,
  "vendor_id": 4
}
```

Assignment response:

```json
{
  "assignment_id": 1,
  "defect_id": 1,
  "vendor_id": 4,
  "assigned_by": 2
}
```

### Ingestion API Draft on `feature/defect-ingestion-system`

These endpoints are present as draft route code on the feature branch, but the branch is not yet runnable end-to-end because the orchestrator and structured extraction schema are incomplete.

| Method | Path | Auth role | Request | Response | Errors |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/ingestion/pdf` | Any authenticated user | Multipart file field `file`, must end with `.pdf` | Orchestrator result | `400`, `401`, `500` |
| `POST` | `/ingestion/email` | Any authenticated user | `EmailIngestionRequest` | Orchestrator result | `401`, `500` |
| `POST` | `/ingestion/form` | Any authenticated user | `FormIngestionRequest` | Orchestrator result | `401`, `500` |

Email ingestion request:

```json
{
  "subject": "Defect report for vessel Series A",
  "body": "Hydraulic pump pressure drops during operation.",
  "attachments": ["<base64-encoded-pdf>"]
}
```

Form ingestion request:

```json
{
  "data": {
    "vessel_name": "Series A",
    "system_equipment": "Hydraulic pump",
    "defect_description": "Pressure drops during operation"
  }
}
```

## 8. Configuration & Environment Variables

### App and Auth

| Variable | Required | Default | Description | Example |
| --- | --- | --- | --- | --- |
| `SECRET_KEY` | Required | None | JWT signing key. Secret; do not commit real values. | `change-me-in-local-dev` |

### Ingestion Feature Branch

The `feature/defect-ingestion-system` branch hardcodes the Ollama model name in `app/services/ingestion/llm_service.py` rather than reading it from an environment variable.

| Variable | Required | Default | Description | Example |
| --- | --- | --- | --- | --- |
| Not configured | N/A | `llama3:8b-instruct-q4_K_M` in code | Ollama model used for local structured extraction | Recommended future variable: `OLLAMA_MODEL=llama3:8b-instruct-q4_K_M` |

### Database

| Variable | Required | Default | Description | Example |
| --- | --- | --- | --- | --- |
| `DATABASE_URL` | Required | None | SQLAlchemy database connection string. Secret when it contains credentials. | `postgresql://postgres:postgres@localhost:5432/defect_management` |

### Docker Compose Defaults

| Variable / setting | Required | Default in compose | Description |
| --- | --- | --- | --- |
| `POSTGRES_USER` | Yes | `postgres` | PostgreSQL username for local Compose database |
| `POSTGRES_PASSWORD` | Yes | `postgres` | PostgreSQL password for local Compose database; secret outside local dev |
| `POSTGRES_DB` | Yes | `defect_management` | PostgreSQL database name |
| `PGADMIN_DEFAULT_EMAIL` | Yes | `admin@admin.com` | Local pgAdmin login email |
| `PGADMIN_DEFAULT_PASSWORD` | Yes | `admin` | Local pgAdmin password; secret outside local dev |

Important: the checked-in `.env` currently contains database credentials and a JWT secret. For production use, replace these values and keep real secrets out of version control.

## 9. Local Development Setup

### Prerequisites

- Python 3.11, matching the Dockerfile and GitHub Actions workflow.
- Docker and Docker Compose.
- Git.

### Option A: Run with Docker Compose

1. Create or update `.env` for local development:

   ```env
   DATABASE_URL=postgresql://postgres:postgres@db:5432/defect_management
   SECRET_KEY=change-me-in-local-dev
   ```

2. Start the full local stack:

   ```bash
   docker compose up --build
   ```

3. Open the services:

   - API: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - pgAdmin: `http://localhost:5050`

4. Log in with the seeded admin account after startup:

   ```json
   {
     "email": "admin@example.com",
     "password": "admin123"
   }
   ```

### Option B: Run the API directly on the host

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run PostgreSQL locally or with Compose:

   ```bash
   docker compose up db pgadmin
   ```

4. Use a host-accessible database URL:

   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/defect_management
   SECRET_KEY=change-me-in-local-dev
   ```

5. Start the API:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Tests, Linters, Formatters, and Type Checks

No test runner, linter, formatter, type checker, or pre-commit configuration is present in the repository. The CI pipeline installs security tools dynamically, but it does not run unit tests, formatting checks, or type checks.

Security checks can be run manually with tools used by CI:

```bash
pip install pip-audit bandit
pip-audit
bandit -r .
```

To try the `feature/defect-ingestion-system` work once it is completed, additional Python packages and system tools will be required. The branch currently references OCR and LLM dependencies in source code but does not add them to `requirements.txt` or the Dockerfile.

## 10. Testing Strategy

No automated test suite is present in the repository. There are no unit, integration, end-to-end, contract, performance, or chaos tests checked in, and no coverage threshold is configured.

Current verification coverage:

| Tier | Status | Notes |
| --- | --- | --- |
| Unit tests | Not configured | No test files or test runner configuration found |
| Integration tests | Not configured | Database-backed route behavior is not covered by tests |
| End-to-end tests | Not configured | No browser or API e2e tests found |
| Contract tests | Partially implicit | FastAPI and Pydantic enforce runtime request/response contracts |
| Security tests | Configured in CI | Safety, pip-audit, Bandit, Gitleaks, Docker Scout, Trivy, OWASP ZAP |
| Coverage | Not configured | No coverage tool or threshold found |

Recommended first test additions:

- Auth login and refresh tests.
- Role-based authorization tests for each router.
- Defect lifecycle tests covering create, assign, status update, and history.
- Regression tests for role-name mismatches and the `/assigments` route typo.
- Feature-branch tests for PDF text extraction, OCR fallback behavior, LLM JSON validation, and ingestion endpoint authentication.

## 11. DevSecOps Pipeline

The GitHub Actions pipeline is defined in `.github/workflows/pipeline.yml`.

Triggers:

- Push to `main`.
- Any pull request.

Jobs and stages:

| Job | Depends on | Stages |
| --- | --- | --- |
| `devsecops` | None | Checkout, set up Python 3.11, install dependencies, Safety scan, pip-audit scan, Bandit SAST |
| `secret_scan` | None | Checkout, Gitleaks secret detection |
| `image_scan` | `devsecops`, `secret_scan` | Checkout, Docker build, Docker login, Docker Scout scan, Trivy image scan |
| `dast_scan` | `image_scan` | Checkout, Docker build, run container on port 8000, OWASP ZAP baseline scan |

Security tooling:

- SCA / dependency scanning: Safety and pip-audit.
- SAST: Bandit.
- Secret scanning: Gitleaks.
- Container scanning: Docker Scout and Trivy.
- DAST: OWASP ZAP baseline scan.
- IaC scanning: not configured.

Pipeline behavior:

- Most security scan steps use `continue-on-error: true`, so findings do not necessarily fail the build.
- Docker image is built locally as `myapp:latest`.
- Docker login uses `DOCKER_USER` and `DOCKER_PASS` repository secrets.
- Safety uses `SAFETY_API_KEY`.
- No artifact publishing or image push is configured.
- No deployment stage is configured.
- No environment promotion path, gates, rollback procedure, or deploy-time observability hooks are present.

## 12. Infrastructure & IaC

No cloud infrastructure or Infrastructure-as-Code tool is present. There are no Terraform, Pulumi, CDK, Helm, Kustomize, Kubernetes, or cloud provider configuration files in the repository.

Local infrastructure is provided by Docker Compose:

| Service | Image/build | Ports | Purpose |
| --- | --- | --- | --- |
| `db` | `postgres:15` | `5432:5432` | PostgreSQL database |
| `backend` | Built from `Dockerfile` | `8000:8000` | FastAPI application |
| `pgadmin` | `dpage/pgadmin4` | `5050:80` | Local database administration |

State and persistence:

- PostgreSQL data persists in the Docker volume `postgres_data`.
- pgAdmin data persists in the Docker volume `pgadmin_data`.
- No backup, restore, disaster recovery, remote state, or locking strategy is defined.

## 13. Observability

Logging:

- The application does not configure a logging framework.
- Uvicorn/FastAPI default server logs are available when running the application.
- Seed functions print simple startup messages to stdout.
- Structured logging is not configured.

Metrics:

- No metrics library or Prometheus/OpenTelemetry metrics exporter is configured.
- No dashboards are referenced.

Tracing:

- No tracing instrumentation is configured.
- Trace propagation headers are not handled explicitly.

Alerting:

- No alert rules, runbooks, or incident management integration are present.

Health checks:

- `GET /` returns `{"message": "API is running"}` and can serve as a basic liveness check.
- No dedicated readiness endpoint is implemented.

## 14. Security & Compliance

Authentication and authorization:

- Authentication uses JWT bearer tokens.
- Passwords are hashed with bcrypt through Passlib.
- Authorization uses role checks in FastAPI dependencies.
- Supported seeded roles are `Admin`, `GuaranteeDept`, `OverseeingTeam`, and `Vendor`.

Secrets management:

- Secrets are read from environment variables using `python-dotenv`.
- No Vault, AWS Secrets Manager, SOPS, or equivalent secrets manager is configured.
- The current `.env` contains secret material and should be treated as local-only.

Network security:

- Docker Compose exposes PostgreSQL on `5432`, the API on `8000`, and pgAdmin on `5050`.
- No VPC, security group, mTLS, firewall, or ingress configuration is present.

