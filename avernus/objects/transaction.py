from avernus.objects.model import SQLiteEntity
from avernus.objects.position import PortfolioPosition

SELL     = 0
BUY      = 1

TYPES = {SELL: 'SELL',
         BUY: 'BUY',
         }  

        
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
                   }
    @property
    def total(self):
        if self.type==BUY:
            sign = -1
        else:
            sign = 1             
        return sign*self.price*self.quantity - self.costs
    
    @property
    def type_string(self):
        if self.type in TYPES:
            return TYPES[self.type]
        return ''

    def is_sell(self):
        return self.type == SELL
