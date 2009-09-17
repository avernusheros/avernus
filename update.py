import ystockquote
import objects


class updater:
    def __init__(self, model):
        self.model = model

    def get_quotations(self, stocks):
        for id, stock in stocks:
            try:   
                price = ystockquote.get_price(stock.symbol)
            except:
                print "failed to get quotation from yahoo"
            else:
                date = 00000
                id = self.model.store.create_quotation(stock_id, date, price)
                objects.Quotation(id, stock_id, date, price)   
    
