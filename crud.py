from sqlalchemy.orm import Session

from . import models, schemas
import logging

logger = logging.getLogger(__name__)


def read_aims_model_fields(db: Session, model_name: str):
    return db.query(models.OdooModelField).filter(models.OdooModelField.model == model_name).all()