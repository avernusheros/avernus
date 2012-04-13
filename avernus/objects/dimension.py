from avernus.objects import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

class Dimension(Base):
    
    __tablename__ = 'dimension'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
class DimensionValue(Base):

    __tablename__ = 'dimension_value'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    dimension_id = Column(Integer, ForeignKey('dimension.id'))
    dimension = relationship('Dimension', backref='values')
    
class AssetDimensionValue(Base):
    
    __tablename__ = 'asset_dimension_value'
    
    id = Column(Integer, primary_key=True)
    value = Column(Float)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    dimension_value_id = Column(Integer, ForeignKey('dimension_value.id'))
    asset = relationship('Asset')
    dimension_value = relationship('DimensionValue')
