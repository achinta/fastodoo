from . import crud, models, schemas
from .database import SessionLocal, engine, get_db
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from .database import Base
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import Depends
import pydantic

def get_fast_model_name(aims_model_name):
    '''
    For many2one and many2many aims fields, get the related Django model name
    :param model_field:
    :return:
    '''
    model_words = aims_model_name.split('.')
    # convert to camel case
    fast_model_name = ''.join([word[0:1].upper() + word[1:] for word in model_words])

    # replace with the alias if present
    # django_model_name = AIMS_MODEL_ALIAS.get(django_model_name, django_model_name)
    return fast_model_name 

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

    odoo_table_name = odoo_model_name.replace('.', '_')
    mail_message_fields_to_ignore = ['message_follower_ids', 'message_ids', 'message_main_attachment_id',
                                     'website_message_ids']

    # initialize fastapi model fields
    db_fields = {'__tablename__': odoo_table_name}
    pydantic_fields = {}
    readonly_fields = []

    for model_field in model_fields:
        # ignore odoo computed fields and mail_message fields
        if not model_field.store or model_field.name in mail_message_fields_to_ignore:
            continue

        if model_field.readonly:
            readonly_fields.append(model_field.name)

        # TODO check if we can use same for text and char
        # if model_field.ttype in ['char', 'text']:
        #     db_fields[model_field.name] = Column(String, nullable=(not model_field.required))
        #     pydantic_fields[model_field.name] = (str, '')

        if model_field.ttype == 'integer':
            if model_field.name == 'id':
                db_fields[model_field.name] = Column(Integer, primary_key=True)
                pydantic_fields[model_field.name] = (int, 0)
            # else:
            #     db_fields[model_field.name] = Column(Integer, nullable=(not model_field.required))


        # if model_field.ttype == 'boolean':
        #     fields[model_field.name] = models.BooleanField(null=(not model_field.required),
        #                                                    help_text=model_field.field_description)

        # if model_field.ttype == 'datetime':
        #     fields[model_field.name] = models.DateTimeField(null=(not model_field.required),
        #                                                     help_text=model_field.field_description)

        # if model_field.ttype == 'date':
        #     fields[model_field.name] = models.DateField(null=(not model_field.required),
        #                                                 help_text=model_field.field_description)

        # if model_field.ttype == 'many2one':
        #     if model_field.name in ['create_uid', 'write_uid']:
        #         continue
        #     fields[model_field.name] = create_many2one_dynamic_field(model_field)

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

    return db_model, pydantic_model
