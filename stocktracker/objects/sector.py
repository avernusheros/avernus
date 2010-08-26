from stocktracker.objects.model import SQLiteEntity
import stocktracker.objects.controller


class Sector(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "sector"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'                   
                  }

    def onDelete(self, **kwargs):
        stocktracker.objects.controller.deleteSectorFromStock(self)
        
    __callbacks__ = {
                     'onDelete':onDelete
                     }
