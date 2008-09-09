try:
    import config
except:
    pass



class Stock(object):
    """ """
    def __init__(self, symbol, name, comment):
        #init variables
        self.symbol            = symbol
        self.currentPrice      = None
        self.currentPercent    = None
        self.currentDate       = None
        self.name              = name
        self.watchStartPrice   = None
        self.watchStartDate    = None 
        self.comment           = comment
        self.change            = None
        self.percent           = None
        self.mkt_cap           = None
        self.avg_vol           = None
        self.fiftytwoweek_low  = None
        self.fiftytwoweek_high = None
        self.eps               = None
        self.pe                = None

    def get_currentprice_text(self):
        color = '#606060'
        text = ""
        text = text + str(self.currentPrice) +"\n<span foreground=\""+ color +"\"><small>" +str(self.currentDate) + "</small></span>"
        return text
        
    def get_price_text(self):
        color = '#606060'
        text = ""
        text = text + str(self.watchStartPrice) +"\n<span foreground=\""+ color +"\"><small>" +str(self.watchStartDate) + "</small></span>"
        return text
        
    def get_name_text(self):
        color = '#606060'
        text = ""
        text = text + self.name +"\n<span foreground=\""+ color +"\"><small>" +self.symbol + "</small></span>"
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
        print self.watchStartDate
        return ret
 
    def update(self):
        #get data from data provider
        self.currentPrice       = config.DATA_PROVIDER.get_price(self.symbol)
        self.currentChange      = config.DATA_PROVIDER.get_change(self.symbol)
        self.currentPercent     = 100*self.currentPrice/(self.currentPrice-self.currentChange)-100
        self.currentDate        = "%s %s" % (config.DATA_PROVIDER.get_price_date(self.symbol)
                                    , config.DATA_PROVIDER.get_price_time(self.symbol))
        self.mkt_cap            = config.DATA_PROVIDER.get_market_cap(self.symbol)
        self.avg_vol            = config.DATA_PROVIDER.get_avg_daily_volume(self.symbol)
        self.fiftytwoweek_low   = config.DATA_PROVIDER.get_52_week_high(self.symbol)
        self.fiftytwoweek_high  = config.DATA_PROVIDER.get_52_week_low(self.symbol)
        self.eps                = config.DATA_PROVIDER.get_earnings_per_share(self.symbol)
        self.pe                 = config.DATA_PROVIDER.get_price_earnings_ratio(self.symbol)              
                                    
        #on first update
        if (self.watchStartPrice == None):
            self.watchStartPrice = self.currentPrice
            self.watchStartDate = self.currentDate
            self.change = 0.00
            self.percent = 0.00
        else:
            self.change = self.currentPrice - self.watchStartPrice
            self.percent = 100*self.currentPrice/self.watchStartPrice -100



