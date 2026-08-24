# CarePath Navigator

CarePath Navigator is an intelligent healthcare care-management decision support platform. It predicts avoidable Emergency Department (ED) utilization and identifies navigation opportunities using machine learning ensembles and real-time clinical workflows.

This project was built for the **Cognizant × SMVEC Hackathon**.

## 🚀 Key Features

- **Predictive Risk Modeling (ML V2 Ensemble):** A highly optimized, data-centric machine learning ensemble (Logistic Regression, Random Forest, XGBoost) trained on robust clinical features to predict ED risk and care fragmentation.
- **Dynamic Care Journey:** A fully event-driven architecture that tracks longitudinal patient interactions and re-scores ML risk dynamically when new clinical reports are ingested or events occur.
- **Care Management Dashboard:** A modern, Next.js-powered responsive UI tailored for hospital care managers and insurance providers to monitor patient populations and high-risk alerts.
- **LLM-Powered Clinical Reasoning:** Utilizes Groq (Llama-based models) to parse uploaded clinical PDFs, extract actionable summaries, and assess care continuity impact instantly.
- **CarePath AI Navigation Assistant:** A floating chatbot featuring strict PHI guardrails, designed to help users navigate the dashboard features without compromising data security.
- **Automated Clinical Outreach:** Twilio Voice and SMS integration to proactively contact patients based on real-time risk escalation.

## 📁 Project Structure

- **`ED-frontend/`**: The Next.js 14+ frontend application. Uses Tailwind CSS, Lucide icons, and a custom component library for a premium medical UI.
- **`backend/`**: The FastAPI Python backend. Manages the SQLite/PostgreSQL database, ML model inference, Twilio outreach, and LLM integrations.
- **`ML_V2/`** & **`ML_V3/`**: Machine learning artifacts, training scripts, pipelines, and evaluation reports. `ML_V2` contains the production-ready Weighted Ensemble model.
- **`Datasets/`**: Data engineering pipelines and the synthesized master dataset mapping CMS synthetic data for ML training.
- **`Documentation/`**: Historical logs, challenges, and retrospective notes regarding the hackathon development lifecycle.

## 🛠️ Technology Stack

- **Frontend**: Next.js, React, Tailwind CSS, TypeScript
- **Backend**: Python, FastAPI, SQLite / PostgreSQL, Uvicorn
- **AI & Machine Learning**: Scikit-Learn, XGBoost, Pandas, Joblib, SHAP
- **LLM Integration**: Groq API (OpenAI drop-in compatibility)
- **External Services**: Twilio (Programmable Voice/SMS)

## ⚙️ Getting Started

### Prerequisites

- Node.js (v18+)
- Python (3.10+)
- A Groq API key and Twilio credentials (optional for full functionality)

### 1. Starting the Backend

Navigate to the backend directory, install dependencies, and start the FastAPI server:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
*(The backend runs on `http://localhost:8001` by default).*

### 2. Starting the Frontend

Open a new terminal window, navigate to the frontend directory, install packages, and start the development server:

```bash
cd ED-frontend
npm install
npm run dev
```
*(The frontend runs on `http://localhost:3000`).*

## 🔒 Security & Privacy

CarePath Navigator is built with strict privacy guardrails:
- The AI navigation assistant is hardcoded to block any Personal Health Information (PHI) discussions.
- Phone numbers and clinical identifiers are masked on public-facing dashboard views.

## 👥 Author & Contributors

- **[Hamsavardhani D V](https://github.com/Hamsa0408)** ([@Hamsa0408](https://github.com/Hamsa0408))
- **[Akshay G](https://github.com/AkshayG-30)** ([@AkshayG-30](https://github.com/AkshayG-30))
- **[Bharath B](https://github.com/BharathB777)** ([@BharathB777](https://github.com/BharathB777))
- **[Dharaneeswaran](https://github.com/Dharaneeswaran)**
- **[Jayaselan](https://github.com/Jayaselan08)** ([@Jayaselan08](https://github.com/Jayaselan08))
- **[Mithilesh](https://github.com/MithiMaster)** ([@MithiMaster](https://github.com/MithiMaster))
- **[Pavan Kumar](https://github.com/Pavankumar)**
- **[Soniya](https://github.com/Soniya-2025)** ([@Soniya-2025](https://github.com/Soniya-2025))

## 🏆 Hackathon Context

This repository represents the culmination of extensive data engineering, ML optimization, and full-stack application development targeted at Use Case 7: Avoidable Emergency Department Utilization for the **Cognizant × SMVEC Hackathon**.


