# Contribution Artifact: Design & Architecture Engineer

## Role Overview
**Role:** Design & Architecture Engineer (Tech Lead)
**Domain:** System Architecture, Database Modeling, & Technical Coordination
**Primary Focus:** Designing the overall system topology, engineering the relational database schemas, defining the boundaries between Machine Learning and Generative AI, and orchestrating the technical strategy across the team.

## Key Responsibilities & Elaborated Technical Contributions

### 1. Dual-Stakeholder Application Architecture
* **Evidence:** `ED-frontend/components/carepath-app.tsx` (Core Routing Logic), `Documentation/carepath_integration_summary.md`
* **Elaborated Details:** You conceptualized and structured the CarePath platform to uniquely serve two distinct personas within a single cohesive application. You architected the routing and layout boundaries to separate the Clinical/Hospital staff interface (which focuses on micro-level, individual patient interventions and ED triage) from the Insurance/Actuarial staff interface (which focuses on macro-level population cohorts, trend visualizations, and ROI). This architectural decision allowed the frontend developers to reuse UI components while keeping the operational domains strictly isolated.

### 2. Relational Database Schema Design
* **Evidence:** `backend/patient_journey_db.py`
* **Elaborated Details:** A robust AI system requires a flawless data foundation. You designed the normalized relational schema that powers the application, consisting of interconnected tables: `patients`, `journey_events`, `risk_predictions`, and `feature_snapshots`. Recognizing that ML pipelines require historical context, you specifically designed the schema to support temporal "point-in-time" tracing. By separating feature snapshots from risk predictions and linking them to journey events, you ensured the system can perfectly reconstruct a patient's clinical state at any exact moment in the past. You also enforced strict foreign-key integrity to prevent orphaned records.

### 3. Orchestrating ML + LLM Workflow Boundaries
* **Evidence:** Architecture flow implemented in `backend/main.py`
* **Elaborated Details:** Your most critical architectural contribution was designing the "Closed-Loop Dynamic Rescoring" pattern. You recognized the inherent danger of using Generative AI (LLMs) to directly predict clinical risk, as LLMs are prone to hallucinations. Instead, you defined a strict architectural boundary: the LLM is used *exclusively* for unstructured text extraction (pulling clinical facts from PDFs), and those extracted facts are then passed to the deterministic, mathematically auditable ML V2 ensemble to generate the actual risk score. This design choice guarantees clinical safety, auditability, and regulatory compliance while still leveraging the power of GenAI.

### 4. Technical Documentation & Repository Coordination
* **Evidence:** `graphify-out/graph.json` (Dependency mapping), `Documentation/` folder.
* **Elaborated Details:** As the technical lead, you were responsible for the overall organization of the repository. You authored comprehensive technical summaries and mapped system dependencies to prevent merge conflicts and circular dependencies. You ensured that the project structure maintained a strict, logical separation of concerns—keeping ETL scripts, ML training pipelines, backend API logic, and frontend UI components in their respective, isolated directories. Your documentation serves as the blueprint for the entire team's development efforts.

## Technologies Utilized
- **System Design Principles:** Applied microservice-like separation of concerns within a monolithic repository to accelerate development while maintaining order.
- **Relational Data Modeling:** Employed strict normalization and temporal data design patterns to support advanced ML feature tracing.
- **Markdown & Diagramming:** Utilized as the primary medium for technical communication, ensuring all engineers understood the API contracts and data flows.

## Strategic Integration Points
- You dictate the technical strategy and API contracts for all other **7 roles**, ensuring the Frontend, Backend, ML, and Data teams are building toward a unified vision.
- You actively managed the boundaries between the **Integration Engineer**'s LLM tools and the **ML Engineer**'s predictive models, ensuring they functioned together seamlessly and safely.
