from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem

app=Flask(__name__)

engine = create_engine('postgresql://vagrant:new_password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

firstCatalog=Catalog(name="sport")
session.add(firstCatalog)
session.commit()
firstCatalogItem=CatalogItem(name="football",description="good sport", catalog=firstCatalog)
session.add(firstCatalogItem)
session.commit()
session.query(Catalog).all()
session.query(CatalogItem).all()