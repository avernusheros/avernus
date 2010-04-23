from stocktracker.objects.model import SQLiteEntity


class Stock(SQLiteEntity):

    __primaryKey__ = 'name'
    __tableName__ = "tag"
    __columns__ = {
                   'name': 'VARCHAR',
                  }
