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
omitted_tables = ['container']
checked_tables = []
table_names = []
expected_tables = ['asset', 'quotation']
    
try:
    con = db.connect(db_file)
    con.row_factory = db.Row
    logger.info("Connection established %s" % con)
    cur = con.cursor()
    cur.execute('SELECT SQLITE_VERSION()')
    data = cur.fetchone()
    logger.debug("SQLite Version: %s" % data)
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
    logger.info("Sanity Check for asset")
    cur.execute('SELECT * FROM asset')
    assets = cur.fetchall()
    assets_sane = True
    for key in ['isin','currency','source']:
        for asset in assets:
            if asset[key] == '':
                assets_sane = False
                logger.error('Missing %s on asset id %s' %(key, asset['id']))
    if assets_sane:
        logger.info("Sanity Check for asset passed")
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
    checked_tables.append('asset')
        
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