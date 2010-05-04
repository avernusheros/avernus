from stocktracker.objects.model import SQLiteEntity

class Sector(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "sector"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'                   
                  }
