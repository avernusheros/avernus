#!/usr/bin/env python
from avernus.gui import gui_utils, page, get_avernus_builder
from avernus.objects import asset_category, account, position
from gi.repository import Gdk, Gtk


class AssetAllocation(page.Page):

    OBJECT = 0
    NAME = 1
    TARGET_PERCENT = 2
    TARGET = 3
    CURRENT_PERCENT = 4
    CURRENT = 5
    DELTA_PERCENT = 6
    DELTA = 7

    def __init__(self):
        page.Page.__init__(self)
        self.builder = get_avernus_builder()
        self.widget = self.builder.get_object("asset_allocation_widget")
        self.treestore = self.builder.get_object("asset_allocation_store")
        self.tree = self.builder.get_object("asset_allocation_tree")
        self.tree.connect("map", self.update_page)
        self.init_widgets()

    def init_widgets(self):
        # FIXME maybe write a helper function to do this
        cell = self.builder.get_object("cellrenderertext46")
        column = self.builder.get_object("treeviewcolumn46")
        column.set_cell_data_func(cell, gui_utils.percent_format, self.TARGET_PERCENT)
        cell = self.builder.get_object("cellrenderertext47")
        column = self.builder.get_object("treeviewcolumn47")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.TARGET)
        cell = self.builder.get_object("cellrenderertext48")
        column = self.builder.get_object("treeviewcolumn48")
        column.set_cell_data_func(cell, gui_utils.percent_format, self.CURRENT_PERCENT)
        cell = self.builder.get_object("cellrenderertext49")
        column = self.builder.get_object("treeviewcolumn49")
        column.set_cell_data_func(cell, gui_utils.currency_format, self.CURRENT)
        cell = self.builder.get_object("cellrenderertext50")
        column = self.builder.get_object("treeviewcolumn50")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_percent, self.DELTA_PERCENT)
        cell = self.builder.get_object("cellrenderertext51")
        column = self.builder.get_object("treeviewcolumn51")
        column.set_cell_data_func(cell, gui_utils.float_to_red_green_string_currency, self.DELTA)

    def insert_category(self, cat, iterator):
        return self.treestore.append(iterator,
                        [cat,
                         cat.name,
                         cat.target_percent,
                         cat.target,
                         cat.current_percent,
                         cat.current,
                         cat.delta_percent,
                         cat.delta,
                         True,
                         "gtk-directory"
                        ])

    def load_categories(self):
        def insert_recursive(cat, iterator):
            new_iter = self.insert_category(cat, iterator)
            for child in cat.children:
                insert_recursive(child, new_iter)
            for acc in cat.accounts:
                self.treestore.append(new_iter,
                        [acc, acc.name, 0.0, 0.0, acc.balance / cat.current,
                         acc.balance, 0.0, 0.0, False, "account"])
            for pos in cat.positions:
                self.treestore.append(new_iter,
                        [pos, pos.asset.name, 0.0, 0.0,
                         pos.current_value / cat.current, pos.current_value,
                         0.0, 0.0, False, "portfolio"])

        self.treestore.clear()
        roots = asset_category.get_root_categories()
        asset_category.calculate_values()
        for root in roots:
            insert_recursive(root, None)

        # expand first level
        iterator = self.treestore.get_iter_first()
        while iterator:
            path = self.treestore.get_path(iterator)
            self.tree.expand_row(path, False)
            iterator = self.treestore.iter_next(iterator)

        self.tree.set_cursor(0)

    def show_context_menu(self, event):
        selected_item = self.get_selected_item()[0]
        if selected_item.__class__.__name__ == "AssetCategory":
            context_menu = self.builder.get_object("asset_allocation_contextmenu")
            # accounts
            account_menu = self.builder.get_object("aa_add_account_menu")
            all_accounts = account.get_all_accounts()
            if all_accounts:
                account_menu.set_visible(True)
                menu = Gtk.Menu()
                account_menu.set_submenu(menu)
                for acc in all_accounts:
                    if selected_item not in acc.asset_categories:
                        item = Gtk.MenuItem(label=acc.name)
                        item.connect("activate", self.on_aa_add_account, selected_item, acc)
                        menu.append(item)
            # positions
            positions_menu = self.builder.get_object("aa_add_positions_menu")
            positions = position.get_all_portfolio_positions()
            if positions:
                positions_menu.set_visible(True)
                menu = Gtk.Menu()
                positions_menu.set_submenu(menu)
                for pos in positions:
                    if pos.quantity > 0:
                        item = Gtk.MenuItem(label=pos.asset.name)
                        item.connect("activate", self.on_aa_add_position, selected_item, pos)
                        menu.append(item)
                account_menu.show_all()
        else:
            context_menu = self.builder.get_object("asset_allocation_item_contextmenu")
        context_menu.show_all()
        context_menu.popup(None, None, None, None, event.button, event.time)

    def get_selected_item(self):
        selection = self.tree.get_selection()
        if selection:
            model, selection_iter = selection.get_selected()
            if selection_iter and model:
                return model[selection_iter][self.OBJECT], selection_iter
        return None, None

    def is_category(self, item):
        return isinstance(item, asset_category.AssetCategory)

    def on_aa_add_account(self, widget, category, acc):
        acc.asset_categories.append(category)
        self.load_categories()

    def on_aa_add_position(self, widget, category, pos):
        pos.asset_categories.append(category)
        self.load_categories()

    def on_asset_allocation_button_press(self, widget, event):
        if event.button == 3:
            self.show_context_menu(event)

    def on_aa_add_root(self, widget):
        asset_category.AssetCategory(name=_("new root"), target_percent=1.0)
        self.load_categories()

    def on_aa_add_category(self, widget):
        parent = self.get_selected_item()[0]
        asset_category.AssetCategory(parent=parent, name=_("new category"), target_percent=0.0)
        self.load_categories()

    def on_aa_remove_category(self, widget):
        cat = self.get_selected_item()[0]
        # move children to parent category
        for child in cat.children:
            child.parent = cat.parent
        cat.delete()
        self.load_categories()

    def on_aa_category_edited(self, cell, path, new_name):
        if self.treestore[path][self.OBJECT].name != new_name:
            self.treestore[path][self.OBJECT].name = new_name
            self.treestore[path][self.NAME] = new_name

    def on_aa_targetpercent_edited(self, cell, path, new_value):
        new_value = float(new_value) / 100
        if new_value != self.treestore[path][self.OBJECT].target_percent:
            self.treestore[path][self.OBJECT].target_percent = new_value
            self.load_categories()

    def on_aa_remove_from_category(self, widget):
        item, child_iter = self.get_selected_item()
        parent_iter = self.treestore.iter_parent(child_iter)
        category = self.treestore[parent_iter][self.OBJECT]
        item.asset_categories.remove(category)
        self.load_categories()

    def on_asset_allocation_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Delete':
            if self.is_category(self.get_selected_item()[0]):
                self.on_aa_remove_category(widget)
            else:
                self.on_aa_remove_from_category(widget)
            return True
        return False

    def on_asset_allocation_row_changed(self, model, path, iterator):
        item = self.treestore[iterator][self.OBJECT]
        parent_iter = self.treestore.iter_parent(iterator)
        if parent_iter:
            parent = self.treestore[parent_iter][self.OBJECT]
            if self.is_category(item):
                item.parent = parent
            else:
                item.asset_category = parent
        self.load_categories()
