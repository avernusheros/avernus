from stocktracker.objects.model import SQLiteEntity


class Portfolio(SQLiteEntity):

    __primaryKey__ = "name"
    __tableName__ = 'portfolio'
    __columns__ = {
                   "name": "VARCHAR",
                   "last_update": "TIMESTAMP",
                   "comment": "TEXT",
                   "cash": "FLOAT",
                   }
