# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
from gi.repository import Gtk
import logging

from avernus.config import avernusConfig

logger = logging.getLogger(__name__)


class PrefDialog(Gtk.Dialog):

    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 500

    def __init__(self, parent=None):
        Gtk.Dialog.__init__(self, _("Preferences"), parent,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                            )
        self.set_default_size(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        vbox = self.get_content_area()
        notebook = Gtk.Notebook()
        vbox.pack_start(notebook, True, True, 0)
        notebook.append_page(AccountPreferences(), Gtk.Label(label=_('Account')))
        notebook.append_page(PortfolioPreferences(), Gtk.Label(label=_('Portfolio')))
        notebook.append_page(ChartPreferences(), Gtk.Label(label=_('Chart')))

        self.show_all()
        self.run()
        self.destroy()


class PreferencesVBox(Gtk.VBox):

    def _add_section(self, name):
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        label = Gtk.Label()
        label.set_markup('<b>' + name + '</b>')
        frame.set_label_widget(label)
        vbox = Gtk.VBox()
        frame.add(vbox)
        self.pack_start(frame, False, False, 10)
        return vbox

    def _get_alignment(self):
        alignment = Gtk.Alignment.new(0.5, 0.5, 1.0, 1.0)
        alignment.set_property("left-padding", 12)
        return alignment

    def _add_option(self, vbox, name, option):
        alignment = self._get_alignment()
        vbox.add(alignment)
        button = Gtk.CheckButton(label=name)
        alignment.add(button)
        button.connect('toggled', self.on_toggled, option)
        pre = self.configParser.get_option(option, self.parser_section)
        pre = pre == "True"
        button.set_active(pre)

    def on_toggled(self, button, option):
        self.configParser.set_option(option, button.get_active(), self.parser_section)


class ChartPreferences(PreferencesVBox):

    parser_section = "Chart"

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.configParser = avernusConfig()

        section = self._add_section(_('Axis'))
        self._add_option(section, _('Normalize Y Axis'), 'normalize_y_axis')


class PortfolioPreferences(PreferencesVBox):

    parser_section = "Portfolio"

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.configParser = avernusConfig()

        section = self._add_section(_('Appearance'))
        self._add_option(section, _('Save vertical space'), 'smallPosition')


class AccountPreferences(PreferencesVBox):

    parser_section = "Account"

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.configParser = avernusConfig()

        section = self._add_section(_('Charts'))
        self._add_option(section, _('Include child categories'), 'categoryChildren')

        section = self._add_section(_('Category Assignments'))
        self._add_option(section, _('Include already categorized transactions'), 'assignments categorized transactions')

        section = self._add_section(_('Transactions'))
        self._add_option(section, _('Show horizontal grid lines'), 'transactionGrid')

