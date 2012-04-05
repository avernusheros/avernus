from avernus.objects.container import Portfolio
from avernus.objects.model import SQLiteEntity


class Benchmark(SQLiteEntity):

    __primaryKey__ = 'id'
    __tableName__ = "portfolioBenchmarks"
    __columns__ = {
                   'id': 'INTEGER',
                   'percentage': 'FLOAT',
                   'portfolio': Portfolio
                  }
    __comparisonPositives__ = ['percentage', 'portfolio']


