from avernus.objects.model import SQLiteEntity

class Region(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "region"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'
                  }
    __comparisonPositives__ = ['name']

    def onDelete(self, **kwargs):
        self.controller.deleteRegionFromStock(self)

    __callbacks__ = {
                     'onDelete':onDelete
                     }

    def __str__(self):
        return self.name
