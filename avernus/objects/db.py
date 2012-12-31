from avernus import objects
from gi.repository.GObject import GObjectMeta
from sqlalchemy import Column, Integer, create_engine, event
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import mapper, sessionmaker, scoped_session
import logging
import os
import shutil
import time
import traceback


# current version of our model
version = 16

logger = logging.getLogger(__name__)
database = None


# automatically add new objects to the session
@event.listens_for(mapper, 'init')
def auto_add(target, args, kwargs):
    objects.Session.add(target)


class DeclarativeGObjectMeta(DeclarativeMeta, GObjectMeta):
    """Metaclass for Declarative and GObject subclasses."""
    pass


class SQLBase(object):
    """Base class for all SQLAlchemy classes."""

    def delete(self):
        try:
            objects.session.delete(self)
        except:
            objects.session.expunge(self)
        objects.session.commit()

# base for the objects
# Base = declarative_base(cls=GObjectMeta)
objects.Base = declarative_base(cls=SQLBase, metaclass=DeclarativeGObjectMeta)


class Meta(objects.Base):
    __tablename__ = 'meta'

    id = Column(Integer, primary_key=True)
    version = Column(Integer)


def set_version(version):
    m = objects.Session.query(Meta).first()
    m.version = version
    objects.Session.commit()


def backup(db):
    old_db = db + '.backup' + time.strftime(".%Y%m%d-%H%M")
    shutil.copyfile(db, old_db)
    return old_db


def add_new_tables(*args):
        # import all objects that are stored in the db
    # sqlalchemy needs this to setup tables
    from avernus.objects import account
    from avernus.objects import asset
    from avernus.objects import container
    from avernus.objects import dimension
    from avernus.objects import asset_category
    objects.Base.metadata.create_all(engine)


def migrate(from_version, database):
    from avernus.objects import migrations
    scripts = [(9, migrations.to_ten),
                (11, migrations.to_eleven),
                (12, migrations.to_twelve),
                (13, migrations.to_thirteen),
                (14, migrations.to_fourteen),
                (15, migrations.to_fifteen),
                (16, migrations.to_sixteen)
                ]

    # pre sqlalchemy area
    if from_version < 10:
        old_db = backup(database)
        os.remove(database)
        # create new db
        objects.session.connect()
        # move data
        try:
            migrations.to_ten(database, old_db)
        except:
            logger.error("migration failed")
            traceback.print_exc()
            exit(1)
    else:
        # creatae missing tables
        add_new_tables()
        # run migration scripts
        for version, script in scripts:
            if from_version < version:
                logger.info("migrate from version %i to %i" % (from_version, version))
                try:
                    backup(database)
                    script(database)
                    from_version = version
                    set_version(version)
                except:
                    logger.error("migration failed")
                    traceback.print_exc()
                    exit(1)


def set_db(db_file):
    global database
    database = db_file


def create_new_database(create_sample_data=False):
    # create the tables, if not there already
    logger.debug("creating new db")
    add_new_tables()
    # store version
    m = Meta(version=version)
    objects.session.add(m)
    if create_sample_data:
        logger.debug("loading sample data")
        from avernus.objects import migrations
        migrations.load_sample_data(objects.session)
    objects.session.commit()


def connect(create_sample_data=False):
    # connect to the database
    global engine
    engine = create_engine("sqlite:///" + database)

    # get a session
    objects.Session = scoped_session(sessionmaker(bind=engine,
                                          autoflush=True,
                                          autocommit=False))
    objects.session = objects.Session()

    # check if already existing
    if os.path.exists(database):
        logger.debug("existing db")
        m = objects.session.query(Meta).first()
        if m.version < version:
            logger.info("db needs migration")
            migrate(m.version, database)
            set_version(version)
            objects.session.commit()
    else:
        create_new_database(create_sample_data)

