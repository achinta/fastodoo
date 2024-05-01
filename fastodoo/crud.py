from typing import Dict
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from fastodoo.database import get_db
from fastodoo import models

import logging
logger = logging.getLogger(__name__)


def read_aims_model_fields(model_name: str):
    db = next(get_db())
    return db.query(models.OdooModelField).filter(models.OdooModelField.model == model_name).all()

def read_objects(sqlalchemy_model, skip: int = 0, limit: int = 10, ):
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
    # if auth_needed:
    #     if request.user.is_authenticated != True:
    #         msg = 'User is not authenticated'
    #         logger.info(msg)
    #         return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=msg)

    #     # check for authoriations using scopes
    #     scope = '' if scope is None else scope
    #     read_scope = f'{scope}:read'
    #     if scope and read_scope not in request.user.scopes:
    #         msg = 'User does not have permissions'
    #         logger.info('user does not have permissions')
    #         return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=msg)
    # else:
    #     logger.info(f'Auth not needed')


    db = next(get_db())
    objs = db.query(sqlalchemy_model).offset(skip)
    if limit > 0:
        objs = objs.limit(limit)
    objs = objs.all()
    return objs

def read_object(sqlalchemy_model, object_id):
    ''''''
    db = next(get_db())
    obj = db.query(sqlalchemy_model).filter(sqlalchemy_model.id == object_id).first()
    return obj

# def get_odoo_models() -> Dict[str, Dict[str, str]]:
#     '''Get odoo models and their corresponding config dict if any'''
#     odoo_models 