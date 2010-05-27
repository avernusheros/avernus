# -*- coding: utf-8 -*-
import os
import pickle
from stocktracker import config


class PluginAPI():

    def __init__(self, main_window, datasource_manager):
        self.main_window = main_window
        self.datasource_manager = datasource_manager
        
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

    def save_configuration(self, plugin_name, item):
        path = os.path.join(config.config_path, plugin_name)
        file = open(path, 'wb')
        pickle.dump(item, file)
        
    def load_configuration(self, plugin_name):
        path = os.path.join(config.config_path, plugin_name)
        if os.path.isfile(path):
            try:
                file = open(path, 'r');
                item = pickle.load(file)
            except:
                return None
            return item    
        return None
