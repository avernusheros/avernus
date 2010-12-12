from avernus.objects.model import SQLiteEntity
from avernus.objects.stock import Stock

class Quotation(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "quotation"
    __columns__ = {
                   'id': 'INTEGER',
                   'stock': Stock,
                   'exchange':'VARCHAR',
                   'date': 'DATE',
                   'open': 'FLOAT',
                   'high': 'FLOAT',
                   'low': 'FLOAT',
                   'close': 'FLOAT',
                   'volume': 'INTEGER',
                   
                  }
    __comparisonPositives__ = ['stock','date', 'exchange']