from model_trainer import ModelTrainer
from db import SessionLocal
import pandas as pd

# Set these to your actual values
icd10_code = "A90, A91"
model_version = "A90, A91_20250714_284"
forecast_steps = 4  # or however many steps you want

trainer = ModelTrainer("models")  # or your model directory
db = SessionLocal()

# Load the model
model = trainer.load_model(icd10_code, model_version)

# Generate predictions
predictions, confidence_intervals = trainer.make_predictions(model, forecast_steps)
confidence_intervals = pd.DataFrame(confidence_intervals)  # Ensure correct type

# Save predictions to DB
trainer.save_predictions_to_db(db, icd10_code, model_version, predictions, confidence_intervals)

db.close()
print("Predictions generated and saved to DB.")