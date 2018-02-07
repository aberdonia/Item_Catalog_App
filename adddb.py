from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User

from datetime import datetime

engine = create_engine('sqlite:///ebay2.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

Customer1 = Category(name="Computer")
session.add(Customer1)
session.commit()

Customer1 = Category(name="Electronics")
session.add(Customer1)
session.commit()

Customer1 = Category(name="Food")
session.add(Customer1)
session.commit()

Customer1 = Category(name="Vehicles")
session.add(Customer1)
session.commit()

Customer1 = Category(name="Entertainment")
session.add(Customer1)
session.commit()

Customer1 = Category(name="Clothing")
session.add(Customer1)
session.commit()


User1 = User(name="Jimmy Jones", email="jimmyjones@gmail.com", picture="#")
session.add(User1)
session.commit()

User1 = User(name="Big Fat Billy", email="jimmyjones@gmail.com", picture="#")
session.add(User1)
session.commit()

Account1 = Item(name="GPU", value=25.00, description="RX 580",
                category_name="Computer", user_id=1)
session.add(Account1)
session.commit()

Account1 = Item(name="PSU", value=21.00, description="EVGA Power Supply",
                category_name="Computer", user_id=2)
session.add(Account1)
session.commit()

print "Finished!"
