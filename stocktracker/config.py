#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    config.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
#
#    This file is part of stocktracker.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
__stocktracker_data_directory__ = '../data/'
import ConfigParser
from stocktracker.session import session


class project_path_not_found(Exception):
    pass

def getdatapath(folder = ''):
    """Retrieve stocktracker data path

    This path is by default <stocktracker_lib_path>/../data/ in trunk
    and /usr/share/stocktracker in an installed version but this path
    is specified at installation time.
    """

    # get pathname absolute or relative
    if __stocktracker_data_directory__.startswith('/'):
        pathname = __stocktracker_data_directory__
    else:
        pathname = os.path.dirname(__file__) + '/' + __stocktracker_data_directory__

    abs_data_path = os.path.join(os.path.abspath(pathname),folder)
    if os.path.exists(abs_data_path):
        return abs_data_path
    else:
        raise project_path_not_found



config_path = os.path.join( os.getenv('HOME'), '.stocktracker')
media_path = os.path.join(getdatapath(), 'media')

quotes_file = os.path.join(config_path, 'historical_data.db')
timezone = 'CET'
currency = '€'

config_template = \
"""
[General]
database=stocktracker.db 
"""


class StocktrackerConfig():
    def __init__(self):
        parser = self.parser = ConfigParser.ConfigParser()
        self.filename = os.path.join(config_path, 'stocktracker.conf')
        if not os.path.exists(self.filename):
            self.create()
        self.parser.read(self.filename)
        
        session['config'] = self        
    
    def create(self):
        if not os.path.exists(config_path):
            os.mkdir(config_path)

        if not self.parser.has_section('General'):
            self.parser.add_section('General')
        
        self.set_option('database file', os.path.join(config_path, 'stocktracker.db'))
        self.write()

    def write(self):
        fd = open(self.filename, 'w')
        self.parser.write(fd)
    
    def get_option(self, name, section = 'General'):
        if self.parser.has_option(section, name):
            return self.parser.get(section, name)

    def set_option(self, name, value, section = 'General'):
        self.parser.set(section, name, value)
