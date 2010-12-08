from avernus.objects.model import SQLiteEntity
import avernus.objects.controller


class Sector(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "sector"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'                   
                  }

    def onDelete(self, **kwargs):
        avernus.objects.controller.deleteSectorFromStock(self)
        
    __callbacks__ = {
                     'onDelete':onDelete
                     }
