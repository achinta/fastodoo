from fastodoo.database import SessionLocal, engine, get_db, Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date
from sqlalchemy.orm import relationship
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import Depends
from datetime import datetime, date
import pydantic

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from fastodoo.database import Base

class OdooModelField(Base):
    __tablename__ = "ir_model_fields"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String)
    model_id = Column(String)
    name = Column(String)
    field_description = Column(String)
    ttype = Column(String)
    selection = Column(String)
    store  = Column(Boolean)
    required = Column(Boolean)
    readonly = Column(Boolean)
    relation = Column(String)
    relation_table = Column(String)
    column1 = Column(String)
    column2 = Column(String)

class OdooIRModel(Base):
    __tablename__ = "ir_model"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    model = Column(String)
    info = Column(String)
    state = Column(String)
    create_date = Column(DateTime)
    write_date = Column(DateTime)
    transient = Column(Boolean)
    is_mail_thread = Column(Boolean)

sqlalchemy_models = {}
pydantic_models = {}

def get_fast_model_name(aims_model_name):
    '''
    For many2one and many2many odoo fields, get dynamic model name
    :param model_field:
    :return:
    '''
    model_words = aims_model_name.split('.')
    # convert to camel case
    fast_model_name = ''.join([word[0:1].upper() + word[1:] for word in model_words])

    # replace with the alias if present
    # django_model_name = AIMS_MODEL_ALIAS.get(django_model_name, django_model_name)
    return fast_model_name 

def get_odoo_table_name(odoo_model_name):
    return odoo_model_name.replace('.', '_')

def create_model(name, fields=None, bases=(), app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model. https://code.djangoproject.com/wiki/DynamicModels
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.items():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, bases, attrs)

    return model


def create_fast_models(odoo_model_name, abstract=False):
    '''
    Creates a database model and pydantic model dynamically by reading field details from odoo table ir_model_fields
    :param abstract:
    :param aims_model_name: aims model name like 'srcm.abhyasi'
    :return: dynamially created model
    '''
    fast_model_name = get_fast_model_name(odoo_model_name) + ('Abstract' if abstract else '')
    # read the model fields from odoo fields metadata
    from fastodoo import crud
    model_fields = crud.read_aims_model_fields(odoo_model_name)

    mail_message_fields_to_ignore = ['message_follower_ids', 'message_ids', 'message_main_attachment_id',
                                     'website_message_ids']

    # initialize fastapi model fields
    sqlalchemy_fields = {'__tablename__': get_odoo_table_name(odoo_model_name), 
                         '__table_args__': {'extend_existing': True}}
    pydantic_fields = {}
    readonly_fields = []

    # ignore models without fields
    if not model_fields:
        return None, None

    for model_field in model_fields:
        # ignore odoo computed fields and mail_message fields
        if not model_field.store or model_field.name in mail_message_fields_to_ignore:
            continue

        if model_field.readonly:
            readonly_fields.append(model_field.name)

        # TODO check if we can use same for text and char
        if model_field.ttype in ['char', 'text']:
            sqlalchemy_fields[model_field.name] = Column(String, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = (str, Field(default=None))
            else:
                pydantic_fields[model_field.name] = (Optional[str], Field(default=None))

        if model_field.ttype == 'integer':
            if model_field.name == 'id':
                sqlalchemy_fields[model_field.name] = Column(Integer, primary_key=True)
            else:
                sqlalchemy_fields[model_field.name] = Column(Integer, nullable=(not model_field.required))
            pydantic_fields[model_field.name] = (int, Field(default=0))


        if model_field.ttype == 'boolean':
            sqlalchemy_fields[model_field.name] = Column(Boolean, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = (bool, Field(default=None))
            else:
                pydantic_fields[model_field.name] = (Optional[bool], Field(default=None))

        if model_field.ttype == 'datetime':
            sqlalchemy_fields[model_field.name] = Column(DateTime, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = (datetime, Field(default=None))
            else:
                pydantic_fields[model_field.name] = (Optional[datetime], Field(default=None))

        if model_field.ttype == 'date':
            sqlalchemy_fields[model_field.name] = Column(Date, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = (date, Field(default=None))
            else:
                pydantic_fields[model_field.name] = (Optional[date], Field(default=None))

        if model_field.ttype == 'many2one':
            if model_field.name in ['create_uid', 'write_uid', 'address_view_id']:
                continue

            rel_model_name = get_fast_model_name(model_field.relation)
            if rel_model_name not in pydantic_models.keys():
                logger.warning(f"skipping many2one field '{odoo_model_name}'.'{model_field.name}' as {rel_model_name} is not configured")
                continue

            rel_table_name = get_odoo_table_name(model_field.relation)
            rel_table_col_name = f'{rel_table_name}.id'

            if model_field.name.endswith('_id'):
                id_field_name = model_field.name
                obj_field_name = model_field.name.replace('_id', '')
            else:
                id_field_name = model_field.name + '_id' 
                obj_field_name = model_field.name

            sqlalchemy_fields[id_field_name] = Column(Integer, ForeignKey(rel_table_col_name), nullable=(not model_field.required))
            sqlalchemy_fields[obj_field_name] = relationship(rel_model_name + 'Db', foreign_keys=[sqlalchemy_fields[id_field_name]])

            if model_field.required:
                pydantic_fields[id_field_name] = (int, 0)
                pydantic_fields[obj_field_name] = (pydantic_models[rel_model_name], None)
            else:
                pydantic_fields[id_field_name] = (Optional[int], 0)
                pydantic_fields[obj_field_name] = (Optional[pydantic_models[rel_model_name]], None)

    #     if model_field.ttype == 'many2many':
    #         to_model = get_django_model_name(model_field.relation)

    #         # Create a through model which contains the mapping
    #         rel_model = create_aims_manytomany_rel_model(model_field)

    #         # related name for reverse relationships. Needed if the models have more than one relation
    #         related_name = AIMS_RELATED_NAMES.get((model_field.model, model_field.name))

    #         # add the field
    #         fields[model_field.name] = models.ManyToManyField(to=to_model, through=rel_model, related_name=related_name,
    #                                                           null=(not model_field.required),
    #                                                           through_fields=(model_field.column1, model_field.column2))

    # # fields['readonly_fields'] = readonly_fields

    sqlalchemy_model = type(fast_model_name + 'Db', (Base,), sqlalchemy_fields)

    pydantic_model = pydantic.create_model(fast_model_name + 'Pyd', **pydantic_fields)
    # pydantic_model.Config.from_attributes = True

    # add to cache
    sqlalchemy_models[fast_model_name] = sqlalchemy_model
    pydantic_models[fast_model_name] = pydantic_model
    return sqlalchemy_model, pydantic_model
