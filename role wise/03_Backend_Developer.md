# Contribution Artifact: Backend Developer

## Role Overview
**Role:** Backend Developer
**Domain:** Core API, Database Architecture, & Request Orchestration
**Primary Focus:** Architecting the FastAPI application, designing the SQLite persistence layer, and orchestrating the complex interactions between the frontend, the ML pipelines, and external LLM services.

## Key Responsibilities & Elaborated Technical Contributions

### 1. FastAPI Application Architecture & Routing
* **Evidence:** `backend/main.py`
* **Elaborated Details:** You served as the primary architect for the CarePath backend, utilizing FastAPI to construct a high-performance, asynchronous REST API. You configured robust Cross-Origin Resource Sharing (CORS) middleware to allow seamless communication with the Next.js dual-frontend (Hospital and Insurance). You structured the API routes logically, implementing strict Pydantic models for data validation to ensure that incoming requests and outgoing responses adhere to a guaranteed schema. Furthermore, you implemented comprehensive error handling, ensuring that unhandled exceptions, database lockups, or ML pipeline failures are caught and returned as clean HTTP 400/500 errors with actionable JSON messages.

### 2. Database Management & Persistence Layer
* **Evidence:** `backend/patient_journey_db.py`, `scripts/migrate_sqlite_to_postgres.py`
* **Elaborated Details:** You designed and implemented the relational persistence layer using SQLite via Python's `sqlite3` DB-API, prioritizing zero-configuration portability for the hackathon environment. You wrote highly optimized CRUD operations for patients, journey events, and risk prediction snapshots. Recognizing the need for ML feature tracing, you designed the schema to support temporal "point-in-time" queries, allowing the system to track exactly when and why a patient's risk score changed. To ensure production readiness, you also developed a migration script (`migrate_sqlite_to_postgres.py`) proving that the application can seamlessly scale to a robust PostgreSQL cluster.

### 3. Patient & Event Endpoint Development
* **Evidence:** `/api/patients`, `/api/patients/{id}`, `/api/patients/{id}/events` in `main.py`
* **Elaborated Details:** You built the core data-serving endpoints that power both the Hospital and Insurance dashboards. Instead of forcing the frontend to download the entire database and filter it locally, you implemented search, pagination, and risk-level filtering directly at the database query level. This significantly reduced network payload sizes and ensured the application remains highly performant even as the patient population scales into the tens of thousands.

### 4. Advanced Workflow Orchestration (ML + LLM)
* **Evidence:** `/api/upload-report`, `/api/patients/{id}/add-event` in `main.py`
* **Elaborated Details:** Your most complex contribution was acting as the central orchestrator for the platform's AI capabilities. You built the `/api/upload-report` endpoint, which operates as a massive, synchronized transaction. When a clinical PDF is uploaded, your endpoint: 1) Calls the Integration Engineer's PyPDF logic to extract text, 2) Transmits the text to the Groq LLM for clinical reasoning, 3) Parses the returned JSON feature updates, 4) Updates the patient's feature vector in the database, 5) Invokes the ML Engineer's V2 ensemble to generate a new risk score, and 6) Commits the new journey event and score to the database. You ensured this complex chain executes reliably and rolls back gracefully if any single component fails.

## Technologies Utilized
- **FastAPI:** Chosen for its asynchronous capabilities, auto-generated OpenAPI documentation, and speed.
- **SQLite / DB-API:** Utilized for lightweight, serverless relational data storage, with a clear path to PostgreSQL.
- **Uvicorn:** The ASGI web server used to run the FastAPI application.
- **Pydantic:** Enforced strict type-checking and data serialization at the API boundaries.

## Strategic Integration Points
- You provided the foundational data and API contracts required by **Frontend Developer 1 & 2**.
- You embedded and executed the serialized ensemble models provided by the **ML Engineer**.
- You provided the framework in which the **Integration Engineer**'s external API calls (Groq, SMS) operate.
