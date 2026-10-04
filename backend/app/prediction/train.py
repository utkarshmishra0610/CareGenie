"""ML training pipeline for disease classification and risk prediction."""
import csv
import os
import random
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "disease_risk_model.joblib")
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "disease_symptoms.csv")


def load_dataset():
    """Loads feature names, disease names, and binary matrix."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        symptoms = [s.strip().lower() for s in header[1:]]

        diseases = []
        matrix = []

        for row in reader:
            if not row or not row[0].strip():
                continue
            diseases.append(row[0].strip())
            vector = [1 if val.strip() == "1" else 0 for val in row[1:]]
            matrix.append(vector)

    return symptoms, diseases, np.array(matrix, dtype=np.float32)


def generate_augmented_training_data(symptoms, diseases, base_matrix, augmentation_factor=5):
    """Generates realistic partial patient symptom vectors to improve multi-symptom generalization."""
    X_train = []
    y_train = []

    # 1. Add ground-truth full profiles
    for idx, disease in enumerate(diseases):
        X_train.append(base_matrix[idx])
        y_train.append(disease)

        active_indices = np.where(base_matrix[idx] == 1)[0]
        if len(active_indices) == 0:
            continue

        # 2. Add realistic partial symptom combinations (subsets of 2-5 symptoms)
        for _ in range(augmentation_factor):
            subset_size = random.randint(1, min(len(active_indices), 6))
            chosen_indices = random.sample(list(active_indices), subset_size)
            sample_vec = np.zeros(len(symptoms), dtype=np.float32)
            sample_vec[chosen_indices] = 1.0

            # Occasionally add 1 non-specific distractor symptom (15% probability)
            if random.random() < 0.15:
                random_distractor = random.randint(0, len(symptoms) - 1)
                sample_vec[random_distractor] = 1.0

            X_train.append(sample_vec)
            y_train.append(disease)

    return np.array(X_train, dtype=np.float32), np.array(y_train)


def train_and_export_model():
    """Trains the clinical disease predictor model and exports joblib artifact."""
    print("Loading clinical disease dataset...")
    symptoms, diseases, base_matrix = load_dataset()
    print(f"Loaded {len(diseases)} diseases with {len(symptoms)} symptom features.")

    print("Generating augmented training vectors...")
    random.seed(42)
    np.random.seed(42)
    X_train, y_train = generate_augmented_training_data(symptoms, diseases, base_matrix, augmentation_factor=8)
    print(f"Total training samples: {X_train.shape[0]}")

    print("Fitting Random Forest classifier...")
    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=30,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1,
    )
    classifier.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    payload = {
        "model": classifier,
        "symptoms": symptoms,
        "diseases": list(classifier.classes_),
        "version": "1.0.0",
    }

    joblib.dump(payload, MODEL_PATH, compress=3)
    print(f"Trained model artifact successfully saved to: {MODEL_PATH}")
    return payload


if __name__ == "__main__":
    train_and_export_model()
