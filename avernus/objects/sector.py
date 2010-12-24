from avernus.objects.model import SQLiteEntity

class Sector(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "sector"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'                   
                  }
    __comparisonPositives__ = ['name']

    def onDelete(self, **kwargs):
        self.controller.deleteSectorFromStock(self)
        
    __callbacks__ = {
                     'onDelete':onDelete
                     }

    def __str__(self):
        return self.name
