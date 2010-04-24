'''
Created on Apr 24, 2010

@author: bastian
'''
import unittest
import stocktracker.objects.store as store
import stocktracker.objects.model as model
import stocktracker.objects.controller as controller
import stocktracker.objects.container as container
from stocktracker.objects.position import PortfolioPosition as Position
#from stocktracker.objects.stock import Stock
import datetime

dbfile = "stocktracker/tests/stockmodel.db"
create = False

class Test(unittest.TestCase):

    def setUp(self):
        self.portfolios = []
        self.positions = []
        self.store = store.Store(dbfile)
        model.store = self.store
        controller.createTables()
        print "Tables created"
        if create:
            self.portfolios.append(container.Portfolio(name="erstesPort",
                                                       last_update=datetime.datetime.now(),
                                                       comment="einKommentar",
                                                       cash=0.0
                                                       ))
            self.portfolios.append(container.Portfolio(name="zweitesPort",
                                                       last_update=datetime.datetime.now(),
                                                       comment="WhoCommentsAPortfolio?",
                                                       cash=5.0
                                                       ))
            self.positions.append(Position(date=datetime.datetime.now(),
                                           type=0,
                                           price=1.58,
                                           quantity=152,
                                           portfolio=self.portfolios[0],
                                           stock=None,
                                           comment="allesKommentieren"
                                  ))
            self.positions.append(Position(date=datetime.datetime.now(),
                                           type=1,
                                           price=1.85,
                                           quantity=125,
                                           portfolio=self.portfolios[0],
                                           stock=None,
                                           comment="allesKommentieren2"
                                  ))
            self.positions.append(Position(date=datetime.datetime.now(),
                                           type=2,
                                           price=14.5,
                                           quantity=512,
                                           portfolio=self.portfolios[0],
                                           stock=None,
                                           comment="allesKommentieren3"
                                  ))
            self.positions.append(Position(date=datetime.datetime.now(),
                                           type=3,
                                           price=11.5,
                                           quantity=142,
                                           portfolio=self.portfolios[1],
                                           stock=None,
                                           comment="allesKommentieren4"
                                  ))
            for el in self.portfolios:
                el.insert()
            #print self.portfolios
            for el in self.positions:
                el.insert()
            print "Data Created"
        self.portfolios = controller.getAllPortfolio()
        self.positions = controller.getAllPosition()
        

    def tearDown(self):
        pass


    def testControllerFunctions(self):
        port0pos = controller.getPositionForPortfolio(self.portfolios[0])
        for port in self.portfolios:
            for pos in port:
                print pos
        self.assertEquals(len(port0pos),3)
        for pos in port0pos:
            self.assertEquals(pos.portfolio,self.portfolios[0])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()