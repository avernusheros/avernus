from avernus import date_utils
from avernus.gui import gui_utils
from avernus.objects import container
from dateutil.relativedelta import relativedelta
from dateutil.rrule import WEEKLY, rrule, FR
from itertools import ifilter
import calendar
import datetime
import logging
import sys


logger = logging.getLogger(__name__)


def get_step_for_range(start, end):
    if start + relativedelta(months=1) > end:
        return relativedelta(days=1)
    if start + relativedelta(months=10) > end:
        return relativedelta(weeks=1)
    return relativedelta(months=1)


def calc_days(step, start, end, max_values=None):
    if step == 'daily':
        days = [start + datetime.timedelta(n) for n in range(int ((end - start).days))]
    elif step == 'weekly':
        days = list(rrule(WEEKLY, dtstart=start, until=end, byweekday=FR))
    elif step == 'monthly':
        days = []
        ym_start = 12 * start.year + start.month - 1
        ym_end = 12 * end.year + end.month
        for ym in range(ym_start, ym_end):
            y, m = divmod(ym, 12)
            days.append(datetime.date(y, m + 1, calendar.monthrange(y, m + 1)[1]))
    elif step == 'yearly':
        days = []
        for y in range(start.year, end.year):
            days.append(datetime.date(y, 12, 31))
    if max_values is not None and len(days) > max_values:
        return days[-max_values:]
    return days


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
        return i, a


class TransactionValueChartController(ChartController):

    def __init__(self, transactions, step="monthly"):
        self.step = step
        self.rolling_avg = False
        self.total_avg = False
        self.average_y = 0.0
        self.update(transactions)
        self.name = _('Transaction value')

    def set_step(self, step):
        self.step = step

    def set_rolling_average(self, avg):
        self.rolling_avg = avg

    def set_total_average(self, avg):
        self.total_avg = avg

    def update(self, transactions, *args):
        self.transactions = sorted(transactions, key=lambda t: t.date)

    def calculate_values(self, *args):
        if not self.transactions:
            return
        self.y_values = []
        self.days = calc_days(self.step, self.transactions[0].date, self.transactions[-1].date, 25)
        self.x_values = format_days(self.days, self.step)
        self.calculate_y_values()
        if self.rolling_avg:
            self.calculate_rolling_average()
        if self.total_avg:
            self.calculate_total_average()
        yield 1

    def calculate_y_values(self):
        # transactions need to be sorted by date
        t = 1
        current_day = self.days[t]
        earnings = [0.0] * len(self.days)
        spendings = [0.0] * len(self.days)
        for transaction in self.transactions:
            # skip transaction out of desired range
            if transaction.date <= self.days[0]:
                continue
            while transaction.date > current_day:
                t += 1
                current_day = self.days[t]
            if transaction.amount < 0:
                spendings[t] += transaction.amount
            else:
                earnings[t] += transaction.amount
        self.y_values = [(_('Earnings'), earnings), (_('Spendings'), spendings)]

    def calculate_total_average(self):
        self.average_y = sum(self.y_values[self.name]) / len(self.y_values[self.name])
        self.y_values[_('Total average')] = [self.average_y for y in self.y_values[self.name]]

    def calculate_rolling_average(self):
        temp_values = []
        for y in self.y_values[self.name]:
            if len(temp_values) == 0:
                temp_values.append(y)
            else:
                temp_values.append((y + temp_values[-1]) / 2)
        self.y_values[_('Rolling average')] = temp_values


class TransactionCategoryPieController(ChartController):

    def __init__(self, transactions, earnings):
        self.transactions = transactions
        if earnings:
            self.transactions_filter = lambda x: x.amount >= 0
        else:
            self.transactions_filter = lambda x: x.amount < 0

    def update(self, transactions, *args):
        self.transactions = transactions

    def calculate_values(self, *args):
        data = {}
        for trans in ifilter(self.transactions_filter, self.transactions):
            try:
                data[str(trans.category)] += abs(trans.amount)
            except:
                data[str(trans.category)] = abs(trans.amount)
        self.values = data
        yield 1


class AccountBalanceController(ChartController):

    def __init__(self, account, date_range, step="monthly"):
        self.account = account
        self.step = step
        self.update(None, date_range)

    def update(self, transactions, date_range):
        if transactions:
            self.account = transactions[0].account
        self.start_date, self.end_date = date_range
        if not self.end_date:
            self.end_date = datetime.date.today()
        if not self.start_date:
            self.start_date = self.account.birthday

    def calculate_values(self, *args):
        self.days = calc_days(self.step, self.start_date, self.end_date)
        self.x_values = format_days(self.days, self.step)

        transactions = [t for t in self.account if t.date >= self.start_date]
        transactions.sort(key=lambda t: t.date, reverse=True)
        count = 1
        balance = self.account.balance
        trans_count = len(transactions)
        if trans_count == 0:
            self.y_values = [balance] * len(self.days)
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
        self.y_values = [('Balance', y_values)]
        yield 1


class DividendsPerYearChartController(ChartController):

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def calculate_values(self, *args):
        data = {}
        for year in date_utils.get_years(self.portfolio.get_birthday()):
            data[str(year)] = 0.0
        for pos in self.portfolio:
            for div in pos.dividends:
                data[str(div.date.year)] += div.total
        self.x_values = sorted(data.keys())
        self.y_values = [(_('Dividends'), [data[x_value] for x_value in self.x_values])]
        yield 1


class DividendsPerPositionChartController(ChartController):

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def calculate_values(self, *args):
        data = {}
        for pos in self.portfolio:
            for div in pos.dividends:
                try:
                    data[pos.asset.name] += div.total
                except:
                    data[pos.asset.name] = div.total
        self.x_values = sorted(data.keys())
        self.y_values = [(_('Dividends'), [data[x_value] for x_value in self.x_values])]
        yield 1


class StockChartPlotController(ChartController):
    # FIXME move code from plot.py here

    def __init__(self, quotations):
        self.y_values = [(_("close"), [d.close for d in quotations])]
        quotation_count = len(quotations)
        self.x_values = [gui_utils.get_date_string(q.date) for q in quotations]

    def calculate_values(self, *args):
        yield 1


class PortfolioChartController(ChartController):

    MAX_VALUES = 25

    def __init__(self, portfolio, step):
        self.portfolio = portfolio
        self.birthday = portfolio.get_birthday()
        self.items = portfolio.get_transactions() + portfolio.get_dividends()
        self.step = step
        self.name_invested = _('invested capital')
        self.name_value = _('portfolio value')

    def calculate_values(self, *args):
        self.days = calc_days(self.step, self.birthday, datetime.date.today(), self.MAX_VALUES)
        self.x_values = format_days(self.days, self.step)
        self.y_values = []
        # FIXME do both things in parallel
        for foo in self.calculate_valueovertime(self.name_value):
            yield foo
        for foo in self.calculate_investmentsovertime(self.name_invested):
            yield foo

    def calculate_valueovertime(self, name):
        # import time
        # t0 = time.clock()
        temp = [0.0] * len(self.days)
        for asset in self.portfolio.get_used_assets():
            i = 0
            for val in self.portfolio.get_value_at_daterange(asset, self.days):
                temp[i] += val
                i += 1
                yield 0
        # print "!!!!", time.clock()-t0, "seconds"
        self.y_values.append((name, temp))
        yield 1

    def update(self):
        self.calculate_values()

    def calculate_investmentsovertime(self, name):
        self.items = sorted(self.items, key=lambda t: t.date)
        temp = []
        count = 0
        i = 0
        for current in self.days:
            while i < len(self.items) and self.items[i].date < current:
                count -= self.items[i].total
                i += 1
            temp.append(count)
        self.y_values.append((name, temp))
        yield 1


class AllPortfolioValueOverTime(PortfolioChartController):

    def __init__(self, step):
        self.step = step
        self.birthday = min([pf.get_birthday() for pf in container.get_all_portfolios()])

    def calculate_values(self, *args):
        self.days = calc_days(self.step, self.birthday, datetime.date.today(), self.MAX_VALUES)
        self.x_values = format_days(self.days, self.step)
        self.y_values = []
        # FIXME do in parallel
        for pf in container.get_all_portfolios():
            self.portfolio = pf
            for foo in self.calculate_valueovertime(pf.name):
                yield foo
        yield 1


class AllPortfolioInvestmentsOverTime(PortfolioChartController):

    def __init__(self, step):
        self.step = step
        self.birthday = min([pf.get_birthday() for pf in container.get_all_portfolios()])

    def calculate_values(self, *args):
        self.days = calc_days(self.step, self.birthday, datetime.date.today(), self.MAX_VALUES)
        self.x_values = format_days(self.days, self.step)
        self.y_values = []
        # FIXME do in parallel
        for pf in container.get_all_portfolios():
            self.items = pf.get_transactions() + pf.get_dividends()
            for foo in self.calculate_investmentsovertime(pf.name):
                yield foo
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
                data[item] += pos.current_value
            except:
                data[item] = pos.current_value
        if sum(data.values()) == 0:
            self.values = {' ': 1}
        else:
            self.values = data
        yield 1


class PortfolioAttributeChartController():

    def __init__(self, attribute):
        self.attribute = attribute
        self.values = {}

    def calculate_values(self, *args):
        portfolios = container.get_all_portfolios()
        data = {}
        for pf in portfolios:
            item = str(getattr(pf, self.attribute))
            try:
                data[item] += pf.get_current_value()
            except:
                data[item] = pf.get_current_value()
        if sum(data.values()) == 0:
            self.values = {' ': 1}
        else:
            self.values = data
        yield 1
