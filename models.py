# models.py

from pydantic import BaseModel
from datetime import date
from typing import Optional
from sqlalchemy import Column, String, Date, BigInteger, Text, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
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

class DiagnoseInput(BaseModel):
    nik: str
    ICD10_code: str
    Kode_kecamatan: str

class Diagnose(BaseModel):
    nik_pasien: str
    id_puskesmas: str
    id_penyakit: str
    
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
    Kode_Kecamatan = Column(Text)
    Kecamatan = Column(Text)
    Periode = Column(Text)
    Jenis_Kelamin = Column(Text)
    Rentang_Umur = Column(Text)
    Jumlah_Kasus = Column(BigInteger)
    Rentang_Umur_Rank = Column(BigInteger)
    YearMonth = Column(Date)

class PenyakitDB(Base):
    __tablename__ = "penyakit"
    
    ICD10 = Column(Text, primary_key=True)
    nama_penyakit = Column(Text, nullable=False)
    deskripsi = Column(Text)
    keterangan = Column(Text)

    # Relationships
    diagnosis = relationship("DiagnosisDB", back_populates="penyakit")

class PasienDB(Base):
    __tablename__ = "pasien"
    
    nik = Column(Text, primary_key=True, unique=True)
    nama = Column(Text, nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    jenis_kelamin = Column(Text, nullable=False)
    no_kk = Column(Text, nullable=False)
    alamat = Column(Text, nullable=False)
    kode_pos = Column(Text, nullable=False)
    kode_kecamatan = Column(Text, nullable=False)
    telepon = Column(Text, nullable=False)
    status_pernikahan = Column(Text, nullable=False)
    status_kerwarganegaraan = Column(Text, nullable=False)

    # Relationships
    diagnosis = relationship("DiagnosisDB", back_populates="pasien")

class DiagnosisDB(Base):
    __tablename__ = "diagnosis"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nik_pasien = Column(Text, ForeignKey("pasien.nik"), nullable=False)
    id_puskesmas = Column(Text, nullable=False)
    id_penyakit = Column(Text, ForeignKey("penyakit.ICD10"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)

    # Relationships
    pasien = relationship("PasienDB", back_populates="diagnosis")
    penyakit = relationship("PenyakitDB", back_populates="diagnosis")

class NotificationDB(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    ICD10_code = Column(Text, ForeignKey("penyakit.ICD10"))
    message = Column(Text, nullable=False)

    # Relationship to penyakit table
    penyakit = relationship("PenyakitDB", back_populates="notifications")
