from stocktracker.objects.model import SQLiteEntity


class Tag(SQLiteEntity):

    __primaryKey__ = 'name'
    __tableName__ = "tag"
    __columns__ = {
                   'name': 'VARCHAR',
                  }
