from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

import logging

logger = logging.getLogger(__name__)


# current version of our model
version = 10

# base for the objects
Base = declarative_base()

from account import *
from container import *
from asset import *
from dimension import *


class Meta(Base):
    __tablename__ = 'meta'

    id = Column(Integer, primary_key=True)
    version = Column(Integer)


# connect to the database
engine = create_engine('sqlite:///sqlite.db'#, echo=True
)

# get a session
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

# check if already existing
if False:#existing:
    logger.debug("existing db")
    current_version = get_version()
    if current_version < version:
        logger.info("db needs migration")
        #migrate!!
else:
    logger.debug("creating new db")
    # create the tables, if not there already
    Base.metadata.create_all(engine)
    # store version
    m = Meta(version=version)
    session.add(m)
    session.commit()

