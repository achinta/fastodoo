from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import RequestValidationError

from . import crud, models, schemas
from .database import SessionLocal, engine
from sqlalchemy.orm import Session
import uvicorn
import logging

app = FastAPI()

from loguru import logger
logging.basicConfig(level=logging.INFO)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)


@app.get('/aims-model-fields/{model_name}', response_model=List[schemas.OdooModelField])
def read_aims_model_fields(model_name: str, skip: int = 0, limit: int = 100, db: Session=Depends(get_db)):
    result = crud.read_aims_model_fields(db, model_name)
    return result

# if __name__ == '__main__':
    # uvicorn.run(app, host='0.0.0.0', port=8000)
