from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base


class Student(Base):
    __tablename__ = "students"

    id         = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    name       = Column(String)
    section    = Column(String, nullable=True)


class StudentRecord(Base):
    __tablename__ = "records"

    id                     = Column(Integer, primary_key=True, index=True)
    student_id             = Column(String, ForeignKey("students.student_id"), index=True)
    age                    = Column(Float)
    gender                 = Column(String)
    study_hours_per_day    = Column(Float)
    sleep_hours            = Column(Float)
    attendance             = Column(Float)
    assignments_completed  = Column(Float)
    internal_score         = Column(Float)
    stress_level           = Column(Float)
    social_media_hours     = Column(Float)
    created_at             = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id             = Column(Integer, primary_key=True, index=True)
    student_id     = Column(String, ForeignKey("students.student_id"), index=True)
    predicted_sgpa = Column(Float)
    model_version  = Column(String, default="v1")
    created_at     = Column(DateTime, default=datetime.utcnow)


class ActualResult(Base):
    __tablename__ = "actual_results"

    id          = Column(Integer, primary_key=True, index=True)
    student_id  = Column(String, ForeignKey("students.student_id"), unique=True, index=True)
    actual_sgpa = Column(Float)
    result_date = Column(DateTime, default=datetime.utcnow)
