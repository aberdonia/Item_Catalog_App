from flask import Flask, render_template, request, redirect, url_for, flash


# for json loads to decode json import to python string
import httplib2, json, requests

# start db
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

# security imports
from flask import session as login_session
import random, string

# flow imports
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response, jsonify

# client secrets
CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']

#Connect to Database and create database session
engine = create_engine('sqlite:///ebay2.db', connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

cats_all = session.query(Category).all()
cats = []
for cat in cats_all:
	cats.append(cat.name)

items_all = session.query(Item).all()
items = []
for item in items_all:
	items.append(item.name)

app = Flask(__name__)

@app.route('/JSON')
def getAllItems():
	items = session.query(Item).all()
	return jsonify(Items=[i.serialize for i in items])

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
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
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

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

    # see if user exists, if it doesn't create new
    user_id = getUserID(login_session['email'])
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

# helper functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
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

# Create anti-forgery state token
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)



@app.route('/', methods=['GET','POST'])
def index():
	if request.method == 'POST':
		newEntry = Item(name=request.form['name'], category_name=request.form['category'],
        	value=request.form['value'], description=request.form['description'], user_id=login_session['user_id'])
		session.add(newEntry)
		session.commit()
		return redirect(url_for('index'))
	return render_template('index.html', cats = cats)

@app.route('/category/<cat>/')
def category(cat):
	# cats = ["Electronics", "Cars", "Food", "Digital"]
	cat_items_all = session.query(Item).filter_by(category_name=cat).all()
	cat_items = []
	for item in cat_items_all:
		cat_items.append(item.name)
	# print cat.name
	print cat_items
	return render_template('index.html', cat = cat, cats = cats, cat_items = cat_items)

@app.route('/category/<cat>/<item>/')
def item(cat, item):
	cat_items_all = session.query(Item).filter_by(category_name=cat).all()
	cat_items = []
	for each in cat_items_all:
		cat_items.append(each.name)
	item_grab = session.query(Item).filter_by(name=item).one()
	print item_grab.name
	seller = session.query(User).filter_by(id=item_grab.user_id).one()
	print seller.name
	return render_template('index_items.html', item = item_grab, cat = cat, cats = cats, cat_items = cat_items, seller = seller)

@app.route('/category/<cat>/<int:item_id>/edit', methods=['GET','POST'])
def editItem(cat, item_id):
	print "line 1"
	item_grab = session.query(Item).filter_by(id=item_id).one()
	print item_grab
	print item_grab.name
	if 'username' not in login_session:
		return redirect('/login')
	if item_grab.user_id != login_session['user_id']:
		return "Not Authorised"
	if request.method == 'POST':
		editItem = item_grab
		print "edit item:"
		print editItem.name
		if request.form['name']:
			editItem.name = request.form['name']
		print 'value here:'
		if request.form['value']:
			print 'value if'
			editItem.value = request.form['value']
			print request.form['value']
		if request.form['description']:
			editItem.description = request.form['description']
		session.add(editItem)
		session.commit()
		return redirect(url_for('index'))
	else:
		return render_template('editItem.html', item = item_grab, cat = cat, cats = cats)

@app.route('/category/<cat>/<int:item_id>/delete', methods=['GET','POST'])
def deleteItem(cat, item_id):
	item_grab = session.query(Item).filter_by(id=item_id).one()
	if 'username' not in login_session:
		return redirect('/login')
	if item_grab.user_id != login_session['user_id']:
		return "Not Authorised"
	if request.method == 'POST':
		session.delete(item_grab)
		session.commit()
		return redirect(url_for('index'))
	else:
		return render_template('deleteItem.html', item = item_grab, cat = cat)


@app.route('/sell/') ### user protected
def sell():
	if 'username' not in login_session:
		return redirect('/login')
	return render_template('sell.html', cats = cats)
	# cats = ["Electronics", "Cars", "Food", "Digital"]
	# return render_template('sell.html', cats = cats)

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)
