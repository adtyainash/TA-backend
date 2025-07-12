# main.py

from fastapi import FastAPI, Depends
from datetime import date, timedelta
from sqlalchemy.orm import Session
from db import SessionLocal
from models import DailyCaseInput
from crud import insert_daily_case

app = FastAPI()

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
