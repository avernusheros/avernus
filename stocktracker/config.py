#!/usr/bin/env python
# -*- coding: latin-1 -*-


import os, sys
__stocktracker_data_directory__ = '../data/'
import ConfigParser
from stocktracker.session import session


class project_path_not_found(Exception):
    pass

def getdatapath():
    """Retrieve foo data path

    This path is by default <stocktracker_lib_path>/../data/ in trunk
    and /usr/share/stocktracker in an installed version but this path
    is specified at installation time.
    """

    # get pathname absolute or relative
    if __stocktracker_data_directory__.startswith('/'):
        pathname = __stocktracker_data_directory__
    else:
        pathname = os.path.dirname(__file__) + '/' + __stocktracker_data_directory__

    abs_data_path = os.path.abspath(pathname)
    if os.path.exists(abs_data_path):
        return abs_data_path
    else:
        raise project_path_not_found



config_path = os.path.join( os.getenv('HOME'), '.stocktracker')
#media_path = os.path.join(getdatapath(), 'media')

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
