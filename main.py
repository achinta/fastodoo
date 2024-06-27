from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, APIRouter, Security, Request, status
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.middleware.authentication import AuthenticationMiddleware

from pydantic import BaseModel, Field

from fastodoo.crud import read_objects, read_object
from fastodoo.database import engine, get_db
from fastodoo.models import create_fast_models, OdooIRModel
from fastodoo.middleware import JWTAuthBackend
from sqlalchemy.orm import Session
from functools import partial

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create the fastapi app
app = FastAPI()
# app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend())

odoo_models = read_objects(OdooIRModel, limit=-1)

def configure_routes_for_models(app, odoo_models):
    '''configure routes for odoo models. Returns number of models configured'''
    configured_model_count = 0
    for odoo_model in odoo_models:
        sqlalchemy_model, api_model = create_fast_models(odoo_model.model)

        # ignore if we could not create an sqlalchemy model
        if not sqlalchemy_model:
            continue

        # replace if we want to different route for an odoo model
        # route_name = model_conf['route'] if model_conf.get('route') else odoo_model.replace('.','-') + 's'
        route_name = odoo_model.model.replace('.','-') + 's'
        # auth_needed = model_conf.get('auth_needed')
        # scope = model_conf.get('scope', odoo_model.replace(',',''))

        # return object list
        # we use partial to pass the db_model as a paramter to read_objects
        read_objects_for_model = partial(read_objects, sqlalchemy_model)
        # we use partial to pass the sqlalchemy_model as a paramter endpoint (which is a callable)
        app.router.add_api_route(f'/models/{route_name}', read_objects_for_model, methods=['get'],
                            response_model=List[api_model], name=odoo_model.name)
        configured_model_count += 1

        # return object detail
        read_object_for_model = partial(read_object, sqlalchemy_model)
        # we use partial to pass the sqlalchemy_model as a paramter endpoint (which is a callable)
        app.add_api_route(path="/models/{0}/".format(route_name) + '{object_id}', endpoint=read_object_for_model, methods=['get'],
                                response_model=api_model, name=odoo_model.name)

    logger.info(f'Configured {configured_model_count} models for rest api')
    return configured_model_count
    

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)

# @app.get('/aims-model-fields/{model_name}', response_model=List[schemas.OdooModelField])
# def read_aims_model_fields(model_name: str, skip: int = 0, limit: int = 100, db: Session=Depends(get_db)):
#     result = crud.read_aims_model_fields(model_name)
#     return result

# configure the routes
configure_routes_for_models(app, odoo_models)

