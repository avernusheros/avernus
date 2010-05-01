from stocktracker.objects.model import SQLiteEntity


class Exchange(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "exchange"
    __columns__ = {
                   'id'  : 'INTEGER',
                   'name': 'VARCHAR',
                  }
    __comparisonPositives__ = ['name']
