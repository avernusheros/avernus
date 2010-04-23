from stocktracker.objects.model import SQLiteEntity



class Watchlist(SQLiteEntity):

    __primaryKey__ = 'name'
    __tableName__ = "watchlist"
    __columns__ = {
                   'name': 'VARCHAR',
                   'last_update':'TIMESTAMP',
                   'comment':'TEXT',
                  }
