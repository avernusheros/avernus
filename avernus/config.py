#!/usr/bin/env python
# -*- coding: latin-1 -*-

from __future__ import with_statement
import os, glib
__avernus_data_directory__ = '../data/'
import ConfigParser


class project_path_not_found(Exception):
    pass

def getdatapath():
    """Retrieve data path

    This path is by default <avernus_lib_path>/../data/ in trunk
    and /usr/share/avernus in an installed version but this path
    is specified at installation time.
    """
    # get pathname absolute or relative
    if __avernus_data_directory__.startswith('/'):
        pathname = __avernus_data_directory__
    else:
        pathname = os.path.dirname(__file__) + '/' + __avernus_data_directory__

    abs_data_path = os.path.abspath(pathname)
    if os.path.exists(abs_data_path):
        return abs_data_path
    else:
        raise project_path_not_found

data_path = glib.get_user_data_dir()
config_path = os.path.join( glib.get_user_config_dir(), 'avernus')
plugins_path = [os.path.join(os.getcwd(), 'avernus/plugins'), os.path.join(config_path,'plugins') ]
#media_path = os.path.join(getdatapath(), 'media')
timezone = 'CET'


class avernusConfig():
    def __init__(self):
        parser = self.parser = ConfigParser.ConfigParser()
        self.filename = os.path.join(config_path, 'avernus.conf')
        if not os.path.exists(self.filename):
            self.create()
        self.parser.read(self.filename)

    def create(self):
        if not os.path.exists(config_path):
            os.mkdir(config_path)

        if not self.parser.has_section('General'):
            self.parser.add_section('General')
        if not self.parser.has_section('Plugins'):
            self.parser.add_section('Plugins')
        if not self.parser.has_section('Gui'):
            self.parser.add_section('Gui')
        self.set_option('database file', os.path.join(config_path, 'avernus.db'))
        self.write()

    def write(self):
        #print self
        with open(self.filename, 'wb') as configfile:
            self.parser.write(configfile)

    def get_option(self, name, section = 'General'):
        if self.parser.has_option(section, name):
            return self.parser.get(section, name)

    def set_option(self, name, value, section = 'General'):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, name, value)
        self.write()

    def __repr__(self):
        txt = ''
        for section in self.parser.sections():
            txt+=section
            txt+='\n-----------'
            for option in self.parser.options(section):
                txt+='\n'+option
            txt+='\n\n'
        return txt
