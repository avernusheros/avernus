from stocktracker.objects.model import SQLiteEntity
from stocktracker.objects.container import Portfolio
from stocktracker.objects.position import PortfolioPosition
        
class Transaction(SQLiteEntity):

    __primaryKey__ = "id"
    __tableName__ = 'trans'
    __columns__ = {
                   "id": "INTEGER",
                   "date": "TIMESTAMP",
                   "type": "INTEGER",
                   "quantity": "INTEGER",
                   "price": "FLOAT",
                   "costs": "FLOAT",
                   "position": PortfolioPosition,
                   "portfolio": Portfolio
                   }


