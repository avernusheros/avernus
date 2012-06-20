#!/usr/bin/env python
# -*- coding: latin-1 -*-

import os, glib
__avernus_data_directory__ = '/usr/share/avernus/'
import ConfigParser


class project_path_not_found(Exception):
    pass

data_path = None

def get_data_path():
    """Retrieve data path

    This path is by default <avernus_lib_path>/../data/ in trunk
    and /usr/share/avernus in an installed version but this path
    is specified at installation time.
    """
    global data_path
    if data_path:
        return data_path
    # get pathname absolute or relative
    if os.path.exists(__avernus_data_directory__): #.startswith('/')
        pathname = __avernus_data_directory__
    else:
        pathname = os.path.dirname(__file__) + '/../data'

    abs_data_path = os.path.abspath(pathname)
    if os.path.exists(abs_data_path):
        data_path = abs_data_path
        return abs_data_path
    else:
        raise project_path_not_found, abs_data_path

config_path = os.path.join( glib.get_user_config_dir(), 'avernus')
timezone = 'CET'

instance = None

def get_ui_file(filename):
    global data_path
    if not data_path:
        get_data_path()
    return os.path.join(data_path, "ui", filename)

def avernusConfig():
    global instance
    if not instance:
        instance = AvernusConfig()
    return instance

class AvernusConfig():
    def __init__(self):
        parser = self.parser = ConfigParser.SafeConfigParser()
        self.filename = os.path.join(config_path, 'avernus.conf')
        if not os.path.exists(self.filename):
            self.create()
        self.parser.read(self.filename)

    def create(self):
        if not os.path.exists(config_path):
            os.mkdir(config_path)
        if not self.parser.has_section('General'):
            self.parser.add_section('General')
        if not self.parser.has_section('Gui'):
            self.parser.add_section('Gui')
        if not self.parser.has_section('Account'):
            self.parser.add_section('Account')
        self.set_option('database file', os.path.join(config_path, 'avernus.db'))
        self.write()

    def write(self):
        with open(self.filename, 'wb') as configfile:
            self.parser.write(configfile)

    def get_option(self, name, section = 'General', default = None):
        #print name, type(name), section, type(section)
        if self.parser.has_option(section, name):
            return self.parser.get(section, name)
        if default != None:
            self.set_option(name, default, section)
        return default
        #print "unkown config request ", name, section

    def set_option(self, name, value, section = 'General'):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, name, str(value))
        self.write()
        #print "written", name, value

    def __repr__(self):
        txt = ''
        for section in self.parser.sections():
            txt+=section
            txt+='\n-----------'
            for option in self.parser.options(section):
                txt+='\n'+option
            txt+='\n\n'
        return txt
