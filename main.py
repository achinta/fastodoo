from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, APIRouter
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from pydantic import BaseModel, Field

from . import crud, models, schemas
from .database import engine, get_db
from .dynamic import create_fast_models
from sqlalchemy.orm import Session
from functools import partial
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

odoo_models = ['srcm.group','res.country']


for odoo_model in odoo_models:
    db_model, api_model = create_fast_models(odoo_model)

    def read_objects():
        db = next(get_db())
        objs = db.query(db_model).all()[0:10]
        return objs

    route_name = odoo_model.replace('.','_')
    app.router.add_api_route(f'/odoo/{route_name}', read_objects, methods=['get'],
                         response_model=List[api_model])

# country_db, country_pyd = create_fast_models('res.country')
# @app.get('/countries', response_model=List[country_pyd])
# def read_countries(skip: int = 0, limit: int = 0):
#     db = next(get_db())
#     countries = db.query(country_db).all()[skip: skip + limit]
#     return countries

# group_db, group_pyd = create_fast_models('srcm.group')
# @app.get('/groups', response_model=List[group_pyd])
# def read_groups(skip: int = 0, limit: int = 0):
#     db = next(get_db())
#     groups = db.query(group_db).all()[skip: skip + limit]
#     return groups

# if __name__ == '__main__':
    # uvicorn.run(app, host='0.0.0.0', port=8000)
