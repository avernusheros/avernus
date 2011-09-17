from avernus.gui import gui_utils
from avernus import date_utils

from dateutil.relativedelta import relativedelta
from dateutil.rrule import *
from itertools import ifilter
import datetime
import logging
from avernus.objects.transaction import Transaction

logger = logging.getLogger(__name__)



def get_step_for_range(start,end):
    if start + relativedelta(months=+1) > end:
        #print "delta day"
        return relativedelta(days=1)
    if start + relativedelta(months=+10) > end:
        #print "delta week"
        return relativedelta(weeks=1)
    #print "delta month"
    return relativedelta(months=1)


def get_legend(smaller, bigger, step):
    erg = []
    if step == 'monthly':
        delta = relativedelta(months=+1)
        formatstring = "%b %y"
    elif step == 'yearly':
        delta = relativedelta(years=+1)
        formatstring = "%Y"
    elif step == 'daily':
        delta = relativedelta(days=+1)
        formatstring = "%x"
    elif step == 'weekly':
        delta = relativedelta(weeks=+1)
        formatstring = "%U"
    while smaller <= bigger:
        erg.append(smaller.strftime(formatstring))
        smaller+=delta
    return erg

def compute_start_date(dateItems):
    lowest = datetime.date.today()
    for item in dateItems:
        if item.date.date() < lowest:
            lowest = item.date.date()
    return lowest

def calculate_x_values(step, start, end):
        result = []
        current = start
        while current < end:
            result.append(current)
            current += step
        result.append(current)
        resultStrings = [gui_utils.get_date_string(x) for x in result]
        return result, resultStrings


class InvestmentChartController:

    def __init__(self, portfolio):
        self.items = portfolio.getTransactions() + portfolio.getDividends()
        self.start_date = compute_start_date(self.items)
        self.end_date = datetime.date.today()
        self.step = get_step_for_range(self.start_date, self.end_date)
        self.legend = get_legend(self.start_date, self.end_date, "monthly")

    def calculate_values(self):
        self.x_values_all, self.x_values = calculate_x_values(self.step, self.start_date, self.end_date)
        self.items = sorted(self.items, key=lambda t: t.date)
        self.y_values = {'invested capital': []}
        count = 0
        i = 0
        for current in self.x_values_all:
            while i < len(self.items) and self.items[i].date.date() < current:
                value = self.items[i].investmentValue
                count += value
                i += 1
            self.y_values['invested capital'].append(count)


class TransactionChartController:

    def get_step(self):
        return get_step_for_range(self.start_date, self.end_date)

    def get_start_date(self):
        return self.start_date



class TransactionValueOverTimeChartController(TransactionChartController):

    def __init__(self, transactions, date_range):
        self.monthly = False
        self.rolling_avg = False
        self.total_avg = False
        self.average_y = 0
        self.update(transactions, date_range)

    def get_start_date(self):
        if self.monthly:
            return datetime.date(self.start_date.year, self.start_date.month, 1)
        return self.start_date

    def get_step(self):
        if self.monthly:
            return relativedelta(months=1)
        return TransactionChartController.get_step(self)

    def set_monthly(self, monthly):
        self.monthly = monthly
        self.calculate_values()
        #print "Set monthly to ", monthly

    def set_rolling_average(self, avg):
        self.rolling_avg = avg
        self.calculate_values()

    def set_total_average(self, avg):
        self.total_avg = avg
        self.calculate_values()

    def update(self, transactions, date_range):
        self.transactions = sorted(transactions, key=lambda t: t.date)
        self.start_date, self.end_date = date_range

    def calculate_values(self):
        self.step = self.get_step()
        self.x_values_all, self.x_values = calculate_x_values(self.step, self.start_date, self.end_date)
        self.calculate_y_values()
        self.remove_zero()
        if self.rolling_avg:
            self.calculate_rolling_average()
        if self.total_avg:
            self.calculate_total_average()

    def remove_zero(self):
        # if the second is the same as the first or the last the same as the one before
        # only do it if we have more than 4
        if len(self.y_values['Transaction value'])>4:
            if (self.y_values['Transaction value'][0] == self.y_values['Transaction value'][1]):
                del self.y_values['Transaction value'][0]
                del self.x_values[0]
            if (self.y_values['Transaction value'][-1] == self.y_values['Transaction value'][-2]):
                del self.y_values['Transaction value'][-1]
                del self.x_values[-1]

    def calculate_y_values(self):
        self.y_values = {'Transaction value':[]}
        #FIXME do we need this temp dict?
        temp = {}
        i = 0
        x = self.x_values_all[i]
        temp[x] = 0
        for t in self.transactions:
            if t.date > x:
                i +=1
                x = self.x_values_all[i]
                temp[x] = temp[self.x_values_all[i-1]]
            temp[x] += t.amount
        if len(self.x_values_all) > len(temp):
            logger.debug("more x than y, defaulting to the value of the last")
            for x in self.x_values_all:
                if not x in temp:
                    logger.debug("X: " + str(x) +  " index " + str(self.x_values_all.index(x)))
                    temp[x] = temp[self.x_values_all[self.x_values_all.index(x)-1]]
        for x in self.x_values_all:
            value = x
            self.y_values['Transaction value'].append(temp[value])

    def calculate_total_average(self):
        self.average_y = sum(self.y_values['Transaction value']) / len(self.y_values['Transaction value'])
        self.y_values['Total average'] = [self.average_y for y in self.y_values['Transaction value']]

    def calculate_rolling_average(self):
        temp_values = []
        for y in self.y_values['Transaction value']:
            if len(temp_values) == 0:
                temp_values.append(y)
            else:
                temp_values.append((y+temp_values[-1])/2)
        self.y_values['Rolling average'] = temp_values


class TransactionStepValueChartController(TransactionValueOverTimeChartController):

    def calculate_y_values(self):
        self.y_values = {'Transaction value': []}
        temp = {}
        # initialize to zero
        for x in self.x_values_all:
            temp[x] = 0
        for t in self.transactions:
            # find the right slot for t
            i = 0
            while t.date >= self.x_values_all[i]:
                i += 1
            temp[self.x_values_all[i]] += t.amount
        # see if the first or last x is zero
        for x in self.x_values_all:
            self.y_values['Transaction value'].append(temp[x])

    def remove_zero(self):
        if self.y_values['Transaction value'][0] == 0:
            del self.y_values['Transaction value'][0]
            del self.x_values[0]
        if self.y_values['Transaction value'][-1] == 0:
            del self.y_values['Transaction value'][-1]
            del self.x_values[-1]


class EarningsVsSpendingsController():

    def __init__(self, transactions, date_range):
        self.update(transactions, date_range)

    def update(self, transactions, date_range):
        self.date_range = date_range
        self.transactions = transactions

    def calculate_values(self):
        start, end = self.date_range
        onemonth = relativedelta(months=1)
        data = {}
        self.x_values = []
        while start.year < end.year or (start.year == end.year and start.month <= end.month):
            if not start.year in data:
                data[start.year] = {}
            if not start.month in data[start.year]:
                data[start.year][start.month] = [0, 0]
            self.x_values.append(start)
            start += onemonth

        for trans in self.transactions:
            if trans.isEarning():
                data[trans.date.year][trans.date.month][0] += trans.amount
            else:
                data[trans.date.year][trans.date.month][1] += abs(trans.amount)
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value.year][x_value.month][0], data[x_value.year][x_value.month][1]])
        self.x_values = map(str, self.x_values)


class TransactionCategoryPieController():

    def __init__(self, transactions, earnings):
        self.earnings = earnings
        self.transactions = transactions

    def update(self, transactions, *args):
        self.transactions = transactions

    def calculate_values(self):
        data = {}
        for trans in ifilter(lambda t: t.isEarning() == self.earnings, self.transactions):
            try:
                data[str(trans.category)] += abs(trans.amount)
            except:
                data[str(trans.category)] = abs(trans.amount)
        self.values = data


class AccountBalanceOverTimeChartController(TransactionChartController):

    def __init__(self, account, date_range):
        self.account = account
        self.update(None, date_range)

    def update(self, transactions, date_range):
        self.start_date, self.end_date = date_range

    def calculate_values(self):
        self.step = self.get_step()
        self.x_values_all, self.x_values = calculate_x_values(self.get_step(), self.start_date, self.end_date)
        transactions = [t for t in self.account if t.date >= self.start_date]
        transactions.sort(key=lambda t: t.date, reverse=True)
        count = 1
        amount = self.account.amount
        trans_count = len(transactions)
        if trans_count == 0:
            self.y_values = {'Balance': [amount for x in self.x_values]}
            return
        iterator = transactions.__iter__()
        current_trans = iterator.next()

        y_values = []
        for current_date in reversed(self.x_values_all):
            while current_trans.date > current_date and count != trans_count:
                amount -= current_trans.amount
                current_trans = iterator.next()
                count += 1
            y_values.append(amount)
        y_values.reverse()
        self.y_values = {'Balance': y_values}


class DividendsPerYearChartController():

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def calculate_values(self):
        data = {}
        for year in date_utils.get_years(self.portfolio.birthday):
            data[str(year)] = 0.0
        for pos in self.portfolio:
            for div in pos.dividends:
                data[str(div.date.year)]+=div.total
        self.x_values = sorted(data.keys())
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value]])


class DividendsPerPositionChartController():

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def calculate_values(self):
        data = {}
        for pos in self.portfolio:
            for div in pos.dividends:
                try:
                    data[pos.name]+=div.total
                except:
                    data[pos.name]=div.total
        self.x_values = sorted(data.keys())
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value]])


class StockChartPlotController():

    def __init__(self, quotations):
        self.y_values = [d.close for d in quotations]
        quotation_count = len(quotations)
        self.x_values = [gui_utils.get_date_string(quotations[int(quotation_count/18 *i)].date) for i in range(18)]
        self.x_values.insert(0,str(quotations[0].date))
        self.x_values.insert(len(self.x_values),str(quotations[-1].date))


class PortfolioValueChartController():
    MAX_VALUES = 25

    def __init__(self, portfolio, step):
        self.portfolio = portfolio
        self.step = step

    def _calc_days(self):
        if self.step == 'daily':
            self.days = list(rrule(DAILY, dtstart = self.portfolio.birthday, until = datetime.date.today()))[-self.MAX_VALUES:]
        elif self.step == 'weekly':
            self.days = list(rrule(WEEKLY, dtstart = self.portfolio.birthday, until = datetime.date.today(), byweekday=FR))[-self.MAX_VALUES:]
        elif self.step == 'monthly':
            self.days = list(rrule(MONTHLY, dtstart = self.portfolio.birthday, until = datetime.date.today(), bymonthday=-1))[-self.MAX_VALUES:]
        elif self.step == 'yearly':
            self.days = list(rrule(YEARLY, dtstart = self.portfolio.birthday, until = datetime.date.today(), bymonthday=-1, bymonth=12))[-self.MAX_VALUES:]

    def calculate_values(self):
        #FIXME do more stuff here, less in portfolio
        self._calc_days()
        self.y_values = {'Portfolio value' : [self.portfolio.get_value_at_date(t) for t in self.days]}
        self.x_values = get_legend(self.days[0], self.days[-1], self.step)


class DimensionChartController():

    def __init__(self, portfolio, dimension):
        self.portfolio = portfolio
        self.dimension = dimension

    def calculate_values(self):
        data = {}
        for val in self.dimension.values:
            data[val.name] = 0
        for pos in self.portfolio:
            for adv in pos.stock.getAssetDimensionValue(self.dimension):
                data[adv.dimensionValue.name] += adv.value * pos.cvalue
        #remove unused dimvalues
        data = dict((k, v) for k, v in data.iteritems() if v != 0.0)
        if sum(data.values()) == 0:
            self.values = {' ':1}
        else:
            self.values = data


class PositionAttributeChartController():

    def __init__(self, portfolio, attribute):
        self.portfolio = portfolio
        self.attribute = attribute

    def calculate_values(self):
        data = {}
        for pos in self.portfolio:
            item = str(getattr(pos.stock, self.attribute))
            try:
                data[item] += pos.cvalue
            except:
                data[item] = pos.cvalue
        if sum(data.values()) == 0:
            self.values = {' ':1}
        else:
            self.values = data
