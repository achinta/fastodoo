from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

from . import crud, models, schemas
from .database import engine, get_db
from .dynamic import create_fast_models
from sqlalchemy.orm import Session
import uvicorn
import logging

app = FastAPI()

from loguru import logger
logging.basicConfig(level=logging.INFO)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)

@app.get('/aims-model-fields/{model_name}', response_model=List[schemas.OdooModelField])
def read_aims_model_fields(model_name: str, skip: int = 0, limit: int = 100, db: Session=Depends(get_db)):
    result = crud.read_aims_model_fields(model_name)
    return result

country_db, country_pyd = create_fast_models('res.country')

class CountryApi2(BaseModel):
    id: Optional[int] = None
    # name: Optional[str] = None
    # column1: Optional[str] = ''
    # column2: Optional[str] = ''

# @app.get('/countries', response_model=List[country_pyd])
@app.get('/countries', response_model=CountryApi2)
def read_countries():
    db = next(get_db())
    countries = db.query(country_db).all()[:10]
    logger.info(countries)
    return countries

# if __name__ == '__main__':
    # uvicorn.run(app, host='0.0.0.0', port=8000)
