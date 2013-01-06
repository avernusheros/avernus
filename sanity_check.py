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
        
def test_for_correct_reference(table, foreign_key, referenced_table):
    logger.info('Sanity Check (correct reference) for %s' % table)
    cur.execute('SELECT * from %s WHERE NOT EXISTS (select 1 from %s where %s = %s)' % 
                (table, referenced_table, table + '.' + foreign_key, referenced_table + '.id'))
    zombies = cur.fetchall()
    table_sane = True
    for zombie in zombies:
        logger.error('%s %s referrs to a non-existant %s %s' % 
                     (table, zombie['id'], referenced_table, zombie['asset_id']))
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
    test_for_correct_reference('quotation', 'asset_id', 'asset')
    checked_tables.append('quotation')
    # stock: has to be an assert, i.e. the id has to be present in the table_entries
    test_for_correct_reference('stock', 'id', 'asset')
    checked_tables.append('stock')
    # category_filter: the rule must not be empty and the category id must exist
    test_for_existing_attributes('category_filter', ['rule'])
    test_for_correct_reference('category_filter', 'category_id', 'account_category')
    checked_tables.append('category_filter')
    # dimension_value: the dimension_id must exist
    test_for_correct_reference('dimension_value', 'dimension_id', 'dimension')
    checked_tables.append('dimension_value')
    # fund: the id has to be present
    test_for_correct_reference('fund', 'id', 'asset')
    checked_tables.append('fund')
    # position: the asset_id has to exist
    test_for_correct_reference('position', 'asset_id', 'asset')
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