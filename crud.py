# crud.py

from sqlalchemy.orm import Session
from db import SessionLocal
from models import DailyCase, DailyCaseInput, DiagnoseInput
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
    
def insert_diagnosis(db: Session, diagnose_input: DiagnoseInput):
    
    """Insert a new diagnosis record"""
    sql = text("""
        INSERT INTO public.diagnosis (nik_pasien, id_puskesmas, id_penyakit)
        VALUES (:nik, :puskesmas, :penyakit)
        ON CONFLICT (nik_pasien, id_puskesmas, id_penyakit) DO NOTHING
    """)
    db.execute(sql, {
        "nik": diagnose_input.nik,
        "puskesmas": diagnose_input.Kode_kecamatan,
        "penyakit": diagnose_input.ICD10_code
    })
    db.commit()
    
def check_predictions_and_create_notifications(db: Session, target_yearweek: Optional[str] = None) -> int:
    """
    For the (single) predicted ICD10_code in the given yearweek, compare predicted_cases
    to historical mean+2*stdev of the same week-number in prior years. Insert one
    notification if it exceeds the threshold. Returns 1 if created, else 0.
    """
    # 1) Determine target yearweek (from predictions if not provided)
    if not target_yearweek:
        latest_sql = text("SELECT MAX(yearweek) AS yw FROM public.predictions WHERE is_actual = 0")
        row = db.execute(latest_sql).mappings().first()
        target_yearweek = row["yw"] if row and row["yw"] else None
        if not target_yearweek:
            return 0

    # 2) Parse YYYY and WW
    try:
        target_year = int(target_yearweek[:4])
        weeknum = target_yearweek[-2:]
    except Exception:
        return 0

    # 3) Grab the single prediction row for this week (latest if multiple exist)
    pred_sql = text("""
        SELECT "ICD10_code", predicted_cases
        FROM public.predictions
        WHERE yearweek = :yearweek AND (is_actual IS NULL OR is_actual = 0)
        ORDER BY created_at DESC NULLS LAST, prediction_pk DESC
        LIMIT 1
    """)
    pred_row = db.execute(pred_sql, {"yearweek": target_yearweek}).mappings().first()
    if not pred_row:
        return 0

    code = pred_row["ICD10_code"]
    predicted_cases = float(pred_row["predicted_cases"])

    # 4) Historical stats for the same week number in previous years
    stats_sql = text("""
        SELECT AVG(wc.cases)::float AS mean,
               COALESCE(STDDEV_SAMP(wc.cases)::float, 0) AS stdev
        FROM public.weekly_case wc
        WHERE RIGHT(wc.yearweek, 2) = :weeknum
          AND CAST(LEFT(wc.yearweek, 4) AS INTEGER) < :target_year
          AND wc."ICD10_code" = :code
    """)
    stats = db.execute(stats_sql, {
        "weeknum": weeknum,
        "target_year": target_year,
        "code": code
    }).mappings().first()

    mean = stats["mean"] if stats and stats["mean"] is not None else None
    stdev = stats["stdev"] if stats and stats["stdev"] is not None else 0.0

    # No historical baseline → nothing to compare
    if mean is None:
        return 0

    threshold = mean + 2.0 * stdev
    if predicted_cases > threshold:
        message = (
            f"Predicted anomaly for week {target_yearweek}: ICD10 {code} "
            f"predicted_cases={predicted_cases:.2f} > threshold(mean+2*stdev)={threshold:.2f}. "
            f"Next week cases predicted to be an anomaly, please beware."
        )
        insert_sql = text("""
            INSERT INTO public.notifications (created_at, "ICD10_code", message)
            VALUES (CURRENT_TIMESTAMP, :code, :message)
        """)
        db.execute(insert_sql, {"code": code, "message": message})
        db.commit()
        return 1

    return 0

if __name__ == "__main__":
    db = SessionLocal()
    result = check_predictions_and_create_notifications(db, target_yearweek="202524")
    print(f"Notifications created: {result}")
    db.close()