from avernus.objects.model import SQLiteEntity
from avernus.objects.position import PortfolioPosition

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

    @property
    def total(self):
        return self.price-self.costs

    def __repr__(self):
        return "Dividend " + self.position.stock.name + "|" + str(self.date) + "|" + str(self.total)
