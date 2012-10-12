#!/usr/bin/env python
from avernus.gui import gui_utils, get_ui_file
from avernus.objects import account
from gi.repository import GObject, Gdk, Gtk


class CategoriesTree(gui_utils.Tree):

    def __init__(self, updater, builder):
        gui_utils.Tree.__init__(self)
        self.updater = updater
        self.model = Gtk.TreeStore(object, str)
        self.set_model(self.model)
        col, self.cell = self.create_column(_('Categories'), 1)
        self.cell.set_property('editable', True)

        #drag n drop
        self.set_reorderable(True)

        #connect signals
        self.cell.connect('edited', self.on_cell_edited)
        self.connect('cursor_changed', self.on_cursor_changed)
        self.connect('button_press_event', self.on_button_press)
        #FIXME
        #self.connect('key_press_event', self.on_key_press)
        self.model.connect('row_changed', self.on_row_changed)

        # actions
        self.actiongroup1 = Gtk.ActionGroup('categories1')
        self.actiongroup1.add_actions([
                ('edit' , Gtk.STOCK_EDIT, 'rename category', None, _('Rename selected category'), self.on_edit),
                ('remove', Gtk.STOCK_DELETE, 'remove category', None, _('Remove selected category'), self.on_remove),
                ('unselect', Gtk.STOCK_CLEAR, 'unselect category', None, _('Unselect selected category'), self.on_unselect),
                     ])
        self.actiongroup2 = Gtk.ActionGroup('categories2')
        self.actiongroup2.add_actions([
                ('add', Gtk.STOCK_ADD, 'new category', None, _('Add new category'), self.on_add)
            ])
        # toolbar
        toolbar = builder.get_object("category_tb")
        toolbar.get_style_context().add_class("inline-toolbar")
        for action in self.actiongroup2.list_actions() + self.actiongroup1.list_actions():
            toolbar.insert(action.create_tool_item(), -1)

    def load_categories(self):
        def insert_recursive(cat, parent):
            new_iter = model.append(parent, [cat, cat.name])
            for child_cat in cat.children:
                insert_recursive(child_cat, new_iter)
        model = self.get_model()
        root_categories = account.get_root_categories()
        for cat in root_categories:
            insert_recursive(cat, None)
        self.expand_all()

    def insert_item(self, cat, parent=None):
        return self.get_model().append(parent, [cat, cat.name])

    def on_add(self, widget=None, data=None):
        parent, selection_iter = self.get_selected_item()
        item = account.AccountCategory(name='new category', parent=parent)
        iterator = self.insert_item(item, parent=selection_iter)
        model = self.get_model()
        if selection_iter:
            self.expand_row(model.get_path(selection_iter), True)
        self.cell.set_property('editable', True)
        self.set_cursor(model.get_path(iterator), start_editing=True)

    def on_row_changed(self, model, path, iterator):
        value = self.model[iterator][0]
        parent_iter = self.model.iter_parent(iterator)
        if parent_iter:
            parent = self.model[parent_iter][0]
        else:
            parent = None
        value.parent = parent

    def on_edit(self, widget=None, data=None):
        cat, selection_iter = self.get_selected_item()
        self.cell.set_property('editable', True)
        self.set_cursor(self.get_model().get_path(selection_iter), self.get_column(0), start_editing=True)

    def on_remove(self, widget=None, data=None):
        obj, iterator = self.get_selected_item()
        if obj is None:
            return False
        dlg = Gtk.MessageDialog(None,
             Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION,
             Gtk.ButtonsType.OK_CANCEL)
        msg = _("Permanently delete category <b>") + GObject.markup_escape_text(obj.name) + '</b>?'
        model = self.get_model()
        if model.iter_has_child(iterator):
            msg += _("\nWill also delete subcategories")
        dlg.set_markup(_(msg))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.OK:
            queue = [(iterator, obj)]
            remove_queue = []
            while len(queue) > 0:
                curr_iter, curr_obj = queue.pop()
                curr_obj.delete()
                if model.iter_has_child(curr_iter):
                    for i in range(0, model.iter_n_children(curr_iter)):
                        new_iter = model.iter_nth_child(curr_iter, i)
                        queue.append((new_iter, model[new_iter][0]))
                remove_queue.insert(0, curr_iter)
            for to_remove in remove_queue:
                model.remove(to_remove)
            self.on_unselect()

    def on_cell_edited(self, cellrenderertext, path, new_text):
        m = self.get_model()
        m[path][0].name = m[path][1] = unicode(new_text)
        cellrenderertext.set_property('editable', False)

    def show_context_menu(self, event):
        context_menu = Gtk.Menu()
        for action in self.actiongroup2.list_actions() + self.actiongroup1.list_actions():
            context_menu.add(action.create_menu_item())
        context_menu.popup(None, None, None, None, event.button, event.time)

    def on_button_press(self, widget, event):
        if event.button == 3:
            self.show_context_menu(event)
        else:
            if not self.get_path_at_pos(int(event.x), int(event.y)):
                self.on_unselect()
        return False

    def on_key_press(self, widget, event):
        if Gdk.keyval_name(event.keyval) == 'Delete':
            self.on_remove()
            return True
        return False

    def on_cursor_changed(self, widget):
        cat, iterator = self.get_selected_item()
        if cat is not None:
            self.on_select(cat)
        else:
            self.on_unselect()

    def on_unselect(self, widget=None, data=None):
        selection = self.get_selection()
        if selection != None:
            self.updater(None)
            selection.unselect_all()
            self.actiongroup1.set_sensitive(False)

    def on_select(self, obj):
        self.updater(obj)
        self.actiongroup1.set_sensitive(True)
