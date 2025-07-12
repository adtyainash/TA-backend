# crud.py

from sqlalchemy.orm import Session
from models import DailyCase, DailyCaseInput
from sqlalchemy import text
from datetime import date

def generate_yearweek(input_date: date) -> str:
    """Generate yearweek in YYYYWW format"""
    year = input_date.year
    week = input_date.isocalendar()[1]
    return f"{year}{week:02d}"

def insert_daily_case(db: Session, case_input: DailyCaseInput):
    # Generate primary key: code.date
    daily_case_pk = f"{case_input.code}/{case_input.date.day}/{case_input.date.year}"
    
    # Generate yearweek
    yearweek = generate_yearweek(case_input.date)
    
    sql = text("""
        INSERT INTO public.daily_case (daily_case_pk, date, cases, yearweek, "ICD10_code")
        VALUES (:pk, :date, :cases, :yearweek, :code)
        ON CONFLICT (daily_case_pk) DO NOTHING
    """)
    db.execute(sql, {
        "pk": daily_case_pk,
        "date": case_input.date,
        "cases": case_input.cases,
        "yearweek": yearweek,
        "code": case_input.code
    })
    db.commit()
