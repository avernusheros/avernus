from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# base for the objects
Base = declarative_base()

from account import *
from container import *
from asset import *
from dimension import *

# connect to the database
engine = create_engine('sqlite:///sqlite.db'#, echo=True
)     
# create the tables, if not there already
Base.metadata.create_all(engine)
# get a session
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

