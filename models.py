# models.py

from pydantic import BaseModel
from datetime import date
from typing import Optional
from sqlalchemy import Column, String, Date, BigInteger, Text, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Pydantic models for API
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

class PredictionInput(BaseModel):
    ICD10_code: str
    forecast_steps: int = 4

# SQLAlchemy models for database tables
class DailyCaseDB(Base):
    __tablename__ = "daily_case"
    
    daily_case_pk = Column(Text, primary_key=True)
    date = Column(Date)
    cases = Column(BigInteger)
    yearweek = Column(Text)
    ICD10_code = Column(Text)

class WeeklyCaseDB(Base):
    __tablename__ = "weekly_case"
    
    weekly_case_pk = Column(Text, primary_key=True)
    yearweek = Column(Text)
    cases = Column(BigInteger)
    mondayofweek = Column(Date)
    ICD10_code = Column(Text)

class PredictionDB(Base):
    __tablename__ = "predictions"
    
    prediction_pk = Column(Text, primary_key=True)
    ICD10_code = Column(Text)
    yearweek = Column(Text)
    predicted_cases = Column(Float)
    confidence_lower = Column(Float, nullable=True)
    confidence_upper = Column(Float, nullable=True)
    model_version = Column(Text)
    created_at = Column(Date)
    is_actual = Column(BigInteger, default=0)  # 0 for prediction, 1 for actual

class MonthlyCaseCompleteDB(Base):
    __tablename__ = "monthly_case_complete"
    
    Daily_Case_PK = Column(Text, primary_key=True)
    Rentang_Umur_Rank = Column(BigInteger)
    Kode_Kecamatan = Column(Text)
    Kecamatan = Column(Text)
    Periode = Column(Text)
    Jenis_Kelamin = Column(Text)
    Rentang_Umur = Column(Text)
    Jumlah_Kasus = Column(BigInteger)

class PenyakitDB(Base):
    __tablename__ = "penyakit"
    
    ICD10 = Column(Text, primary_key=True)
    nama_penyakit = Column(Text, nullable=False)
    deskripsi = Column(Text)
