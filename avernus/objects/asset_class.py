from avernus.objects.model import SQLiteEntity

class AssetClass(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "assetclass"
    __columns__ = {
                   'id': 'INTEGER',
                   'name': 'VARCHAR'                   
                  }
    __comparisonPositives__ = ['name']

    def onDelete(self, **kwargs):
        self.controller.deleteAssetClassFromStock(self)
        
    __callbacks__ = {
                     'onDelete':onDelete
                     }

    def __str__(self):
        return self.name
