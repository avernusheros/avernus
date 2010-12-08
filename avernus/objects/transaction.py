from avernus.objects.model import SQLiteEntity
from avernus.objects.container import Portfolio
from avernus.objects.position import PortfolioPosition

SELL     = 0
BUY      = 1
SPLIT    = 2
DEPOSIT  = 3
WITHDRAW = 4

TYPES = {SELL: 'SELL',
         BUY: 'BUY',
         SPLIT: 'SPLIT',
         DEPOSIT: 'DEPOSIT',
         WITHDRAW: 'WITHDRAW',
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
                   "portfolio": Portfolio
                   }
    @property
    def total(self):
        if self.type==BUY or self.type==WITHDRAW:
            sign = -1
        else:
            sign = 1             
        return sign*self.price*self.quantity - self.costs
    
    @property
    def type_string(self):
        if self.type in TYPES:
            return TYPES[self.type]
        return ''
