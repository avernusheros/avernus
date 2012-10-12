#!/usr/bin/env python

import datetime
import logging
from gi.repository import Gtk

logger = logging.getLogger(__name__)



class CalendarDialog(Gtk.Dialog):

    def __init__(self, date=None, parent=None):
        Gtk.Dialog.__init__(self, _("Chose a date"), parent
                            , Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                             Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT)
                            )
        vbox = self.get_content_area()
        self.calendar = Gtk.Calendar()
        self.date = date
        if date:
            self.calendar.select_month(date.month - 1, date.year)
            self.calendar.select_day(date.day)

        vbox.pack_start(self.calendar, True, True, 0)

        self.calendar.connect("day-selected-double-click", self.on_day_selected)
        self.show_all()
        self.run()
        self.process_result()

    def process_result(self):
        y, m, d = self.calendar.get_date()
        self.date = datetime.date(y, m + 1, d)
        self.destroy()

    def on_day_selected(self, cal):
        self.process_result()
