try:
    import config
    from data import *
except:
    pass



class Stock(object):
    """ """
    def __init__(self, stock_id, comment):
        #init variables
        self.stock_id          = stock_id
        self.currentPrice      = None
        self.currentPercent    = None
        self.currentChange     = None
        self.currentDate       = None
        self.startPrice        = None
        self.startDate         = None 
        self.comment           = comment
        self.change            = None
        self.percent           = None
        self.mkt_cap           = None
        self.avg_vol           = None
        self.fiftytwoweek_low  = None
        self.fiftytwoweek_high = None
        self.eps               = None
        self.pe                = None
        #database connection
        self.db = database.get_db() 

    def get_currentprice_text(self):
        color = '#606060'
        text = ""
        text = text + str(self.currentPrice) +"\n<span foreground=\""+ color +"\"><small>" +str(self.currentDate) + "</small></span>"
        return text
        
    def get_price_text(self):
        color = '#606060'
        text = ""
        text = text + str(self.startPrice) +"\n<span foreground=\""+ color +"\"><small>" +str(self.startDate) + "</small></span>"
        return text
        
    def get_name_text(self):
        color = '#606060'
        text = ""
        info = self.db.get_stock_name(self.stock_id)
        text = text + info[0] +"\n \
                <span foreground=\""+ color +"\"><small>" +info[1]+ "</small></span>\n \
                 <span foreground=\""+ color +"\"><small>" +info[2]+ "</small></span>"
        return text
    
    def get_change_text(self):
        color = '#606060'
        text = ""
        text = text + str(self.change) +"\n<span foreground=\""+ color +"\"><small>" +str(round(self.percent,2)) + "</small></span>"
        return text
        
    def get_currentchange_text(self):
        color = '#606060'
        text = ""
        text = text + str(self.currentChange) +"\n<span foreground=\""+ color +"\"><small>" +str(round(self.currentPercent, 2)) + "</small></span>"
        return text

    def get_datetime_string(self, datetime):
        """Used to get the date and the time in the specified format
        @returns - string - the date and the time.
        """
        ret = ""
        return ret
 
    def update(self):
        #get data from data provider
        data = config.DATA_PROVIDER.get_all(self.stock_id)
        self.currentPrice       = float(data['price'])
        self.currentChange      = float(data['change'])
        self.currentPercent     = 100*self.currentPrice/(self.currentPrice-self.currentChange)-100
        self.currentDate        = "%s %s" % (data['price_date'], data['price_time'])
        self.mkt_cap            = data['market_cap']
        self.avg_vol            = data['avg_daily_volume']
        self.fiftytwoweek_low   = data['52_week_high']
        self.fiftytwoweek_high  = data['52_week_low']
        self.eps                = data['earnings_per_share']
        self.pe                 = data['price_earnings_ratio']
                                    
        #on first update
        if (self.startPrice == None):
            self.startPrice = self.currentPrice
            self.startDate = self.currentDate
            self.change = 0.00
            self.percent = 0.00
        else:
            self.change = self.currentPrice - self.startPrice
            self.percent = 100*self.currentPrice/self.startPrice -100



