# -*- coding: utf8 -*-

# Bunch of meta data, used at least in the about dialog
__version__ = '0.1'
__url__='http://www.stocktracker.launchpad.org'
__author__ = 'Wolfgang Steitz <wsteitz@gmail.com>'
__copyright__ = 'Copyright 2008 Wolfgang Steitz <wsteitz@gmail.com>'
__license__='''\
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
'''

import os, logging

class stocktracker():
    '''FIXME'''

    def __init__(self, executable='stocktracker', verbose=False, debug=False):
        self.app = self # make Component methods work
        self.pid = os.getpid()
        self.executable = executable
        self.plugins = []
        self.logger = logging.getLogger('stocktracker')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(asctime)s %(funcName)s %(lineno)d %(message)s"))
        self.logger.addHandler(handler)
    

        #set log levels
        if verbose:
            self.logger.info('logger lever = verbose')
            self.logger.setLevel(logging.INFO)
        elif debug:
            self.logger.info('logger level = debug')
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.info('logger level = warning')
            self.logger.setLevel(logging.WARNING)

        if verbose or debug:
            self.logger.info('This is stocktracker %s' % __version__)
            try:
                from stocktracker._version import version_info
                self.logger.info(
                    'branch: %(branch_nick)s\n'
                    'revision: %(revno)d %(revision_id)s\n'
                    'date: %(date)s\n'
                        % version_info )
            except:
                self.logger.info('No bzr version-info found')
                
        self.load_config()
        self.load_plugins()

    def load_config(self):
        '''TODO'''

    def load_plugins(self):
        '''TODO'''
        plugins = []
        for plugin in plugins:
            self.load_plugin(plugin)

    def load_plugin(self, pluginname):
        '''FIXME'''
        pass

    def unload_plugin(self, plugin):
        '''FIXME'''
        pass
        
    def spawn(self, *args):
        '''FIXME'''
        args = list(args)
        if args[0] == 'stocktracker':
            args[0] = self.executable
        self.debug('Spawn process: '+' '.join(['"%s"' % a for a in argv]))
        try:
            pid = os.spawnvp(os.P_NOWAIT, argv[0], argv)
        except AttributeError:
            # spawnvp is not available on windows
            # TODO path lookup ?
            pid = os.spawnv(os.P_NOWAIT, args[0], args)
        self.debug('New process: %i' % pid)

    def start(self):
        from stocktracker import stocktracker_gui
        import gtk
        stocktracker_gui.StockTracker()
        gtk.main()



