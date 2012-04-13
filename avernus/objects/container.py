from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship

class Benchmark(Base):

    __tablename__ = 'benchmark'

    id = Column(Integer, primary_key=True)
    percentage = Column(Float)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    portfolio = relationship('Portfolio', backref='benchmarks')

class Container(Base):

    __tablename__ = 'container'
    discriminator = Column('type', String(30))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    last_update = Column(Date)

    def __iter__(self):
        return self.positions.__iter__()

class Portfolio(Container):

    __tablename__ = 'portfolio'
    __mapper_args__ = {'polymorphic_identity': 'portfolio'}
    id = Column(Integer, ForeignKey('container.id'), primary_key=True)


class Watchlist(Container):

    __tablename__ = 'watchlist'
    __mapper_args__ = {'polymorphic_identity': 'watchlist'}
    id = Column(Integer, ForeignKey('container.id'), primary_key=True)


class Position(Base):
    __tablename__ = 'position'
    discriminator = Column('type', String(30))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    price = Column(Float)
    comment = Column(String)
    quantity = Column(Float)

    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    asset_id = Column(Integer, ForeignKey('asset.id'))

    def __iter__(self):
        return self.positions.__iter__()


class PortfolioPosition(Position):
    __tablename__ = 'portfolio_position'
    __mapper_args__ = {'polymorphic_identity': 'portfolioposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)

    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    portfolio = relationship('Portfolio', backref='positions')


class WatchlistPosition(Position):
    __tablename__ = 'watchlist_position'
    __mapper_args__ = {'polymorphic_identity': 'watchlistposition'}
    id = Column(Integer, ForeignKey('position.id'), primary_key=True)

    watchlist_id = Column(Integer, ForeignKey('watchlist.id'))
    watchlist = relationship('Watchlist', backref='positions')
