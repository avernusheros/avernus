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
    
class Stock(Asset):
    
    __tablename__ = 'stock'
    __mapper_args__ = {'polymorphic_identity': 'stock'}
    id = Column(Integer, ForeignKey('asset.id'), primary_key=True)
