from typing import List, Optional
from pydantic import BaseModel

class OdooModelField(BaseModel):
    id: Optional[int] = None
    model : Optional[str] = None
    model_id: str
    name: str
    field_description: str
    ttype: str
    selection: Optional[str] = ''
    store : Optional[bool] = None
    required: Optional[bool] = None
    readonly: Optional[bool] = None
    relation: Optional[str] = None
    relation_table: Optional[str] = ''
    column1: Optional[str] = ''
    column2: Optional[str] = ''

    class Config:
        from_attributes = True
