# -*- coding: utf-8 -*-


class PluginAPI():

    def __init__(self, main_window):
        self.main_window = main_window
        
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
                    
