import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api.health import router as health_router
from .api.analysis import router as analysis_router
from .api.dataset import router as dataset_router
from .api.upload import router as upload_router

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title='ClinGap-NLP API')

# CORS (allow all for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health_router)
app.include_router(analysis_router)
app.include_router(dataset_router)
app.include_router(upload_router)

# Logging configuration
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=log_level)
