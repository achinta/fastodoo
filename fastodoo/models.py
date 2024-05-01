from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from fastodoo.database import Base

class OdooModelField(Base):
    __tablename__ = "ir_model_fields"
    # class Meta(object) =
    #     db_table = 'ir_model_fields'
    #     ordering = ('id',)
    #     managed = False

    # model = models.CharField(max_length=256)
    # model_id = models.IntegerField()
    # name = models.CharField(max_length=256)
    # field_description = models.CharField(max_length=256)
    # ttype = models.CharField(max_length=256)
    # selection = models.CharField(max_length=256)
    # store = models.BooleanField()
    # required = models.BooleanField()
    # readonly = models.BooleanField()
    # relation = models.CharField(max_length=256)
    # relation_table = models.CharField(max_length=256)
    # column1 = models.CharField(max_length=256)
    # column2 = models.CharField(max_length=256)

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
