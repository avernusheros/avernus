#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import sys
import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
import optparse
import logging

PROJECT_ROOT_DIRECTORY = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))

b_from_source = False
if (os.path.exists(os.path.join(PROJECT_ROOT_DIRECTORY, 'avernus'))
    and PROJECT_ROOT_DIRECTORY not in sys.path):
    b_from_source = True

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
    filename = os.path.join(config.config_path, 'avernus.log')
    if not os.path.exists(config.config_path):
        os.mkdir(config.config_path)
    filehandler = logging.FileHandler(filename=filename)
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

    path = os.path.join(config.get_data_path(), 'images')
    iconNames = [
    'avernus', 'tags', 'tag', 'watchlists', 'watchlist', 'portfolio',
    'portfolios', 'index', 'indices', 'arrow_down', 'arrow_med_down',
    'arrow_up', 'arrow_med_up', 'arrow_right', 'A', 'F', 'fund', 'stock',
    'etf', 'accounts', 'account', 'onvista', 'yahoo'
    ]
    for name in iconNames:
        icons.add_icon_name_from_directory(name, path)
    Gtk.Window.set_default_icon_name('avernus')


def main():
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
        from avernus.objects import session
        session.commit()
        session.close_all()
        threads.terminate_all()
        print "wie gesagt ... abgekachelt ..."
        exit(1)
