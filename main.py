# main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, timedelta
from sqlalchemy.orm import Session
from db import SessionLocal
from models import DailyCaseInput, PredictionInput, DiagnoseInput
from crud import insert_daily_case, aggregate_daily_to_weekly, get_weekly_stats, get_latest_yearweek, insert_diagnosis
from model_trainer import ModelTrainer
from typing import List, Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://disease-surveillance-dashboard.online", "https://www.disease-surveillance-dashboard.online"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/submit_case/")
def submit_case(case: DailyCaseInput, db: Session = Depends(get_db)):
    insert_daily_case(db, case)
    return {"message": "Case submitted successfully"}

@app.post("/submit_diagnosis")
def submit_diagnosis(diagnose: DiagnoseInput, db: Session = Depends(get_db)):
    try:
        insert_diagnosis(db, diagnose)
        return {"message": "Diagnosis submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting diagnosis: {str(e)}")

@app.post("/aggregate_weekly/")
def aggregate_weekly(target_yearweek: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Manually trigger weekly aggregation
    
    Args:
        target_yearweek: Specific yearweek to process (format: YYYYWW). If None, processes all unprocessed weeks
    """
    try:
        aggregate_daily_to_weekly(db, target_yearweek)
        if target_yearweek:
            return {"message": f"Weekly aggregation completed for week {target_yearweek}"}
        else:
            return {"message": "Weekly aggregation completed for all unprocessed weeks"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during aggregation: {str(e)}")

@app.post("/train_models/")
def train_models(forecast_steps: int = 4):
    """
    Manually trigger model training and forecasting
    
    Args:
        forecast_steps: Number of weeks to forecast (default: 4)
    """
    try:
        trainer = ModelTrainer()
        trainer.train_and_predict_all(forecast_steps=forecast_steps)
        return {"message": f"Model training completed successfully. Forecasted {forecast_steps} weeks ahead."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during model training: {str(e)}")

@app.get("/predictions/")
def get_predictions(icd10_code: Optional[str] = None, model_version: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get predictions from database
    
    Args:
        icd10_code: Specific ICD10 code to get predictions for
        model_version: Specific model version to get predictions for
    """
    try:
        trainer = ModelTrainer()
        predictions = trainer.get_predictions(db, icd10_code, model_version)
        return {
            "icd10_code": icd10_code,
            "model_version": model_version,
            "total_predictions": len(predictions),
            "predictions": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving predictions: {str(e)}")

@app.get("/weekly_stats/")
def get_weekly_statistics(yearweek: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get weekly case statistics
    
    Args:
        yearweek: Specific yearweek to get stats for. If None, returns all weeks
    """
    try:
        stats = get_weekly_stats(db, yearweek)
        return {
            "yearweek": yearweek,
            "total_records": len(stats),
            "data": [
                {
                    "yearweek": row[0],
                    "ICD10_code": row[1],
                    "cases": row[2],
                    "mondayofweek": row[3].isoformat() if row[3] else None,
                    "nama_penyakit": row[4]
                }
                for row in stats
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving weekly stats: {str(e)}")

@app.get("/latest_yearweek/")
def get_latest_week(db: Session = Depends(get_db)):
    """Get the latest yearweek from daily_case table"""
    try:
        latest_week = get_latest_yearweek(db)
        return {"latest_yearweek": latest_week}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving latest yearweek: {str(e)}")

@app.get("/")
def read_root():
    return {
        "message": "Weekly Case Aggregation and Prediction API",
        "endpoints": {
            "submit_case": "POST /submit_case/ - Submit daily case data",
            "aggregate_weekly": "POST /aggregate_weekly/ - Manually trigger weekly aggregation",
            "train_models": "POST /train_models/ - Manually trigger model training",
            "predictions": "GET /predictions/ - Get predictions",
            "weekly_stats": "GET /weekly_stats/ - Get weekly statistics",
            "latest_yearweek": "GET /latest_yearweek/ - Get latest yearweek"
        }
    }
