from flask import Flask, render_template, request, redirect, url_for


# for json loads to decode json import to python string
import httplib2, json, requests

# start db
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

# for json loads to decode json import to python string
import httplib2, json, requests

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

# cats = ["Electronics", "Cars", "Food", "Digital"]

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():
	if request.method == 'POST':
		newEntry = Item(name=request.form['name'], category_name=request.form['category'],
        	value=request.form['value'], description=request.form['description'])
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
	return render_template('index_items.html', item = item_grab, cat = cat, cats = cats, cat_items = cat_items)

@app.route('/sell/')
def sell():
	return render_template('sell.html', cats = cats)
	# cats = ["Electronics", "Cars", "Food", "Digital"]
	# return render_template('sell.html', cats = cats)




if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 8000)
