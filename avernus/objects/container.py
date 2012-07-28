from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy import event
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import reconstructor
from gi.repository import GObject


class Benchmark(Base):
    __tablename__ = 'benchmark'

    id = Column(Integer, primary_key=True)
    percentage = Column(Float)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    portfolio = relationship('Portfolio')

    def __str__(self):
        return _('Benchmark ')+str(round(self.percentage*100,2))+"%"


class Container(Base, GObject.GObject):
    __tablename__ = 'container'
    discriminator = Column('type', String(30))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    last_update = Column(DateTime)

    __gsignals__ = {
        'position_added': (GObject.SIGNAL_RUN_LAST, None, (object,)),
        'updated' : (GObject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self, *args, **kwargs):
        GObject.GObject.__init__(self)
        Base.__init__(self, *args, **kwargs)

    @reconstructor
    def _init(self):
        GObject.GObject.__init__(self)

    def __iter__(self):
        return self.positions.__iter__()

GObject.type_register(Container)


class Portfolio(Container):
    __tablename__ = 'portfolio'
    __mapper_args__ = {'polymorphic_identity': 'portfolio'}
    id = Column(Integer, ForeignKey('container.id'), primary_key=True)
    positions = relationship('PortfolioPosition', backref='portfolio', cascade="all,delete")

    def __iter__(self):
        return self.positions.__iter__()


class Watchlist(Container):
    __tablename__ = 'watchlist'
    __mapper_args__ = {'polymorphic_identity': 'watchlist'}
    id = Column(Integer, ForeignKey('container.id'), primary_key=True)
    positions = relationship('WatchlistPosition', backref='watchlist', cascade="all,delete")


class Position(Base):
    __tablename__ = 'position'
    discriminator = Column('type', String(30))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    price = Column(Float)
    comment = Column(String, default='')

    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref='positions')

    def __iter__(self):
        return self.positions.__iter__()


class PortfolioPosition(Position):
    __tablename__ = 'portfolio_position'
    __mapper_args__ = {'polymorphic_identity': 'portfolioposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)
    quantity = Column(Float, default=0.0)

    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))


class WatchlistPosition(Position):
    __tablename__ = 'watchlist_position'
    __mapper_args__ = {'polymorphic_identity': 'watchlistposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)
    quantity = 1

    watchlist_id = Column(Integer, ForeignKey('watchlist.id'))
