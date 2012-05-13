from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

import time
import shutil
import logging
import os

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

def backup(db):
    old_db = db+'.backup'+time.strftime(".%Y%m%d-%H%M")
    shutil.copyfile(db, old_db)
    return old_db


def migrate(from_version, database):
    from avernus.objects import migrations
    scripts = [(9, migrations.to_ten)]

    # pre sqlalchemy area
    if from_version < 10:
        old_db = backup(database)
        os.remove(database)
        # create new db
        connect()
        # move data
        try:
            migrations.to_ten(database, old_db)
        except:
            logger.error("migration failed")
            import traceback
            traceback.print_exc()
            exit(1)
    else:
        for version, script in scripts:
            if from_version <= version:
                logger.info("migrate from version %i to %i", (from_version, version))
                try:
                    backup(database)
                    script(database)
                    from_version = version
                except:
                    logger.error("migration failed")
                    exit(1)
database = None
session = None
Session = None

def set_db(db_file):
    global database
    database = db_file

def connect():
    # connect to the database
    engine = create_engine("sqlite:///"+database, poolclass=QueuePool,
                            #, echo=True
    )

    # get a session
    global session
    global Session
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()

    # check if already existing
    if os.path.exists(database):
        logger.debug("existing db")
        m = session.query(Meta).first()
        if m.version < version:
            logger.info("db needs migration")
            migrate(m.version, database)
            m.version = version
            session.commit()
    else:
        logger.debug("creating new db")
        # create the tables, if not there already
        Base.metadata.create_all(engine)
        # store version
        m = Meta(version=version)
        session.add(m)
        session.commit()
