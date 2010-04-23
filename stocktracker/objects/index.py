from stocktracker.objects.model import SQLiteEntity



class Index(SQLiteEntity):

    __primaryKey__ = 'name'
    __tableName__ = "indices"
    __columns__ = {
                   'name': 'VARCHAR',
                   'last_update':'TIMESTAMP',
                  }
