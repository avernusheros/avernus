import os, sys, logging 

from avernus import config
import sqlite3 as db
import optparse

logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consolehandler = logging.StreamHandler()
consolehandler.setFormatter(formatter)
logger.addHandler(consolehandler)

version = '1'

parser = optparse.OptionParser(version='%prog ' + version)
parser.add_option("-f", "--file", dest="datafile", help="set database file")
(options, args) = parser.parse_args()
db_file = options.datafile
if db_file == None:
# getting the database file
    configs = config.avernusConfig()
    default_file = os.path.join(config.config_path, 'avernus.db')
    db_file = configs.get_option('database file', default=default_file)

#building the database connection
con = None
# tables that do not need a sanity check
omitted_tables = ['container', 'source_info', 'account_category', 'asset_category',
                  'meta', 'dimension']
# Reasons for omitting tables:
#    container: author does not know what could be checked (empty type??)
#    source_info: author does not know what this table stores
#    account_category: check does not fit standard functions

### TODO: More complex checks
# account category parents have to exist
# each portfolio transaction has to either be a buy or a sell
# assetcategory parents have to exist
# each container has to be one of the types
# each asset has to be one of the types

# as this 'each' foo has to be one of the 'bars' is common, there should be a function too
table_names = []
expected_tables = ['asset', 'quotation', 'category_filter', 'source_info',
                   'dimension_value', 'fund', 'position', 'asset_category', 
                   'account_category', 'meta', 'dimension', 'container', 'account',
                   'benchmark', 'asset_dimension_value', 'dividend', 'watchlist_position',
                   'portfolio_position', 'account_transaction', 'portfolio_transaction',
                   'portfolio_sell_transaction', 'portfolio_buy_transaction','watchlist',
                   'portfolio', 'etf']

def test_for_existing_attributes(table, columns):
    logger.info("Sanity Check (existing attribute) for %s" % table)
    cur.execute('SELECT * FROM %s' % table)
    table_entries = cur.fetchall()
    table_sane = True
    for key in columns:
        for asset in table_entries:
            if asset[key] == '':
                table_sane = False
                logger.error('Missing %s on %s %s' %(key, table, asset['id']))
    if table_sane:
        logger.info("Sanity Check (existing attribute) for %s passed" % table)
        
def test_for_correct_reference(table, foreign_key, referenced_table):
    logger.info('Sanity Check (correct reference) for %s' % table)
    cur.execute('SELECT * from %s WHERE NOT EXISTS (select 1 from %s where %s = %s)' % 
                (table, referenced_table, table + '.' + foreign_key, referenced_table + '.id'))
    zombies = cur.fetchall()
    table_sane = True
    for zombie in zombies:
        logger.error('%s %s referrs to a non-existant %s' % 
                     (table, zombie['id'], referenced_table))
        table_sane = False
    if table_sane:
        logger.info("Sanity Check (correct reference) for %s passed" % table)
    
try:
    con = db.connect(db_file)
    con.row_factory = db.Row
    logger.info("Connection established %s" % con)
    cur = con.cursor()
    cur.execute('SELECT SQLITE_VERSION()')
    data = cur.fetchone()
    logger.debug("SQLite Version: %s" % data['SQLITE_VERSION()'])
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    for table in tables:
        table_names.append(table['name'])
    logger.info("Table names %s" %table_names)
    logger.info('Tables omitted on purpose: %s' % omitted_tables)
    for table in expected_tables:
        if not table in table_names:
            raise db.Error('No Table %s present' % table)
    logger.info('All expected tables are present')
    if len(table_names) > len(expected_tables):
        logger.error('There are unexpected tables in the database')
    else:
        logger.info('No unexpected tables were found in the database')
    # start with the sanity checks
    # asset: Every asset should have a source, currency and isin
    # TODO: Do the types have to be reflected in the type-tables?
    test_for_existing_attributes('asset', ['source','currency','isin'])
    # quotation: the asset id has to be present 
    # TODO: The date sanity has to be checked as well
    test_for_correct_reference('quotation', 'asset_id', 'asset')
    # category_filter: the rule must not be empty and the category id must exist
    test_for_existing_attributes('category_filter', ['rule'])
    test_for_correct_reference('category_filter', 'category_id', 'account_category')
    # dimension_value: the dimension_id must exist
    test_for_correct_reference('dimension_value', 'dimension_id', 'dimension')
    # fund: the id has to be present
    test_for_correct_reference('fund', 'id', 'asset')
    # position: the asset_id has to exist
    test_for_correct_reference('position', 'asset_id', 'asset')
    # account: should have a name and a type
    test_for_existing_attributes('category_filter', ['rule'])
    # benchmark: portfolio_id must exist
    test_for_correct_reference('benchmark', 'portfolio_id', 'portfolio')
    # asset_dimension_value: asset_id must exist
    test_for_correct_reference('asset_dimension_value', 'asset_id', 'asset')
    # dividend: position_id must exist
    test_for_correct_reference('dividend', 'position_id', 'position')
    # watchlist_position: watchlist_id must exist
    test_for_correct_reference('watchlist_position', 'watchlist_id', 'watchlist')
    # portfolio_position: portfolio_id must exist
    test_for_correct_reference('portfolio_position', 'portfolio_id', 'portfolio')
    # account_transaction: account_id must exist, description, amount and date have to be
    test_for_existing_attributes('account_transaction', ['description','amount','date'])
    test_for_correct_reference('account_transaction', 'account_id', 'account')
    # portfolio_transaction: position_id must exist, type, date, quantity and price have to be
    test_for_existing_attributes('portfolio_transaction', ['type','date','quantity','price'])
    test_for_correct_reference('portfolio_transaction', 'position_id', 'position')
    # portfolio_sell_transaction: id has to exist
    test_for_correct_reference('portfolio_sell_transaction', 'id', 'portfolio_transaction')
    # portfolio_buy_transaction: id has to exist
    test_for_correct_reference('portfolio_buy_transaction', 'id', 'portfolio_transaction')
    # watchlist: id has to exist
    test_for_correct_reference('watchlist', 'id', 'container')
    # portfolio: id has to exist
    test_for_correct_reference('portfolio', 'id', 'container')
    # etf: id has to exist
    test_for_correct_reference('etf', 'id', 'asset')
        
except db.Error, e: 
    logger.critical("Fatal Error %s" % e.args[0])
    sys.exit(1)
    
finally:
    if con:
        con.close()
        logger.info("Connection closed")