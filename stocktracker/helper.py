import config
from data import *

db = database.get_db()


def update_stock(id):
        item = {}
        #get data from data provider
        data = config.DATA_PROVIDER.get_all(id)
        data['percent'] = 100*float(data['price'])/(float(data['price'])-float(data['change'])) -100
        db.add_quotation(id, float(data['price']), float(data['change'])
                        , data['volume'], data['avg_daily_volume']
                        , data['market_cap'], data['book_value']
                        , data['ebitda'], data['dividend_per_share']
                        , data['dividend_yield'], data['earnings_per_share']
                        , data['52_week_high'], data['52_week_low']
                        , data['price_earnings_ratio']
                        , "%s %s" % (data['price_date'], data['price_time']))
        return data


def get_arrow_type(percent, large = False):
    type = 0
    for th in config.TRESHHOLDS:
        if percent > th:
            type += 1
    if large:
        return config.ARROWS_LARGE[str(type)]
    else:
        return config.ARROWS_SMALL[str(type)]
