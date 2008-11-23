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


def start():
    from stocktracker import stocktracker_gui
    import gtk
    stocktracker_gui.StockTracker()
    gtk.main()



