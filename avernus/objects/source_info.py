from avernus.objects.model import SQLiteEntity
from avernus.objects.stock import Stock

class SourceInfo(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "sourceinfo"
    __columns__ = {
                   'id': 'INTEGER',
                   'source': 'VARCHAR',
                   'stock': Stock,
                   'info': 'VARCHAR'                   
                  }
    __comparisonPositives__ = ['source', 'stock', 'info']
