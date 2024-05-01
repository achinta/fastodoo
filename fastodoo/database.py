from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session, sessionmaker


import logging
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = "postgresql://odoo:odoo@127.0.0.1/aims"
# postgis://mysrcm:password@localhost/aims

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

