from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    title = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # note, transcript, prescription
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    patient = relationship('Patient', back_populates='documents')
    entities = relationship('ClinicalEntity', back_populates='document')
