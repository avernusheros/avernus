import unittest
import avernus.objects.store as store
import avernus.objects.model as model
from avernus.controller import controller
import avernus.objects.container as container
from avernus.objects.position import PortfolioPosition as Position
import datetime

dbfile = ":memory:"
create = True

class Test(unittest.TestCase):

    def setUp(self):
        self.portfolios = []
        self.positions = []
        self.store = store.Store(dbfile)
        model.store = self.store
        controller.createTables()
        print "Tables created"
        if create:
            pf_a =controller.newPortfolio(name="erstesPort",
                                       last_update=datetime.datetime.now(),
                                       comment="einKommentar",
                                       cash=0.0
                                       )
            s1 = controller.newPortfolioPosition(
                                   date=datetime.datetime.now(),
                                   price=1.58,
                                   quantity=152,
                                   portfolio=pf_a,
                                   stock=None,
                                   comment="allesKommentieren"
                                  )
            s2 = controller.newPortfolioPosition(
                                    date=datetime.datetime.now(),
                                   price=1.85,
                                   quantity=125,
                                   portfolio=pf_a,
                                   stock=None,
                                   comment="allesKommentieren2"
                                  )
            s3 = controller.newPortfolioPosition(
                                date=datetime.datetime.now(),
                               price=14.5,
                               quantity=512,
                               portfolio=pf_a,
                               stock=None,
                               comment="allesKommentieren3"
                                  )
            print "Data Created"
        self.portfolios = controller.getAllPortfolio()
        self.positions = controller.getAllPosition()


    def tearDown(self):
        pass


    def testControllerFunctions(self):
        port0pos = controller.getPositionForPortfolio(self.portfolios[0])
        count = 0
        for port in self.portfolios:
            for pos in port:
                count+=1
                print pos
        self.assertEquals(count,3)
        for pos in port0pos:
            print pos.portfolio, self.portfolios[0]
            self.assertEquals(pos.portfolio,self.portfolios[0])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
