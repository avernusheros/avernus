from avernus.objects.model import SQLiteEntity

class Risk(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "risk"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'                   
                  }
    __comparisonPositives__ = ['name']

    def onDelete(self, **kwargs):
        self.controller.deleteRiskFromStock(self)
        
    __callbacks__ = {
                     'onDelete':onDelete
                     }

    def __str__(self):
        return self.name
