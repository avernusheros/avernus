#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import sys
import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
import optparse
import logging

# Add project root directory (enable symlink, and trunk execution).
PROJECT_ROOT_DIRECTORY = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))

b_from_source = False
python_path = []
if os.path.abspath(__file__).startswith('/opt'):
    syspath = sys.path[:] # copy to avoid infinite loop in pending objects
    for path in syspath:
        opt_path = path.replace('/usr', '/opt/extras.ubuntu.com/avernus')
        python_path.insert(0, opt_path)
        sys.path.insert(0, opt_path)
if (os.path.exists(os.path.join(PROJECT_ROOT_DIRECTORY, 'avernus'))
    and PROJECT_ROOT_DIRECTORY not in sys.path):
    b_from_source = True
if python_path:
    os.putenv('PYTHONPATH', "%s:%s" % (os.getenv('PYTHONPATH', ''), ':'.join(python_path))) # for subprocesses    os.putenv('PYTHONPATH', PROJECT_ROOT_DIRECTORY) # for subprocesses

import avernus
from avernus import config
from avernus.gui import threads

if b_from_source:
    config.__avernus_data_directory__ = '../data/'


def init_logger(debug=False):
    if debug:
        loggerlevel = logging.DEBUG
    else:
        loggerlevel = logging.INFO

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    rootlogger = logging.getLogger()
    rootlogger.setLevel(loggerlevel)

    # logging to terminal
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    rootlogger.addHandler(consolehandler)

    # logging to file
    filehandler = logging.FileHandler(filename='avernus.log')
    filehandler.setFormatter(formatter)
    rootlogger.addHandler(filehandler)


def init_translations():
    import locale
    #locale.setlocale(locale.LC_ALL, '')
    import gettext
    from os.path import pardir, abspath, dirname, join

    GETTEXT_DOMAIN = 'avernus'
    LOCALE_PATH = abspath(join(dirname(__file__), pardir, 'locales'))
    if not os.path.isdir(LOCALE_PATH):
        LOCALE_PATH = '/usr/share/locale'

    # setup translation
    languages_used = []

    lc, encoding = locale.getdefaultlocale()
    if lc:
        languages_used = [lc]
    lang_in_env = os.environ.get('LANGUAGE', None)
    if lang_in_env:
        languages_used.extend(lang_in_env.split())

    gettext.bindtextdomain(GETTEXT_DOMAIN, LOCALE_PATH)
    gettext.textdomain(GETTEXT_DOMAIN)
    translation = gettext.translation(GETTEXT_DOMAIN, LOCALE_PATH,
                                      languages=languages_used,
                                      fallback=True)
    import __builtin__
    __builtin__._ = translation.gettext

def init_icons():
    from avernus.gui.icons import IconManager
    icons = IconManager()

    path = os.path.join(config.getdatapath(), 'images')
    iconNames = [
    'avernus', 'tags', 'tag', 'watchlists', 'watchlist', 'portfolio',
    'portfolios', 'index', 'indices', 'arrow_down', 'arrow_med_down',
    'arrow_up', 'arrow_med_up', 'arrow_right', 'A', 'F', 'fund', 'stock',
    'etf', 'accounts', 'account', 'onvista', 'yahoo'
    ]
    for name in iconNames:
        icons.add_icon_name_from_directory(name, path)
    Gtk.Window.set_default_icon_name('avernus')


#MAIN
try:
    init_translations()
    # Support for command line options.
    parser = optparse.OptionParser(version='%prog ' + avernus.__version__)
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help=_("enable debug output"))
    parser.add_option("-f", "--file", dest="datafile", help="set database file")
    (options, args) = parser.parse_args()

    init_logger(options.debug)
    init_icons()
    db_file = options.datafile
    if db_file == None:
        configs = config.avernusConfig()
        default_file = os.path.join(config.config_path, 'avernus.db')
        db_file = configs.get_option('database file', default=default_file)

    from avernus.objects import set_db, connect
    set_db(db_file)
    connect(True)

    GObject.threads_init()

    from avernus.controller import asset_controller

    from avernus.gui.mainwindow import MainWindow
    from avernus.datasource_manager import DatasourceManager
    dsm = DatasourceManager()
    main_window = MainWindow()
    asset_controller.datasource_manager = dsm
    try:
        Gtk.main()
    except Exception as e:
        main_window.on_destroy()
        raise
except Exception as e:
    print "crashed, abgekachelt ... !!"
    import traceback
    traceback.print_exc()
    avernus.objects.session.commit()
    avernus.objects.Session.close_all()
    threads.terminate_all()
    print "wie gesagt ... abgekachelt ..."
    exit(1)


#FIXME fix or remove the network manager code
#from avernus.network_manager import DBusNetwork
#DBusNetwork()



