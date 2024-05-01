from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, APIRouter, Security, Request, status
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.middleware.authentication import AuthenticationMiddleware

from pydantic import BaseModel, Field

from fastodoo import crud, models, schemas
from fastodoo.database import engine, get_db
from fastodoo.dynamic import create_fast_models
from fastodoo.middleware import JWTAuthBackend
from sqlalchemy.orm import Session
from functools import partial

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# config
ODOO_MODELS = {
    'res.currency':{
        'route': 'currencies',
        'auth_needed': False
    },
    'res.country':{
        'route': 'countries',
        'auth_needed': False
    },
    # 'res.city':{
    #     'route': 'cities',
    #     'auth_needed': False
    # },
    # 'srcm.group': {
    #     'route': 'groups',
    #     'auth_needed': True
    # },
    # 'meditation.center':{
    #     'auth_needed': True,
    #     'scope': 'meditationcenters'
    # },
}

# create the fastapi app
app = FastAPI()
# app.add_middleware(AuthenticationMiddleware, backend=JWTAuthBackend())

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)

@app.get('/aims-model-fields/{model_name}', response_model=List[schemas.OdooModelField])
def read_aims_model_fields(model_name: str, skip: int = 0, limit: int = 100, db: Session=Depends(get_db)):
    result = crud.read_aims_model_fields(model_name)
    return result

def read_objects(db_model, auth_needed: bool, scope: str, request: Request, skip: int = 0, limit: int = 10, ):
    """
    Common method to read list of odoo objects
    Args:
        db_model ([type]): SQL Alchemy model
        request (Request): [description]
        skip (int, optional):  
        limit (int, optional): 

    Returns:
        [type]: Odoo objects
    """    
    # check for authentication
    if auth_needed:
        if request.user.is_authenticated != True:
            msg = 'User is not authenticated'
            logger.info(msg)
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=msg)

        # check for authoriations using scopes
        scope = '' if scope is None else scope
        read_scope = f'{scope}:read'
        if scope and read_scope not in request.user.scopes:
            msg = 'User does not have permissions'
            logger.info('user does not have permissions')
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=msg)
    else:
        logger.info(f'Auth not needed')


    db = next(get_db())
    objs = db.query(db_model).offset(skip).limit(limit).all()
    return objs

def read_object(db_model, object_id):
    db = next(get_db())
    obj = db.query(db_model).filter(db_model.id == object_id).first()
    return obj

for odoo_model, model_conf in ODOO_MODELS.items():
    db_model, api_model = create_fast_models(odoo_model)
    # replace if we want to different route for an odoo model
    route_name = model_conf['route'] if model_conf.get('route') else odoo_model.replace('.','-') + 's'
    auth_needed = model_conf.get('auth_needed')
    scope = model_conf.get('scope', odoo_model.replace(',',''))

    # return object list
    # we use partial to pass the db_model as a paramter to read_objects
    read_objects_for_model = partial(read_objects, db_model, auth_needed, scope)
    app.router.add_api_route(f'/odoo/{route_name}', read_objects_for_model, methods=['get'],
                         response_model=List[api_model])

    # return object
    read_object_for_model = partial(read_object, db_model)
    app.add_api_route("/odoo/{0}/".format(route_name) + '{object_id}', read_object_for_model, methods=['get'],
                             response_model=api_model)

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
