from flask import Flask,render_template,request,url_for,flash,redirect,make_response,jsonify
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem, User
from sqlalchemy import desc

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2,random, string,json
import requests

app=Flask(__name__)

engine = create_engine('postgresql://vagrant:new_password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
CLIENT_ID="900451959177-0jciq7nf7jv1uhibgd05njd6n152lneu.apps.googleusercontent.com";
APPLICATION_NAME = "Catalog Application"

GLOBALPARAMS= {
    "islogin":False,
    "applicationName":APPLICATION_NAME
}

#query function
def getCatalogId(catalog_name):
    try:
        catalog = session.query(Catalog).filter_by(name=catalog_name).first()
        return catalog.id
    except:
        return None

def getCatalog():
    try:
        catalog =session.query(Catalog).order_by(desc(Catalog.id)).all()
        return catalog
    except:
        return []

def getCatalogItems(catalogid):
    try:
        items = session.query(CatalogItem).filter_by(catalog_id=catalogid).all()
        return items
    except:
        return []

@app.route('/',methods=['GET'])
def main():
    catalog = getCatalog();
    if 'username' not in login_session:
        GLOBALPARAMS["islogin"]=False
        return render_template('main.html',catalogs=catalog, g=GLOBALPARAMS)
    else:
        GLOBALPARAMS["islogin"]=True
        return render_template('main.html',catalogs=catalog, g=GLOBALPARAMS)

#login function 
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    print login_session
    if 'username' not in login_session:
        GLOBALPARAMS["islogin"]=False
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html', STATE=state, g=GLOBALPARAMS)
    else:
        GLOBALPARAMS["islogin"]=True
        return redirect('/', g=GLOBALPARAMS)

@app.route('/gconnect', methods=['POST'])
def gconnect():

    #Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        print 1
        oauth_flow.redirect_uri = 'postmessage'
        print 2
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    print url
    h = httplib2.Http()
    
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    print "result";
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    print user_id
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions
def createUser(login_session):
    #print login_session
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    print newUser
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



# application function


@app.route('/Snowboarding/<int:catalogid>',methods=['GET'])
def Snowboard(catalogid):
   return render_template('main.html',items=getCatalogItems(catalogid),catalogs=getCatalog(),catalogid=catalogid)

@app.route('/Snowboarding/new', methods=['GET','POST'])
def SnowboardCatalogAdd():
    # if 'username' not in login_session:
    #     GLOBALPARAMS["islogin"]=True
    #     return redirect('/login')
    if request.method == 'POST':
        catalog_name=request.form['name']
        if catalog_name:
            print getCatalogId(catalog_name)
            if not getCatalogId(catalog_name):
                catalog=Catalog(name=request.form['name'])
                session.add(catalog)
                session.commit()
                flash("new catalog item created!")
                return redirect(url_for('Snowboard', catalogid=catalog.id))
            else:
                flash("cataloname has exist")
                return render_template('SnowboardCatalogAdd.html')
        else:
            flash("cataloname can't be empty")
            return render_template('SnowboardCatalogAdd.html')
    else:
        return render_template('SnowboardCatalogAdd.html')

@app.route('/Snowboarding/<int:catalogid>/new', methods=['GET','POST'])
def SnowboardItemAdd(catalogid):
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        newItem = CatalogItem(name=request.form['name'], description=request.form[
                           'description'], catalog_id=catalogid)
        session.add(newItem)
        session.commit()
        flash("new menu item created!")
        return redirect(url_for('Snowboard', catalogid=catalogid))
    else:
        return render_template('SnowboardItemAdd.html',catalogid=catalogid)
    

@app.route('/Snowboarding/<int:catalogid>/<int:itemid>', methods=['GET','PUT'])
def SnowboardItemEdit(catalogid,itemid):
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'PUT':
        output = 'PUT edit'
        output += '</br>'
        output += str(catalog_id)
        return output
    else:
        item = session.query(CatalogItem).filter_by(id=itemid).first();
        return render_template('SnowboardItem.html',item=item,catalogid=catalogid,itemid=itemid)


@app.route('/Snowboarding/<int:catalog_id>/<int:item_id>', methods=['DELETE'])
def SnowboarditemDelete(catalog_id,item_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'DELETE':
        output = 'DELETE DELETE'
        output += '</br>'
        output += str(catalog_id)
        return output

if __name__=='__main__':
    app.secret_key = 'super_secret_key'
    app.debug=True
    app.run(host='0.0.0.0',port=8080)