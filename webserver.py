from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem
from sqlalchemy import desc
app=Flask(__name__)

engine = create_engine('postgresql://vagrant:new_password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')

@app.route('/hello')
def HelloWorld():
    catalog = session.query(Catalog).order_by(desc(Catalog.id)).first()
    print catalog.id
    items = session.query(CatalogItem).filter_by(catalog_id=catalog.id).all();
    output = ''
    print items
    for i in items:
        output += i.name
        output += '</br>'
        output += '</br>'
        output += i.description
        output += '</br>'
        output += '</br>'
    return output

if __name__=='__main__':
    app.debug=True
    app.run(host='0.0.0.0',port=8080)