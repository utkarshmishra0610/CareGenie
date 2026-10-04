"""Dataset initialization script for disease symptoms classification."""
import os
import shutil

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(DATA_DIR, "disease_symptoms.csv")
ML_SERVICE_DIR = os.path.abspath(
    os.path.join(DATA_DIR, "..", "..", "..", "ml-service", "data")
)
ML_CSV_PATH = os.path.join(ML_SERVICE_DIR, "disease_symptoms.csv")


def sync_to_ml_service():
    """Ensure ml-service has an identical copy of the dataset."""
    os.makedirs(ML_SERVICE_DIR, exist_ok=True)
    if os.path.exists(CSV_PATH):
        shutil.copy(CSV_PATH, ML_CSV_PATH)
        print(f"Synced dataset to {ML_CSV_PATH}")


if __name__ == "__main__":
    sync_to_ml_service()
