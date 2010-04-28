from stocktracker.objects.model import SQLiteEntity
from stocktracker.objects.stock import Stock

class Quotation(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "quotation"
    __columns__ = {
                   'id': 'INTEGER',
                   'stock': Stock,
                   'date': 'DATE',
                   'open': 'FLOAT',
                   'high': 'FLOAT',
                   'low': 'FLOAT',
                   'close': 'FLOAT',
                   'volume': 'INTEGER',
                   
                  }
