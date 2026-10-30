from ..database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # relationships
    documents = relationship('Document', back_populates='patient')

