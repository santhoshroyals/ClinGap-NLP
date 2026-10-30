from ..database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class ClinicalEntity(Base):
    __tablename__ = 'clinical_entities'
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    entity_text = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    normalized_value = Column(String)
    confidence = Column(Float, default=0.0)
    negated = Column(Boolean, default=False)
    source = Column(String)
    document = relationship('Document', back_populates='entities')
