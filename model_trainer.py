#!/usr/bin/env python3
"""
Model Training and Prediction System

This script handles:
1. Training SARIMAX models for each ICD10 code
2. Making predictions for the next 4 weeks
3. Saving predictions to the database
4. Model versioning and management
"""

import pickle
import pandas as pd
import numpy as np
from datetime import date, timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults
from sklearn.metrics import mean_absolute_error
import logging
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import SessionLocal
from crud import generate_yearweek, get_monday_of_week
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_trainer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
    def get_weekly_data(self, db: Session, icd10_code: str) -> pd.DataFrame:
        """Get weekly case data for a specific ICD10 code"""
        sql = text("""
            SELECT yearweek, cases, mondayofweek
            FROM weekly_case 
            WHERE "ICD10_code" = :icd10_code
            ORDER BY yearweek ASC
        """)
        
        result = db.execute(sql, {"icd10_code": icd10_code}).fetchall()
        
        if not result:
            logger.warning(f"No data found for ICD10 code: {icd10_code}")
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        df['mondayofweek'] = pd.to_datetime(df['mondayofweek'])
        df = df.set_index('mondayofweek')
        
        return df
    
    def train_and_save_sarimax_model(self, df: pd.DataFrame, icd10_code: str) -> Tuple[object, str, str]:
        """Train SARIMAX model for given data and save it to file"""
        try:
            # Prepare data
            ts_data = df['cases'].astype(float)
            
            # Determine seasonal period (52 weeks for yearly seasonality)
            seasonal_period = 115  # Changed from 115 to 52 for weekly data
            
            # Train SARIMAX model
            model = SARIMAX(
                ts_data,
                order=(2, 0, 0),
                seasonal_order=(0, 1, 1, seasonal_period),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            sarima_result = model.fit(disp=False)
            
            # Generate model version
            model_version = f"{icd10_code}_{date.today().strftime('%Y%m%d')}_{len(ts_data)}"
            
            # Save model
            model_path = os.path.join(self.model_dir, f"{icd10_code}_{model_version}.pkl")
            with open(model_path, 'wb') as pkl:
                pickle.dump(sarima_result, pkl)
            logger.info(f"Model trained and saved successfully for {icd10_code}. Version: {model_version}, Path: {model_path}")
            return sarima_result, model_version, model_path
            
        except Exception as e:
            logger.error(f"Error training and saving model for {icd10_code}: {str(e)}")
            raise
    
    def load_model(self, icd10_code: str, model_version: str) -> SARIMAXResults:
        """Load trained model from file"""
        model_path = os.path.join(self.model_dir, f"{icd10_code}_{model_version}.pkl")
        
        try:
            with open(model_path, 'rb') as pkl:
                model = pickle.load(pkl)
            logger.info(f"Model loaded from: {model_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def make_predictions(self, model: SARIMAXResults, steps: int = 4) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions for the next N steps"""
        try:
            # Get forecast
            forecast = model.get_forecast(steps=steps)
            predicted_values = forecast.predicted_mean
            confidence_intervals = forecast.conf_int()
            
            return predicted_values, confidence_intervals
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise
    
    def calculate_next_yearweek(self, current_yearweek: str) -> str:
        """Calculate the next yearweek"""
        year = int(current_yearweek[:4])
        week = int(current_yearweek[4:])
        
        week += 1
        if week > 52:
            week = 1
            year += 1
        
        return f"{year}{week:02d}"
    
    def save_predictions_to_db(self, db: Session, icd10_code: str, model_version: str, 
                             predictions: np.ndarray, confidence_intervals: pd.DataFrame):
        """Save predictions to database"""
        try:
            # Get the last week from the data to calculate future weeks
            last_week_sql = text("""
                SELECT MAX(yearweek) as last_week
                FROM weekly_case 
                WHERE "ICD10_code" = :icd10_code
            """)
            last_week_result = db.execute(last_week_sql, {"icd10_code": icd10_code}).fetchone()
            
            if not last_week_result or not last_week_result[0]:
                logger.error(f"No data found for {icd10_code}")
                return
            
            last_week = last_week_result[0]
            current_yearweek = last_week
            
            # Insert predictions
            for i, (pred, conf_lower, conf_upper) in enumerate(zip(predictions, 
                                                                  confidence_intervals.iloc[:, 0], 
                                                                  confidence_intervals.iloc[:, 1])):
                # Calculate next week
                current_yearweek = self.calculate_next_yearweek(current_yearweek)
                prediction_pk = f"{icd10_code}/{current_yearweek}/{model_version}"
                
                # Calculate Monday of the week
                monday_date = date.today() + timedelta(weeks=i+1)
                monday_date = monday_date - timedelta(days=monday_date.weekday())
                
                sql = text("""
                    INSERT INTO predictions (prediction_pk, "ICD10_code", yearweek, 
                                           predicted_cases, confidence_lower, confidence_upper, 
                                           model_version, created_at, is_actual)
                    VALUES (:pk, :code, :yearweek, :pred, :conf_lower, :conf_upper, 
                           :version, :created_at, 0)
                    ON CONFLICT (prediction_pk) DO UPDATE SET
                        predicted_cases = EXCLUDED.predicted_cases,
                        confidence_lower = EXCLUDED.confidence_lower,
                        confidence_upper = EXCLUDED.confidence_upper,
                        model_version = EXCLUDED.model_version,
                        created_at = EXCLUDED.created_at
                """)
                
                db.execute(sql, {
                    "pk": prediction_pk,
                    "code": icd10_code,
                    "yearweek": current_yearweek,
                    "pred": float(pred),
                    "conf_lower": float(conf_lower),
                    "conf_upper": float(conf_upper),
                    "version": model_version,
                    "created_at": date.today()
                })
            
            db.commit()
            logger.info(f"Predictions saved to database for {icd10_code}")
            
        except Exception as e:
            logger.error(f"Error saving predictions to database: {str(e)}")
            db.rollback()
            raise
    
    def get_unique_icd10_codes(self, db: Session) -> List[str]:
        """Get all unique ICD10 codes from weekly_case table"""
        sql = text("""
            SELECT DISTINCT "ICD10_code"
            FROM weekly_case
            ORDER BY "ICD10_code"
        """)
        
        result = db.execute(sql).fetchall()
        return [row[0] for row in result]
    
    def train_and_predict_all(self, forecast_steps: int = 4):
        """Train models and make predictions for all ICD10 codes"""
        db = SessionLocal()
        
        try:
            icd10_codes = self.get_unique_icd10_codes(db)
            logger.info(f"Found {len(icd10_codes)} ICD10 codes to process")
            
            for icd10_code in icd10_codes:
                logger.info(f"Processing {icd10_code}...")
                
                try:
                    # Get data
                    df = self.get_weekly_data(db, icd10_code)
                    if df.empty:
                        logger.warning(f"Skipping {icd10_code} - no data")
                        continue
                    
                    # Train and save model
                    model, model_version, _ = self.train_and_save_sarimax_model(df, icd10_code)
                    
                    # Make predictions
                    predictions, confidence_intervals = self.make_predictions(model, forecast_steps)  # type: ignore[arg-type]
                    confidence_intervals = pd.DataFrame(confidence_intervals)
                    
                    # Save predictions to database
                    self.save_predictions_to_db(db, icd10_code, model_version, 
                                             predictions, confidence_intervals)
                    
                    logger.info(f"Completed processing {icd10_code}")
                    
                except Exception as e:
                    logger.error(f"Error processing {icd10_code}: {str(e)}")
                    # Continue with next ICD10 code instead of failing completely
                    continue
            
            logger.info("All models trained and predictions saved successfully!")
            
        except Exception as e:
            logger.error(f"Error in train_and_predict_all: {str(e)}")
            raise
        finally:
            db.close()
    
    def get_predictions(self, db: Session, icd10_code: Optional[str] = None, 
                       model_version: Optional[str] = None) -> List[Dict]:
        """Get predictions from database"""
        try:
            if icd10_code and model_version:
                sql = text("""
                    SELECT * FROM predictions 
                    WHERE "ICD10_code" = :code AND model_version = :version
                    ORDER BY yearweek ASC
                """)
                result = db.execute(sql, {"code": icd10_code, "version": model_version})
            elif icd10_code:
                sql = text("""
                    SELECT * FROM predictions 
                    WHERE "ICD10_code" = :code
                    ORDER BY yearweek ASC
                """)
                result = db.execute(sql, {"code": icd10_code})
            else:
                sql = text("""
                    SELECT * FROM predictions 
                    ORDER BY "ICD10_code", yearweek ASC
                """)
                result = db.execute(sql)
            
            predictions = []
            for row in result:
                predictions.append({
                    "prediction_pk": row[0],
                    "ICD10_code": row[1],
                    "yearweek": row[2],
                    "predicted_cases": row[3],
                    "confidence_lower": row[4],
                    "confidence_upper": row[5],
                    "model_version": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "is_actual": row[8]
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting predictions: {str(e)}")
            raise

def main():
    """Main function for manual execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Model Training and Prediction')
    parser.add_argument('--train', action='store_true', help='Train models and make predictions')
    parser.add_argument('--steps', type=int, default=4, help='Number of forecast steps')
    parser.add_argument('--model-dir', type=str, default='models', help='Directory to save models')
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(args.model_dir)
    
    if args.train:
        trainer.train_and_predict_all(args.steps)
    else:
        print("Use --train to train models and make predictions")

if __name__ == "__main__":
    main()