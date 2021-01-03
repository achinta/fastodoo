from sqlalchemy.orm import Session
from fastapi import Depends
from .database import get_db 

from . import models, schemas
from loguru import logger
import logging
logging.basicConfig(level=logging.INFO)

def read_aims_model_fields(model_name: str):
    db = next(get_db())
    return db.query(models.OdooModelField).filter(models.OdooModelField.model == model_name).all()