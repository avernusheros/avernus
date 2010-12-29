'''
Created on Dec 28, 2010

@author: simpsus
'''
from avernus.objects.model import SQLiteEntity
from avernus.objects.stock import Stock

class Dimension(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "dimension"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'                   
                  }
    __comparisonPositives__ = ['name']

    def __str__(self):
        return self.name
    
    @property
    def values(self):
        return self.controller.getDimensionValueForDimension(self)
    
class DimensionValue(SQLiteEntity):
    
    __primaryKey__ = 'id'
    __tableName__ = "dimensionValue"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'dimension': Dimension,                 
                  }
    __comparisonPositives__ = ['dimension','name']
    
    def __repr__(self):
        return self.name
    
class AssetDimensionValue(SQLiteEntity):
    
    __primaryKey__ = 'id'
    __tableName__ = "AssetDimensionValue"
    __columns__ = {
                   'id': 'INTEGER',
                   'stock': Stock,
                   'dimensionValue': DimensionValue,
                   'value': 'FLOAT'                 
                  }
    __comparisonPositives__ = ['dimensionValue','stock']
    
    def __repr__(self):
        erg = self.dimensionValue.name
        if self.value != 1.0:
            erg += ":"+str(self.value)
        return erg