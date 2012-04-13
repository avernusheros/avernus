from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship

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
    date = Column(Date)
    position_id = Column(Integer, ForeignKey('container.id'))
    position = relationship('Portfolio', backref='dividends')
    
class Fund(Asset):
    
    __tablename__ = 'fund'
    __mapper_args__ = {'polymorphic_identity': 'fund'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    ter = Column(Float)
    
    
class Etf(Asset):
    
    __tablename__ = 'etf'
    __mapper_args__ = {'polymorphic_identity': 'etf'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
    ter = Column(Float)
    
    
class Bond(Asset):
    
    __tablename__ = 'bond'
    __mapper_args__ = {'polymorphic_identity': 'bond'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)

    
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
    
class Transaction(Base):
    
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    quantity = Column(Float)
    price = Column(Float)
    cost = Column(Float)
    type = Column(Integer)
    position_id = Column(Integer, ForeignKey('portfolio_position.id'))
    position = relationship('PortfolioPosition', backref='transactions')
