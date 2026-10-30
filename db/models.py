from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # additional fields can be added
    documents = relationship("Document", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    gaps = relationship("Gap", back_populates="patient")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    title = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # note, transcript, prescription
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    patient = relationship("Patient", back_populates="documents")
    entities = relationship("ClinicalEntity", back_populates="document")

class ClinicalEntity(Base):
    __tablename__ = "clinical_entities"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    entity_text = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    normalized_value = Column(String)
    confidence = Column(Float, default=0.0)
    negated = Column(Boolean, default=False)
    source = Column(String)
    document = relationship("Document", back_populates="entities")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medication = Column(String, nullable=False)
    dosage = Column(String)
    frequency = Column(String)
    patient = relationship("Patient", back_populates="prescriptions")

class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    name = Column(String, nullable=False)
    documented = Column(Boolean, default=False)

class Guideline(Base):
    __tablename__ = "guidelines"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, unique=True, nullable=False)
    description = Column(Text)
    criteria = Column(Text)  # JSON string of criteria
    recommendation = Column(String)

class Gap(Base):
    __tablename__ = "gaps"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    gap_type = Column(String, nullable=False)
    description = Column(Text)
    confidence = Column(Float)
    patient = relationship("Patient", back_populates="gaps")
