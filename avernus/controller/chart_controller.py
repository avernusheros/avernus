from avernus.gui import gui_utils
from avernus import date_utils
from avernus.controller import asset_controller
from avernus.controller import portfolio_controller
from avernus.controller import dimensions_controller
from avernus.controller import position_controller

from dateutil.relativedelta import relativedelta
from dateutil.rrule import *
from itertools import ifilter
import datetime
import sys
import logging

logger = logging.getLogger(__name__)


def get_step_for_range(start, end):
    if start + relativedelta(months= +1) > end:
        return relativedelta(days=1)
    if start + relativedelta(months= +10) > end:
        return relativedelta(weeks=1)
    return relativedelta(months=1)


def format_days(days, step):
    if step == "daily":
        return map(lambda d: gui_utils.get_date_string(d), days)
    elif step == 'monthly':
        formatstring = "%b %y"
    elif step == 'yearly':
        formatstring = "%Y"
    elif step == 'weekly':
        formatstring = "%U"
    return map(lambda d: d.strftime(formatstring), days)

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
        result.append(end)
        return result


class ChartController:

    def get_y_bounds(self):
        i = sys.maxint
        a = sys.maxint * (-1)
        for series in self.y_values.values():
            i = min(min(series), i)
            a = max(max(series), a)
        return (i, a)


class TransactionChartController(ChartController):

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
        #print "Set monthly to ", monthly

    def set_rolling_average(self, avg):
        self.rolling_avg = avg

    def set_total_average(self, avg):
        self.total_avg = avg

    def update(self, transactions, date_range):
        self.transactions = sorted(transactions, key=lambda t: t.date)
        self.start_date, self.end_date = date_range

    def calculate_values(self, *args):
        self.step = self.get_step()
        self.days = calculate_x_values(self.step, self.start_date, self.end_date)
        self.x_values = format_days(self.days, 'daily')
        self.calculate_y_values()
        self.remove_zero()
        if self.rolling_avg:
            self.calculate_rolling_average()
        if self.total_avg:
            self.calculate_total_average()
        yield 1

    def remove_zero(self):
        # if the second is the same as the first or the last the same as the one before
        # only do it if we have more than 4
        if len(self.y_values['Transaction value']) > 4:
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
        x = self.days[i]
        temp[x] = 0
        for t in self.transactions:
            if t.date > x:
                i += 1
                x = self.days[i]
                temp[x] = temp[self.days[i - 1]]
            temp[x] += t.amount
        if len(self.days) > len(temp):
            logger.debug("more x than y, defaulting to the value of the last")
            for x in self.days:
                if not x in temp:
                    logger.debug("X: " + str(x) + " index " + str(self.days.index(x)))
                    temp[x] = temp[self.days[self.days.index(x) - 1]]
        for x in self.days:
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
                temp_values.append((y + temp_values[-1]) / 2)
        self.y_values['Rolling average'] = temp_values


class TransactionStepValueChartController(TransactionValueOverTimeChartController):

    def calculate_y_values(self):
        self.y_values = {'Transaction value': []}
        temp = {}
        # initialize to zero
        for x in self.days:
            temp[x] = 0
        for t in self.transactions:
            # find the right slot for t
            i = 0
            while t.date >= self.days[i]:
                i += 1
            temp[self.days[i]] += t.amount
        # see if the first or last x is zero
        for x in self.days:
            self.y_values['Transaction value'].append(temp[x])

    def remove_zero(self):
        if self.y_values['Transaction value'][0] == 0:
            del self.y_values['Transaction value'][0]
            del self.x_values[0]
        if self.y_values['Transaction value'][-1] == 0:
            del self.y_values['Transaction value'][-1]
            del self.x_values[-1]


class EarningsVsSpendingsController(ChartController):

    def __init__(self, transactions, date_range):
        self.update(transactions, date_range)

    def update(self, transactions, date_range):
        self.date_range = date_range
        self.transactions = transactions

    def calculate_values(self, *args):
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
            if trans.amount >=0:
                data[trans.date.year][trans.date.month][0] += trans.amount
            else:
                data[trans.date.year][trans.date.month][1] += abs(trans.amount)
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value.year][x_value.month][0], data[x_value.year][x_value.month][1]])
        self.x_values = map(str, self.x_values)
        yield 1


class TransactionCategoryPieController(ChartController):

    def __init__(self, transactions, earnings):
        self.earnings = earnings
        self.transactions = transactions

    def update(self, transactions, *args):
        self.transactions = transactions

    def calculate_values(self, *args):
        data = {}
        for trans in ifilter(lambda t: t.amount>=0 == self.earnings, self.transactions):
            try:
                data[str(trans.category)] += abs(trans.amount)
            except:
                data[str(trans.category)] = abs(trans.amount)
        self.values = data
        yield 1


class AccountBalanceOverTimeChartController(TransactionChartController):

    def __init__(self, account, date_range):
        self.account = account
        self.update(None, date_range)

    def update(self, transactions, date_range):
        self.start_date, self.end_date = date_range

    def calculate_values(self, *args):
        self.step = self.get_step()
        self.days = calculate_x_values(self.get_step(), self.start_date, self.end_date)
        self.x_values = format_days(self.days, 'daily')
        transactions = [t for t in self.account if t.date >= self.start_date]
        transactions.sort(key=lambda t: t.date, reverse=True)
        count = 1
        balance = self.account.balance
        trans_count = len(transactions)
        if trans_count == 0:
            self.y_values = {'Balance': [balance for x in self.x_values]}
            return
        iterator = transactions.__iter__()
        current_trans = iterator.next()

        y_values = []
        for current_date in reversed(self.days):
            while current_trans.date > current_date and count != trans_count:
                balance -= current_trans.amount
                current_trans = iterator.next()
                count += 1
            y_values.append(balance)
        y_values.reverse()
        self.y_values = {'Balance': y_values}
        yield 1


class DividendsPerYearChartController(ChartController):

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def calculate_values(self, *args):
        data = {}
        for year in date_utils.get_years(portfolio_controller.get_birthday(self.portfolio)):
            data[str(year)] = 0.0
        for pos in self.portfolio:
            for div in pos.dividends:
                data[str(div.date.year)] += asset_controller.get_total_for_dividend(div)
        self.x_values = sorted(data.keys())
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value]])
        yield 1


class DividendsPerPositionChartController(ChartController):

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def calculate_values(self, *args):
        data = {}
        for pos in self.portfolio:
            for div in pos.dividends:
                try:
                    data[pos.name] += asset_controller.get_total_for_dividend(div)
                except:
                    data[pos.name] = asset_controller.get_total_for_dividend(div)
        self.x_values = sorted(data.keys())
        self.y_values = []
        for x_value in self.x_values:
            self.y_values.append([data[x_value]])
        yield 1


class StockChartPlotController(ChartController):
    #FIXME move code from plot.py here

    def __init__(self, quotations):
        self.y_values = [d.close for d in quotations]
        quotation_count = len(quotations)
        self.x_values = [gui_utils.get_date_string(quotations[int(quotation_count / 18 * i)].date) for i in range(18)]
        self.x_values.insert(0, str(quotations[0].date))
        self.x_values.insert(len(self.x_values), str(quotations[-1].date))

    def calculate_values(self, *args):
        yield 1


class PortfolioChartController(ChartController):

    MAX_VALUES = 25

    def __init__(self, portfolio, step):
        self.portfolio = portfolio
        self.birthday = portfolio_controller.get_birthday(portfolio)
        self.items = portfolio_controller.get_transactions(portfolio) + portfolio_controller.get_dividends(portfolio)
        self.step = step

    def _calc_days(self):
        if self.step == 'daily':
            days = list(rrule(DAILY, dtstart=self.birthday, until=datetime.date.today()))[-self.MAX_VALUES:]
        elif self.step == 'weekly':
            days = list(rrule(WEEKLY, dtstart=self.birthday, until=datetime.date.today(), byweekday=FR))[-self.MAX_VALUES:]
        elif self.step == 'monthly':
            days = list(rrule(MONTHLY, dtstart=self.birthday, until=datetime.date.today(), bymonthday= -1))[-self.MAX_VALUES:]
        elif self.step == 'yearly':
            days = list(rrule(YEARLY, dtstart=self.birthday, until=datetime.date.today(), bymonthday= -1, bymonth=12))[-self.MAX_VALUES:]
        self.days = [d.date() for d in days]

    def calculate_values(self, *args):
        self._calc_days()
        self.x_values = format_days(self.days, self.step)
        self.y_values = {}
        #FIXME do both things in parallel
        for foo in self.calculate_valueovertime('portfolio value'):
            yield foo
        for foo in self.calculate_investmentsovertime('invested capital'):
            yield foo

        for benchmark in portfolio_controller.get_benchmarks_for_portfolio(self.portfolio):
            self.calculate_benchmark(benchmark)
        yield 1

    def calculate_benchmark(self, benchmark):
        #FIXME why not per year?
        percent = benchmark.percentage
        values = [0.0] * len(self.days)
        daily = percent / len(self.days)
        values[0] = self.y_values['invested capital'][0]
        for i in range(1, len(values)):
            values[i] = values[i - 1] * (1 + daily) + self.y_values['invested capital'][i] - self.y_values['invested capital'][i - 1]
        key = 'Benchmark ' + str(int(percent * 100)) + '%'
        self.y_values[key] = values

    def calculate_valueovertime(self, name):
        self.y_values[name] = [0.0] * len(self.days)
        for pos in self.portfolio:
            for i in range(len(self.days)):
                self.y_values[name][i] += position_controller.get_value_at_date(pos, self.days[i])
                yield 0
        yield 1

    def update(self):
        self.calculate_values()

    def calculate_investmentsovertime(self, name):
        self.items = sorted(self.items, key=lambda t: t.date)
        self.y_values[name] = []
        count = 0
        i = 0
        for current in self.days:
            while i < len(self.items) and self.items[i].date < current:
                #FIXME two different total functions. maybe we can avoid the ugly if
                if self.items[i].__class__.__name__ == "Dividend":
                    count -= asset_controller.get_total_for_dividend(self.items[i])
                else:
                    count -= asset_controller.get_total_for_transaction(self.items[i])
                i += 1
            self.y_values[name].append(count)
        yield 1


class AllPortfolioValueOverTime(PortfolioChartController):

    def __init__(self, step):
        self.step = step
        self.birthday = min([pf.birthday for pf in portfolio_controller.getAllPortfolio()])

    def calculate_values(self, *args):
        self._calc_days()
        self.x_values = format_days(self.days, self.step)
        self.y_values = {}
        #FIXME do in parallel
        for pf in portfolio_controller.getAllPortfolio():
            self.portfolio = pf
            for foo in self.calculate_valueovertime(pf.name):
                yield foo
        yield 1


class AllPortfolioInvestmentsOverTime(PortfolioChartController):

    def __init__(self, step):
        self.step = step
        self.birthday = min([pf.birthday for pf in portfolio_controller.get_all_portfolio()])

    def calculate_values(self, *args):
        self._calc_days()
        self.x_values = format_days(self.days, self.step)
        self.y_values = {}
        #FIXME do in parallel
        for pf in portfolio_controller.get_all_portfolio():
            self.items = pf.getTransactions() + pf.getDividends()
            for foo in self.calculate_investmentsovertime(pf.name):
                yield foo
        yield 1


class DimensionChartController():

    def __init__(self, portfolio, dimension):
        self.portfolio = portfolio
        self.dimension = dimension

    def calculate_values(self, *args):
        data = {}
        for val in self.dimension.values:
            data[val.name] = 0
        for pos in self.portfolio:
            for adv in dimensions_controller.get_asset_dimension_value(pos.asset, self.dimension):
                data[adv.dimensionValue.name] += adv.value * position_controller.get_current_value(pos)
        #remove unused dimvalues
        data = dict((k, v) for k, v in data.iteritems() if v != 0.0)
        if sum(data.values()) == 0:
            self.values = {' ':1}
        else:
            self.values = data
        yield 1


class PositionAttributeChartController():

    def __init__(self, portfolio, attribute):
        self.portfolio = portfolio
        self.attribute = attribute

    def calculate_values(self, *args):
        data = {}
        for pos in self.portfolio:
            if pos.quantity == 0.0:
                continue
            item = str(getattr(pos.asset, self.attribute))
            try:
                data[item] += position_controller.get_current_value(pos)
            except:
                data[item] = position_controller.get_current_value(pos)
        if sum(data.values()) == 0:
            self.values = {' ':1}
        else:
            self.values = data
        yield 1



class PortfolioAttributeChartController():

    def __init__(self, attribute):
        self.attribute = attribute
        self.values = {}

    def calculate_values(self, *args):
        portfolios = portfolio_controller.getAllPortfolio()
        data = {}
        for pf in portfolios:
            item = str(getattr(pf, self.attribute))
            try:
                data[item] += portfolio_controller.get_current_value(pf)
            except:
                data[item] = portfolio_controller.get_current_value(pf)
        if sum(data.values()) == 0:
            self.values = {' ':1}
        else:
            self.values = data
        yield 1
