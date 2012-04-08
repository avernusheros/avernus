from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Date

class Portfolio(Base):
    
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    last_update = Column(Date)
    
    
class Watchlist(Base):
    
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    last_update = Column(Date)
