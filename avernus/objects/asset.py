from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

class Asset(Base):
    
    __tablename__ = 'asset'
    
    discriminator = Column('type', String(20))
    
    __mapper_args__ = {'polymorphic_on': discriminator}
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(Date)
    isin = Column(String)
    exchange = Column(String)
    currency = Column(String)
    price = Column(Float)
    source = Column(String)
    change = Column(Float)
    
class Dividend(Base):
    
    __tablename__ = 'dividend'
    id = Column(Integer, primary_key=True)
    isin = Column(String)
    price = Column(Float)
    cost = Column(Float)
    shares = Column(Float)
    position_id = Column(Integer, ForeignKey('container.id'))
    position = relationship('Portfolio', backref='dividends')
    
class MetaPosition(object):
    pass
    
class Quotation(Base):
    
    __tablename__ = 'quotation'
    
    id = Column(Integer, primary_key=True)
    exchange = Column(String)
    date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref='quotations')
    
class SourceInfo(Base):
    
    __tablename__ = 'source_info'
    
    id = Column(Integer, primary_key=True)
    source = Column(String)
    info = Column(String)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship('Asset', backref='source_info')
    
class Stock(Asset):
    
    __tablename__ = 'stock'
    __mapper_args__ = {'polymorphic_identity': 'stock'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
