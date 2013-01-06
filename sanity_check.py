import os, sys, logging

from avernus import config
import sqlite3 as db

logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consolehandler = logging.StreamHandler()
consolehandler.setFormatter(formatter)
logger.addHandler(consolehandler)


# getting the database file
configs = config.avernusConfig()
default_file = os.path.join(config.config_path, 'avernus.db')
db_file = configs.get_option('database file', default=default_file)

#building the database connection
con = None
# tables that do not need a sanity check
omitted_tables = ['container', 'source_info']
# Reasons for omitting tables:
#    container: author does not know what could be checked (empty type??)
#    source_info: author does not know what this table stores
checked_tables = []
table_names = []
expected_tables = ['asset', 'quotation', 'stock', 'category_filter', 'source_info',
                   'dimension_value', 'fund', 'position']

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
    for table in omitted_tables:
        logger.debug('Table %s omitted on purpose' % table)
    for table in expected_tables:
        if not table in table_names:
            raise db.Error('No Table %s present' % table)
    # start with the sanity checks
    # asset: Every asset should have a source, currency and isin
    # TODO: Do the types have to be reflected in the type-tables?
    test_for_existing_attributes('asset', ['source','currency','isin'])
    checked_tables.append('asset')
    # quotation: the asset id has to be present 
    # TODO: The date sanity has to be checked as well
    logger.info('Sanity Check for quotation')
    cur.execute('SELECT * from quotation WHERE NOT EXISTS (select 1 from asset where quotation.asset_id = asset.id)')
    zombie_quotations = cur.fetchall()
    quotations_sane = True
    for zombie in zombie_quotations:
        logger.error('quotation %s referrs to a non-existant asset %s' % (zombie['id'], zombie['asset_id']))
        quotations_sane = False
    if quotations_sane:
        logger.info("Sanity Check for quotation passed")
    checked_tables.append('quotation')
    # stock: has to be an assert, i.e. the id has to be present in the table_entries
    logger.info("Sanity Check for stock")
    cur.execute('SELECT * from stock WHERE NOT EXISTS (select 1 from asset where stock.id = asset.id)')
    stock_sane = True
    for zombie in cur.fetchall():
        logger.error('stock %s referrs to a non-existant asset %s' % (zombie['id'], zombie['id']))
        stock_sane = False
    if stock_sane:
        logger.info('Sanity Check for stock passed')
    checked_tables.append('stock')
    # category_filter: the rule must not be empty and the category id must exist
    logger.info("Santiy Check for category_filter")
    category_filter_sane = True
    cur.execute('SELECT * from category_filter')
    for cf in cur.fetchall():
        if cf['rule'] == '':
            logger.error('category_filter %s has an empty rule' % cf['id'])
            category_filter_sane = False
    cur.execute('SELECT * from category_filter WHERE NOT EXISTS (select 1 from account_category where category_filter.category_id = account_category.id)')
    for zombie in cur.fetchall():
        logger.error('category_filter %s referrs to a non-existant category %s' % (cf['id'], cf['category_id']))
        category_filter_sane = False
    if category_filter_sane:
        logger.info('Sanity Check for category_filter passed')
    checked_tables.append('category_filter')
    # dimension_value: the dimension_id must exist
    logger.info('Sanity Check for dimension_value')
    dimension_value_sane = True
    cur.execute('SELECT * from dimension_value WHERE NOT EXISTS (select 1 from dimension where dimension_value.dimension_id = dimension.id)')
    for zombie in cur.fetchall():
        logger.error('dimension_value %s referrs to a non-existant dimension %s' % (zombie['id'], zombie['dimension_id']))
        dimension_value_sane = False
    if dimension_value_sane:
        logger.info('Sanity Check for dimension_value passed')
    checked_tables.append('dimension_value')
    # fund: the id has to be present
    logger.info('Sanify Check for fund')
    fund_sane = True
    cur.execute('SELECT * from fund WHERE NOT EXISTS (select 1 from asset where fund.id = asset.id)')
    for zombie in cur.fetchall():
        logger.error('fund %s referrs to a non-existant asset' % zombie['id'])
        fund_sane = False
    if fund_sane:
        logger.info('Sanity Check for fund passed')
    checked_tables.append('fund')
    # position: the asset_id has to exist
    logger.info('Sanity Check for position')
    position_sane = True
    cur.execute('SELECT * from position WHERE NOT EXISTS (select 1 from asset where position.asset_id = asset.id)')
    for zombie in cur.fetchall():
        position_sane = False
        logger.error('position %s referrs to a non-existant asset %s' % (zombie['id'], zombie['asset_id']))
    if position_sane:
        logger.info('Sanity Check for position passed')
    checked_tables.append('position')
        
except db.Error, e: 
    logger.error("Error %s" % e.args[0])
    sys.exit(1)
    
finally:
    for table in table_names:
        if not table in checked_tables and not table in omitted_tables:
            logger.info('Table %s was neither checked nor omitted on purpose.' % table)
    if con:
        con.close()
        logger.info("Connection closed")