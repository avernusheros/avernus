from stocktracker.objects.model import SQLiteEntity


class Dividend(SQLiteEntity):

    __primaryKey__ = 'name'
    __tableName__ = "dividend"
    __columns__ = {
                   'name': 'VARCHAR',
                  }
