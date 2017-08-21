from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Catalog(Base):
    __tablename__ = 'catalog'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
 
class CatalogItem(Base):
    __tablename__ = 'catalogitem'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    catalog_id = Column(Integer,ForeignKey('catalog.id'))
    catalog = relationship(Catalog) 

engine = create_engine('postgresql://vagrant:new_password@localhost/catalog')
Base.metadata.create_all(engine)