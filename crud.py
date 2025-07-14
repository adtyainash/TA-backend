# crud.py

from sqlalchemy.orm import Session
from models import DailyCase, DailyCaseInput
from sqlalchemy import text, func
from datetime import date, timedelta
from typing import Optional

def generate_yearweek(input_date: date) -> str:
    """Generate yearweek in YYYYWW format"""
    year = input_date.year
    week = input_date.isocalendar()[1]
    return f"{year}{week:02d}"

def get_monday_of_week(input_date: date) -> date:
    """Get the Monday of the week for a given date"""
    days_since_monday = input_date.weekday()
    monday = input_date - timedelta(days=days_since_monday)
    return monday

def insert_daily_case(db: Session, case_input: DailyCaseInput):
    # Generate primary key: code.date
    daily_case_pk = f"{case_input.code}.{case_input.date.day}/{case_input.date.month}/{case_input.date.year}"
    
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

def aggregate_daily_to_weekly(db: Session, target_yearweek: Optional[str] = None):
    """
    Aggregate daily cases into weekly cases for a specific yearweek or all unprocessed weeks
    
    Args:
        db: Database session
        target_yearweek: Specific yearweek to process (format: YYYYWW). If None, processes all unprocessed weeks
    """
    
    if target_yearweek:
        # Process specific yearweek
        sql = text("""
            INSERT INTO public.weekly_case (weekly_case_pk, yearweek, cases, mondayofweek, "ICD10_code")
            SELECT 
                CONCAT(dc."ICD10_code", '.', :yearweek) as weekly_case_pk,
                dc.yearweek,
                SUM(dc.cases) as cases,
                MIN(DATE_TRUNC('week', dc.date)::date) as mondayofweek,
                dc."ICD10_code"
            FROM public.daily_case dc
            WHERE dc.yearweek = :yearweek
            GROUP BY dc.yearweek, dc."ICD10_code"
            ON CONFLICT (weekly_case_pk) DO UPDATE SET
                cases = EXCLUDED.cases,
                mondayofweek = EXCLUDED.mondayofweek
        """)
        db.execute(sql, {"yearweek": target_yearweek})
    else:
        # Process all yearweeks that don't have weekly aggregation yet
        sql = text("""
            INSERT INTO public.weekly_case (weekly_case_pk, yearweek, cases, mondayofweek, "ICD10_code")
            SELECT 
                CONCAT(dc."ICD10_code", '.', dc.yearweek) as weekly_case_pk,
                dc.yearweek,
                SUM(dc.cases) as cases,
                MIN(DATE_TRUNC('week', dc.date)::date) as mondayofweek,
                dc."ICD10_code"
            FROM public.daily_case dc
            WHERE NOT EXISTS (
                SELECT 1 FROM public.weekly_case wc 
                WHERE wc.yearweek = dc.yearweek AND wc."ICD10_code" = dc."ICD10_code"
            )
            GROUP BY dc.yearweek, dc."ICD10_code"
            ON CONFLICT (weekly_case_pk) DO UPDATE SET
                cases = EXCLUDED.cases,
                mondayofweek = EXCLUDED.mondayofweek
        """)
        db.execute(sql)
    
    db.commit()

def get_latest_yearweek(db: Session) -> Optional[str]:
    """Get the latest yearweek from daily_case table"""
    sql = text("""
        SELECT MAX(yearweek) as latest_yearweek
        FROM public.daily_case
    """)
    result = db.execute(sql).fetchone()
    return result[0] if result and result[0] else None

def get_weekly_stats(db: Session, yearweek: Optional[str] = None):
    """Get weekly case statistics"""
    if yearweek:
        sql = text("""
            SELECT wc.yearweek, wc."ICD10_code", wc.cases, wc.mondayofweek, p.nama_penyakit
            FROM public.weekly_case wc
            LEFT JOIN public.penyakit p ON wc."ICD10_code" = p.ICD10
            WHERE wc.yearweek = :yearweek
            ORDER BY wc.cases DESC
        """)
        return db.execute(sql, {"yearweek": yearweek}).fetchall()
    else:
        sql = text("""
            SELECT wc.yearweek, wc."ICD10_code", wc.cases, wc.mondayofweek, p.nama_penyakit
            FROM public.weekly_case wc
            LEFT JOIN public.penyakit p ON wc."ICD10_code" = p.ICD10
            ORDER BY wc.yearweek DESC, wc.cases DESC
        """)
        return db.execute(sql).fetchall()