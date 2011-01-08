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
    
    def on_delete(self, **kwargs):
        self.controller.deleteAllDimensionValue(self)
    
    __callbacks__ = {
                 'onDelete':on_delete
                 }

    def __str__(self):
        return self.name
    
    @property
    def values(self):
        return self.controller.getAllDimensionValueForDimension(self)
    
    
class DimensionValue(SQLiteEntity):
    
    __primaryKey__ = 'id'
    __tableName__ = "dimensionValue"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR',
                   'dimension': Dimension,                 
                  }
    __comparisonPositives__ = ['dimension','name']
    
    def on_delete(self, **kwargs):
        self.controller.deleteAllAssetDimensionValue(self)
    
    __callbacks__ = {
                 'onDelete':on_delete
                 }
                    
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
        if self.dimensionValue:
            erg = self.dimensionValue.name
            if self.value != 100:
                erg += ":"+str(self.value)
            return erg
        return SQLiteEntity.__repr__(self)
