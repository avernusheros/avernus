#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from avernus.objects import account, container, dimension
import datetime
import sqlite3


def to_twelve(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    for row in c.execute('SELECT id, last_update from container').fetchall():
        if row[1]:
            temp = row[1].split("-")
            temp = map(int, temp)
            temp = datetime.date(temp[0], temp[1], temp[2])
            c.execute('UPDATE container SET last_update = ? WHERE id = ?', (datetime.datetime.combine(temp, datetime.time()), row[0]))
    conn.commit()
    c.close()


def to_eleven(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS portfolio_buy_transaction (id INTEGER NOT NULL, PRIMARY KEY(id), FOREIGN KEY(id) REFERENCES portfolio_transaction(id))')
    c.execute('CREATE TABLE IF NOT EXISTS portfolio_sell_transaction (id INTEGER NOT NULL, PRIMARY KEY(id), FOREIGN KEY(id) REFERENCES portfolio_transaction(id))')

    for row in c.execute('SELECT id, type from portfolio_transaction').fetchall():
        if row[1] == 1:
            print "BUY"
            c.execute('INSERT INTO portfolio_buy_transaction VALUES (?)', (row[0],))
            c.execute('UPDATE portfolio_transaction SET type = "portfolio_buy_transaction" WHERE id = ?', (row[0],))
        else:
            c.execute('INSERT INTO portfolio_sell_transaction VALUES (?)', (row[0],))
            c.execute('UPDATE portfolio_transaction SET type = "portfolio_sell_transaction" WHERE id = ?', (row[0],))

    conn.commit()
    c.close()


def to_ten(database, old_db):
    conn_old = sqlite3.connect(old_db)
    conn_new = sqlite3.connect(database)
    c_old = conn_old.cursor()
    c_new = conn_new.cursor()

    # portfolios
    for row in c_old.execute('SELECT id, name from portfolio').fetchall():
        old_id = row[0]
        c_new.execute("INSERT INTO container (name, type) VALUES (?, 'portfolio')", (row[1],))
        new_id = c_new.lastrowid
        c_new.execute("INSERT INTO portfolio VALUES (?)", (new_id,))

        # positions
        for row in c_old.execute('SELECT id, comment, price,date, quantity, stock from portfolioposition WHERE portfolio=?', (old_id,)).fetchall():
            old_pos = row[0]
            c_new.execute("INSERT INTO position (type, date, price, comment, asset_id) VALUES ('portfolioposition', ?,?,?,?)", (row[3], row[2], row[1], row[5]))
            new_pos = c_new.lastrowid
            c_new.execute("INSERT INTO portfolio_position (id, quantity, portfolio_id) VALUES (?,?,?)", (new_pos, row[4], new_id))

            # transactions
            for row in c_old.execute('SELECT id, costs, date, price, type, quantity from trans WHERE position=?', (old_pos,)).fetchall():
                c_new.execute("INSERT INTO portfolio_transaction (type, date, price, cost, quantity, position_id ) VALUES (?,?,?,?,?,?)", (row[4], row[2], row[3], row[1], row[5], new_pos))

            # dividends
            for row in c_old.execute('SELECT costs, date, price from dividend WHERE position=?', (old_pos,)).fetchall():
                c_new.execute("INSERT INTO dividend (date, price, cost, position_id ) VALUES (?,?,?,?)", (row[1], row[2], row[0], new_pos))

        # benchmarks
        for row in c_old.execute('SELECT percentage from portfolioBenchmarks WHERE portfolio=?', (old_id,)).fetchall():
            c_new.execute("INSERT INTO benchmark (portfolio_id, percentage) VALUES (?,?)", (new_id, row[0]))

    # watchlists
    for row in c_old.execute('SELECT id, name from watchlist'):
        old_id = row[0]
        c_new.execute("INSERT INTO container (name, type) VALUES (?, 'watchlist')", (row[1],))
        new_id = c_new.lastrowid
        c_new.execute("INSERT INTO watchlist VALUES (?)", (new_id,))

        # positions
        for row in c_old.execute('SELECT id, comment, price,date, stock from watchlistposition WHERE watchlist=?', (old_id,)).fetchall():
            old_pos = row[0]
            c_new.execute("INSERT INTO position (type, date, price, comment, asset_id) VALUES ('watchlistposition', ?,?,?,?)", (row[3], row[2], row[1], row[4]))
            new_pos = c_new.lastrowid
            c_new.execute("INSERT INTO watchlist_position (id, watchlist_id) VALUES (?,?)", (new_pos, new_id))

    # stocks
    stockdate = datetime.datetime.now() - datetime.timedelta(days=365)
    for row in c_old.execute('SELECT id, currency, name, source, isin, type, ter from stock').fetchall():
        if row[5] == 0:
            assettype = 'fund'
        elif row[5] == 1:
            assettype = 'stock'
        elif row[5] == 2:
            assettype = 'etf'
        elif row[5] == 3:
            assettype = 'bond'
        c_new.execute("INSERT INTO asset (id, name, isin, currency, source, price, change, exchange, type, date) VALUES (?,?,?,?,?,1.0, 0.0, '',?,?)", (row[0], row [2], row[4], row[1], row[3], assettype, stockdate))
        if assettype == 'etf' or assettype == 'fund':
            c_new.execute("INSERT INTO " + assettype + " VALUES (?, ?)", (row[0], row[6]))
        else:
            c_new.execute("INSERT INTO " + assettype + " (id) VALUES (?)", (row[0],))

    # quotations
    for row in c_old.execute('SELECT high, low, volume, exchange, date, close, open, stock from quotation').fetchall():
        c_new.execute("INSERT INTO quotation (high, low, volume, exchange, date, close, open, asset_id) VALUES (?,?,?,?,?,?,?,?)", row)

    # dimension
    for row in c_old.execute('SELECT id, name from dimension').fetchall():
        c_new.execute("INSERT INTO dimension (id, name) VALUES (?,?)", (row[0], row[1]))

    # dimension value
    for row in c_old.execute('SELECT id, name, dimension from dimensionValue').fetchall():
        c_new.execute("INSERT INTO dimension_value (id, name, dimension_id) VALUES (?,?,?)", (row[0], row[1], row[2]))

    # asset dimension value
    for row in c_old.execute('SELECT dimensionValue, value, stock from AssetDimensionValue').fetchall():
        c_new.execute("INSERT INTO asset_dimension_value (value, dimension_value_id, asset_id) VALUES (?,?,?)", (row[1], row[0], row[2]))


    # source info
    for row in c_old.execute('SELECT info, source, stock from sourceinfo').fetchall():
        c_new.execute("INSERT INTO source_info (source, info, asset_id) VALUES (?,?,?)", (row[1], row[0], row[2]))

    # accounts
    for row in c_old.execute('SELECT id, name, amount from account').fetchall():
        c_new.execute("INSERT INTO account (name, type, balance, id) VALUES (?, 1, ?, ?)", (row[1], row[2], row[0]))

    # account transactions
    for row in c_old.execute('SELECT id, category, account, description, transferid, amount, date from accounttransaction').fetchall():
        c_new.execute("INSERT INTO account_transaction (id, description, amount, date, account_id, transfer_id, category_id) VALUES (?, ?,?,?,?,?,?)", (row[0], row[3], row[5], row[6], row[2], row[4], row[1]))

    # categories
    for row in c_old.execute('SELECT parentid, id, name from accountcategory').fetchall():
        if row[0] == -1:
            parent = None
        else:
            parent = row[0]
        c_new.execute("INSERT INTO account_category (id, parent_id, name) VALUES (?, ?, ?)", (row[1], parent, row[2]))

    # transaction filter
    for row in c_old.execute('SELECT id, active, priority, category, rule from transactionFilter').fetchall():
        c_new.execute("INSERT INTO category_filter (rule, active, priority, category_id) VALUES (?, ?, ?, ?)", (row[4], row[1], row[2], row[3]))

    conn_new.commit()
    c_new.close()
    c_old.close()


def load_sample_data(session):
    DIMENSIONS = {_('Region'): [_('Emerging markets'), _('America'), _('Europe'), _('Pacific')],
              _('Asset Class'): [_('Bond'), _('Stocks developed countries'), _('Commodities')],
              _('Risk'): [_('high'), _('medium'), _('low')],
              _('Currency'): [_('Euro'), _('Dollar'), _('Yen')],
              _('Company Size'): [_('large'), _('medium'), _('small')],
              _('Sector'): ['Basic Materials', 'Conglomerates', 'Consumer Goods', 'Energy', 'Financial', 'Healthcare', 'Industrial Goods', 'Services', 'Technology', 'Transportation', 'Utilities']
              }
    CATEGORIES = {
        _('Utilities'): [_('Gas'), _('Phone'), _('Water'), _('Electricity')],
        _('Entertainment'): [_('Books'), _('Movies'), _('Music'), _('Amusement')],
        _('Fees'):[],
        _('Gifts'):[],
        _('Health care'): [_('Doctor'), _('Pharmacy'), _('Health insurance')],
        _('Food'): [_('Groceries'), _('Restaurants'), _('Coffee')],
        _('Transport'): [_('Car'), _('Train'), _('Fuel')],
        _('Services'): [_('Shipping')],
        _('Home'): [_('Rent'), _('Home improvements')],
        _('Personal care'): [],
        _('Taxes'): [],
        _('Income'): [],
        _('Shopping'): [_('Clothes'), _('Electronics'), _('Hobbies'), _('Sporting Goods')],
        _('Travel'): [_('Lodging'), _('Transportation')]
    }

    for dim, vals in DIMENSIONS.iteritems():
        new_dim = dimension.Dimension(name=dim)
        for val in vals:
            dimension.DimensionValue(dimension=new_dim, name=val)
    for cat, subcats in CATEGORIES.iteritems():
        parent = account.AccountCategory(name=cat)
        for subcat in subcats:
            account.AccountCategory(name=subcat, parent=parent)
    acc = account.Account(name=_('sample account'), balance=100.0)
    account.AccountTransaction(account=acc, description='this is a sample transaction', amount=99.99, date=datetime.date.today())
    account.AccountTransaction(account=acc, description='another sample transaction', amount= -33.90, date=datetime.date.today())
    container.Portfolio(name=_('sample portfolio'))
    container.Watchlist(name=_('sample watchlist'))
