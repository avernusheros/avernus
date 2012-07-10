from gi.repository import Gtk, GObject, Gdk

from avernus.gui import get_ui_file
from avernus.gui import gui_utils
from avernus.controller import asset_controller
from avernus.gui.portfolio.dialogs import EditAssetDialog


class AssetManager:

    def __init__(self, parent=None):
        self.parent = parent
        builder = Gtk.Builder()
        builder.add_from_file(get_ui_file("portfolio/asset_manager_dialog.glade"))

        self.tree = gui_utils.Tree()
        self.tree.set_headers_visible(True)
        model = Gtk.ListStore(object, str, str, str)
        self.tree.set_model(model)
        self.tree.create_column(_('Name'), 1)
        self.tree.create_column(_('ISIN'), 2)
        self.tree.create_column(_('Type'), 3)

        sw = builder.get_object("scrolledwindow")
        sw.add(self.tree)

        tb = builder.get_object("toolbar")
        tb.get_style_context().add_class("inline-toolbar")

        # connect signals
        handlers = {
            "on_delete_clicked": self.on_delete,
            "on_edit_clicked": self.on_edit
            }
        builder.connect_signals(handlers)
        self.tree.connect("button-press-event", self.on_button_press_event)

        # load items
        for asset in asset_controller.get_all_assets():
            model.append(self.get_row(asset))

        dlg = builder.get_object("dialog")
        dlg.set_transient_for(parent)
        dlg.add_buttons(
                    Gtk.STOCK_CLOSE, Gtk.ResponseType.ACCEPT)

        dlg.show_all()
        dlg.run()
        dlg.destroy()

    def get_row(self, asset):
        return [asset, GObject.markup_escape_text(asset.name), asset.isin, asset.type]

    def on_button_press_event(self, widget, event):
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_edit(widget)

    def on_edit(self, widget, user_data=None):
        asset, iterator = self.tree.get_selected_item()
        if asset:
            EditAssetDialog(asset, self.parent)
            # update tree
            self.tree.get_model()[iterator] = self.get_row(asset)

    def on_delete(self, widget, user_data=None):
        asset, iterator = self.tree.get_selected_item()
        if asset:
            # check if there is a position with this stock
            if asset_controller.is_asset_used(asset):
                # show warning
                dlg = Gtk.MessageDialog(self.parent,
                Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK)
                dlg.set_markup(_("The asset ") + "<b>" + asset.name + '</b>' + _(" is linked to a position and cannot be deleted."))
                dlg.show_all()
                response = dlg.run()
                dlg.destroy()
            else:
                asset_controller.delete_object(asset)
                self.tree.get_model().remove(iterator)
