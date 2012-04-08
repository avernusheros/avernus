from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

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
    
    
class PortfolioPosition(Base):
    
    __tablename__ = 'portfolio_position'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    price = Column(Float)
    quantity = Column(Float)
    comment = Column(String)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
    asset_id = Column(Integer, ForeignKey('asset.id'))
    
    portfolio = relationship('Portfolio', backref='positions')
    asset = relationship('Stock')
    
    
    
class Watchlist(Container):
    
    __tablename__ = 'watchlist'
    __mapper_args__ = {'polymorphic_identity': 'watchlist'}
    id = Column(Integer, ForeignKey('container.id'), primary_key=True)
    

class WatchlistPosition(Base):
    
    __tablename__ = 'watchlist_position'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    price = Column(Float)
    quantity = Column(Float)
    comment = Column(String)
    watchlist_id = Column(Integer, ForeignKey('watchlist.id'))
    asset_id = Column(Integer, ForeignKey('asset.id'))
    
    watchlist = relationship('Watchlist', backref='positions')
    asset = relationship('Asset')
