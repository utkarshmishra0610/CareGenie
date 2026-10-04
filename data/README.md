# Disease & Symptoms Dataset

This folder contains the clinical disease and symptoms dataset utilized by the **Personalized AI Health Assistant for Disease Risk Assessment**.

---

## Dataset Overview

* **Filename**: `disease_symptoms.csv`
* **File Size**: ~268 KB
* **Rows (Diseases)**: 261 distinct medical conditions
* **Columns (Features)**: 489 symptom binary indicator variables (0 = absent, 1 = present)
* **Target Label**: `label_dis` (Disease name)

---

## Usage in Architecture

1. **AI Chatbot Service** (`backend/app/ai/`):
   Standardized taxonomy of 489 clinical symptoms used for intent matching and symptom extraction.
2. **Adaptive Questioning Engine** (`backend/app/ai/adaptive_questioning.py`):
   Identifies missing high-differential symptoms to ask smart follow-up questions.
3. **Machine Learning Risk Prediction** (`backend/app/prediction/` & `ml-service/`):
   Trains explainable classifiers (Random Forest / Logistic Regression) to assess preliminary disease risk.
4. **Healthcare Specialty Recommendation**:
   Maps conditions to appropriate specialist navigation (e.g. Cardiologist, Dermatologist, General Physician).
