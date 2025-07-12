# models.py

from pydantic import BaseModel
from datetime import date
from typing import Optional

class DailyCaseInput(BaseModel):
    date: date
    cases: int
    code: str

class DailyCase(BaseModel):
    daily_case_pk: str
    date: date
    cases: int
    yearweek: str
    ICD10_code: str
