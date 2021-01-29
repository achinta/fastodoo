from . import crud, models, schemas
from .database import SessionLocal, engine, get_db
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date
from sqlalchemy.orm import relationship
from .database import Base
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import Depends
from datetime import datetime, date
import pydantic

db_models = {}
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
    model_fields = crud.read_aims_model_fields(odoo_model_name)

    mail_message_fields_to_ignore = ['message_follower_ids', 'message_ids', 'message_main_attachment_id',
                                     'website_message_ids']

    # initialize fastapi model fields
    db_fields = {'__tablename__': get_odoo_table_name(odoo_model_name)}
    pydantic_fields = {}
    readonly_fields = []

    for model_field in model_fields:
        # ignore odoo computed fields and mail_message fields
        if not model_field.store or model_field.name in mail_message_fields_to_ignore:
            continue

        if model_field.readonly:
            readonly_fields.append(model_field.name)

        # TODO check if we can use same for text and char
        if model_field.ttype in ['char', 'text']:
            db_fields[model_field.name] = Column(String, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = str
            else:
                pydantic_fields[model_field.name] = (Optional[str], None)


        if model_field.ttype == 'integer':
            if model_field.name == 'id':
                db_fields[model_field.name] = Column(Integer, primary_key=True)
            else:
                db_fields[model_field.name] = Column(Integer, nullable=(not model_field.required))
            pydantic_fields[model_field.name] = (int, 0)


        if model_field.ttype == 'boolean':
            db_fields[model_field.name] = Column(Boolean, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = bool
            else:
                pydantic_fields[model_field.name] = (Optional[bool], None)

        if model_field.ttype == 'datetime':
            db_fields[model_field.name] = Column(DateTime, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = datetime
            else:
                pydantic_fields[model_field.name] = (Optional[datetime], None)

        if model_field.ttype == 'date':
            db_fields[model_field.name] = Column(Date, nullable=(not model_field.required))
            if model_field.required:
                pydantic_fields[model_field.name] = date
            else:
                pydantic_fields[model_field.name] = (Optional[date], None)

        if model_field.ttype == 'many2one':
            if model_field.name in ['create_uid', 'write_uid', 'address_view_id']:
                continue

            rel_model_name = get_fast_model_name(model_field.relation)
            rel_table_name = get_odoo_table_name(model_field.relation)
            rel_table_col_name = f'{rel_table_name}.id'

            if model_field.name.endswith('_id'):
                id_field_name = model_field.name
                obj_field_name = model_field.name.replace('_id', '')
            else:
                id_field_name = model_field.name + '_id' 
                obj_field_name = model_field.name

            db_fields[id_field_name] = Column(Integer, ForeignKey(rel_table_col_name), nullable=(not model_field.required))
            db_fields[obj_field_name] = relationship(rel_model_name + 'Db')

            if model_field.required:
                pydantic_fields[id_field_name] = (int, 0)
                pydantic_fields[obj_field_name] = db_models[rel_model_name] 
            else:
                pydantic_fields[id_field_name] = (Optional[int], 0)
                pydantic_fields[obj_field_name] = db_models[rel_model_name] 

        # if model_field.ttype == 'many2many':
        #     to_model = get_django_model_name(model_field.relation)

        #     # Create a through model which contains the mapping
        #     rel_model = create_aims_manytomany_rel_model(model_field)

        #     # related name for reverse relationships. Needed if the models have more than one relation
        #     related_name = AIMS_RELATED_NAMES.get((model_field.model, model_field.name))

        #     # add the field
        #     fields[model_field.name] = models.ManyToManyField(to=to_model, through=rel_model, related_name=related_name,
        #                                                       null=(not model_field.required),
        #                                                       through_fields=(model_field.column1, model_field.column2))

    # fields['readonly_fields'] = readonly_fields

    db_model = type(fast_model_name + 'Db', (Base,), db_fields)


    pydantic_model = pydantic.create_model(fast_model_name + 'Api', **pydantic_fields)
    pydantic_model.Config.orm_mode = True

    # add to cache
    db_models[fast_model_name] = db_model
    return db_model, pydantic_model
