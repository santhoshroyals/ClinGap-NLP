import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_db = os.path.join(_base_dir, 'clinngap.db').replace('\\', '/')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{_default_db}')
engine = create_engine(
    DATABASE_URL,
    connect_args={
        'check_same_thread': False
    } if DATABASE_URL.startswith('sqlite') else {},
    future=True,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
