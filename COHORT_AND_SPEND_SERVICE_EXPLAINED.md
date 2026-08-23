# 📚 Plain English Guide: Cohort & Avoidable Spend Service

> **What is this file?**  
> This guide breaks down the **`CohortService`** in simple words so you can easily understand it, explain it in your project presentation, and answer questions from CTS judges.

---

## 1. What Problem Does It Solve? (The Big Picture)

In healthcare, **Emergency Department (ED) visits and hospital admissions are extremely expensive**:
- An average Emergency Department visit costs **~$1,850**.
- An average Inpatient hospital admission costs **~$14,200**.
- An outpatient preventive checkup or care manager call costs only **~$120**.

### The Core Idea:
Many chronic patients (e.g., people with Heart Failure, Diabetes, COPD) go to the Emergency Room **simply because they didn't get timely care, forgot medication, or missed a doctor checkup** (known in US healthcare as **Ambulatory Care Sensitive Conditions** or **Preventable ED Visits**).

👉 **`CohortService` calculates:**
1. **How sick/complex is the patient?** (Comorbidity Index)
2. **How much emergency hospital money could we save** if we proactively help this patient before they get worse? (Avoidable Spend)
3. **What is the Return on Investment (ROI)?** For every $1 spent on nurse outreach, how many dollars of hospital bills are saved?

---

## 2. The 3 Main Functions in `CohortService`

The file is located at [`backend/services/cohort_service.py`](file:///d:/CTS-%20Main/backend/services/cohort_service.py). It has 3 key functions:

```
┌─────────────────────────────────────────────────────────────┐
│                       CohortService                         │
├──────────────────────────────┬──────────────────────────────┤
│ 1. calculate_comorbidity_    │ 2. estimate_avoidable_       │ 3. stratify_population(...)   │
│    index(...)                │    spend(...)                │                               │
│  Counts & weights diseases   │  Calculates dollar savings   │  Groups 7,754 patients into   │
│  (CHF, COPD, Diabetes, etc.) │  and ROI ($ saved vs $ spent)│  High / Medium / Low tiers    │
└──────────────────────────────┴──────────────────────────────┴───────────────────────────────┘
```

---

### Function 1: `calculate_comorbidity_index(conditions)`
- **What it does:** Reads the patient's conditions (e.g., `"CHF, Diabetes, COPD"`).
- **How it works:** Assigns clinical weights (based on CMS HCC standards):
  - **Congestive Heart Failure (CHF):** Weight = `1.8` (Very high risk)
  - **Chronic Kidney Disease (CKD):** Weight = `1.6`
  - **COPD (Lung disease):** Weight = `1.5`
  - **Diabetes:** Weight = `1.2`
  - **Hypertension (High Blood Pressure):** Weight = `1.0`
- **Output:** Returns a **Weighted Score** and assigns a tier: `High`, `Moderate`, or `Low`.

---

### Function 2: `estimate_avoidable_spend(risk_score, ed_visits, inpatient_admissions)`
- **What it does:** Calculates exact **dollar savings** for health insurance payers and hospitals.
- **How it works:**
  - If a patient is **High Risk (> 0.8)**, **65%** of their future emergency encounters can be prevented with proactive outreach.
  - If a patient is **Medium Risk (0.6 - 0.8)**, **45%** can be prevented.
  - If a patient is **Low Risk (< 0.6)**, **25%** can be prevented.
- **Example Calculation:**
  - Patient has **3 ED visits** ($1,850 each = $5,550 total).
  - Preventability = 65%.
  - **Avoidable Spend** = $5,550 × 0.65 = **$3,607.50 saved**.
  - Cost of nurse SMS/call = **$120**.
  - **Net Savings** = $3,607.50 - $120 = **$3,487.50**.
  - **ROI Ratio** = $3,607.50 / $120 = **~30x Return on Investment**.

---

### Function 3: `stratify_population(patients)`
- **What it does:** Takes all 7,754 patients and aggregates them into high-level dashboard summaries:
  - **High Risk Cohort** (Percentage & Count)
  - **Medium Risk Cohort**
  - **Low Risk Cohort**
  - **Care Continuity Breakdown** (Stable, Moderate, Fragmented doctors)

---

## 3. How to Explain This to Judges (Your Presentation Script)

If a judge or interviewer asks: **"What did you build on the backend for cohort analytics and avoidable spend?"**

You can answer with this 30-second explanation:

> *"As the backend developer, I built the **Cohort & Avoidable Spend Service** in Python:*
>
> 1. *It parses chronic disease profiles and computes a clinical **Comorbidity Index** based on CMS HCC disease weights.*
> 2. *It applies an actuarial cost model that determines what percentage of Emergency Department visits are **clinically preventable**.*
> 3. *It calculates the **projected 30-day avoidable spend** and **ROI ratio**, giving insurance payers and hospitals exact financial justification to dispatch care managers to high-risk patients before an emergency occurs."*

---

## 4. How to Run the Tests to Prove It Works

You can run the dedicated test suite anytime from terminal:

```powershell
.\venv\Scripts\python tests/test_cohort_service.py
```
**Output:**
```
[OK] All CohortService unit tests passed successfully!
```
