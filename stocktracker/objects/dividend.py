from stocktracker.objects.model import SQLiteEntity
from stocktracker.objects.position import PortfolioPosition

class Dividend(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "dividend"
    __columns__ = {
                   'id'      : 'INTEGER',
                   'date'    : 'TIMESTAMP',
                   'price'   : 'FLOAT',
                   'costs'   : 'FLOAT',
                   'shares'  : 'FLOAT',
                   'position': PortfolioPosition
                   
                  }
    
