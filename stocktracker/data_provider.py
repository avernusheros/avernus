#!/usr/bin/env python


class DataProvider():

    def get_all(self, symbol):
        """
        Get all available quote data for the given ticker symbol.
        
        Returns a dictionary.
        """
        pass
        
    def get_price(self, symbol): 
        return "N/A"

    def get_change(self, symbol):
        return "N/A"
        
    def get_volume(self, symbol): 
        return "N/A"

    def get_price_date(self, symbol):
        return "N/A"
    
    def get_price_time(self, symbol):
        return "N/A"

    def get_avg_daily_volume(self, symbol): 
        return "N/A"
        
    def get_stock_exchange(self, symbol): 
        return "N/A"
        
    def get_market_cap(self, symbol):
        return "N/A"
       
    def get_book_value(self, symbol):
        return "N/A"

    def get_ebitda(self, symbol): 
        return "N/A"
        
    def get_dividend_per_share(self, symbol):
        return "N/A"

    def get_dividend_yield(symbol): 
        return "N/A"
        
    def get_earnings_per_share(self, symbol): 
        return "N/A"

    def get_52_week_high(self, symbol): 
        return "N/A"
        
    def get_52_week_low(self, symbol): 
        return "N/A"
        
    def get_50day_moving_avg(symbol): 
        return "N/A"
        
    def get_200day_moving_avg(self, symbol): 
        return "N/A"
        
    def get_price_earnings_ratio(self, symbol): 
        return "N/A"

    def get_price_earnings_growth_ratio(self, symbol): 
        return "N/A"

    def get_price_sales_ratio(self, symbol): 
        return "N/A"
        
    def get_price_book_ratio(self, symbol): 
        return "N/A"
    
    def get_short_ratio(self, symbol): 
        return "N/A"
        
    def get_historical_prices(self, symbol, start_date, end_date):
        """
        Get historical prices for the given ticker symbol.
        Date format is 'YYYYMMDD'
        Returns a nested list.
        """
        return "N/A"




