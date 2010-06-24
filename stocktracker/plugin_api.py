# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import pickle
from stocktracker import config, logger


class PluginAPI():

    def __init__(self, main_window, datasource_manager):
        self.main_window = main_window
        self.datasource_manager = datasource_manager
        self.logger = logger.logger
        
    def add_menu_item(self, item, menu_name):
        menu = self.main_window.main_menu
        for child in menu.get_children():
            if child.mname == menu_name:
                child.get_submenu().add(item)
                item.show_all()
         
    def remove_menu_item(self, item):
        menu = self.main_window.main_menu
        for child in menu.get_children():
            for sm in child.get_submenu():
                if sm == item:
                    child.get_submenu().remove(item)
                    
    def add_tab(self, item, name, categories):
        for cat in categories:
            self.main_window.tabs[cat].append((item, name))           

    def remove_tab(self, item, name, categories):
        for cat in categories:
            self.main_window.tabs[cat].remove((item, name))

    def register_datasource(self, item, name):
        self.datasource_manager.register(item, name)
        
    def deregister_datasource(self, item, name):
        self.datasource_manager.deregister(item, name)

    def load_configuration(self, plugin_name, filename):
        path = os.path.join(config.config_path, plugin_name, filename)        
        if os.path.isfile(path):
            with open(path, 'r') as file:
                return pickle.load(file)
        return None

    def save_configuration(self, plugin_name, filename, item):
        path = os.path.join(config.config_path, plugin_name)
        if not os.path.isdir(path):
            os.makedirs(path)
        path = os.path.join(path, filename)
        with open(path, 'wb') as file:
             pickle.dump(item, file)

