from typing import List, Optional
from pydantic import BaseModel

class OdooModelField(BaseModel):
    id: Optional[int] = None
    model : Optional[str] = None
    # model_id: str
    # name: str
    # field_description: str
    # ttype: str
    # selection: str
    # store : bool
    # required: bool
    # readonly: bool
    # relation: str
    # relation_table: Column(String)
    # column1: str
    # column2: str

    class Config:
        orm_mode = True
