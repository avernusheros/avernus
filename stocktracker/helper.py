import config, time, calendar
from db import *

db = database.get_db()


def update_stock(id):
        item = {}
        #get data from data provider
        data = config.DATA_PROVIDER.get_all(id)
        data['percent'] = 100*float(data['price'])/(float(data['price'])-float(data['change'])) -100
        data['date'] = "%s %s" % (data['price_date'], data['price_time'])
        db.add_quotation(id, float(data['price']), float(data['change'])
                        , data['volume'], data['avg_daily_volume']
                        , data['market_cap'], data['book_value']
                        , data['ebitda'], data['dividend_per_share']
                        , data['dividend_yield'], data['earnings_per_share']
                        , data['52_week_high'], data['52_week_low']
                        , data['price_earnings_ratio']
                        , data['date'])
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


def get_extremum_length(list, max = True):
    """get the longest/shortest item of a list without changing the list"""
    op = None
    if max:
        op = lambda a,b: a > b
    else:
        op = lambda a,b: a < b
    if len(list) == 1:
        return list[0]
    res = list[0]
    for item in list:
        if op(len(item),len(res)):
            res = item
    return item

def getDayOfWeekFromTime(value):
    return config.Weekday[makeTupleFromTime[6]]

def makeTimeTuple(timeString, format = "%m/%d/%Y %H:%M:%S"):
    #print timeString, format
    return time.strptime(timeString, format)

def makeTimeFromTuple(tuple):
    return time.mktime(tuple)

def makeTupleFromTime(aTime):
    return time.localtime(aTime)

def _makeMonthSecondsFromTime(aTime):
    tuple   = makeTupleFromTime(aTime)
    month   = tuple[1]
    year    = tuple[0]
    return calendar.monthrange(year, month)[1] * config.DAY

def makeDayDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, config.DAY)

def makeMinuteDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, config.MINUTE)

def makeHourDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, config.MINUTE)

def makeWeekDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, config.WEEK)

def makeYearDifference(aTime, bTime):
    aYears = makeTupleFromTime(aTime)[0]
    bYears = makeTupleFromTime(bTime)[0]
    return aYears - bYears

def makeMonthDifference(aTime, bTime):
    aMonth = makeTupleFromTime(aTime)[1]
    bMonth = makeTupleFromTime(bTime)[1]
    yearMonths = makeYearDifference(aTime, bTime) * 12
    return yearMonths + (aMonth - bMonth)

def _makeDifference(aTime, bTime, scale):
    return int(aTime - bTime) / scale

def makeScaleListFromTimelist(list):
    """constructs a list of scale points for the plot from the list of times"""
    list.sort()
    pivot = list[0]
    scales = [l - pivot for l in list[1:]]
    erg = [0]
    erg.extend(scales)
    return erg

def normalizeScales(list, unit):
    return [int(item / unit) for item in list]

def normalizeToMinutes(list):
    return normalizeScales(list, config.MINUTE)

def normalizeToHours(list):
    return normalizeScales(list, config.HOUR)

def normalizeToDays(list):
    return normalizeScales(list, config.DAY)

def normalizeToWeeks(list):
    return normalizeScales(list, config.WEEK)

def makePlotGraph(scaleList, values):
    erg = []
    if not len(scaleList) == len(values):
        raise Exception("Unequal list lenght in makePlotGraph")
    for i in range(0,len(values)):
        erg.append((scaleList[i], values[i]))
    return erg

def makeTimeFromYahoo(input):
    """format von yahoo

      date: "30/10/2008"
     time: "12:35pm"
    """
    return makeTimeFromTuple(makeTimeTuple(input, "%d/%m/%Y %I:%M%p"))

def makeTimeFromGTK(input):
    """format von gtk:

    (yyyy, mm, dd) , beispiel (2008, 10, 30)
    """
    #print input
    #gtk months start with 0
    input = (input[0], input[1]+1, input[2])
    return makeTimeFromTuple(makeTimeTuple(str(input), "(%Y, %m, %d)"))

def makeStringFromTime(aTime, format = "%d.%B %Y"):
    return time.strftime(format, makeTupleFromTime(aTime))

"""Format String options: http://www.python.org/doc/2.5.2/lib/module-time.html"""

def makePangoStringSmall(color, text, newline = False):
    suffix = ""
    if newline:
        suffix = "\n"
    return "<span foreground=\""+ color +"\"><small>" +text+ "</small></span>" + suffix
