#!/usr/bin/env python

import __builtin__
__builtin__._ = str


from avernus import objects
from avernus.objects import db

dbfile = ":memory:"
db.set_db(dbfile)
db.connect()

from avernus.data_sources import yahoo
from avernus.controller import datasource_controller as dsm
from avernus.objects import asset
from avernus.gui import threads
import datetime
import unittest
from gi.repository import Gtk, GObject, GLib





class ThreadingTest(unittest.TestCase):

    def setUp(self):
        db.set_db(dbfile)
        db.connect()
        objects.session.commit()
        GObject.threads_init()
        
    def tearDown(self):
        threads.terminate_all()

    def test_updating_of_new_assets(self):
        
        def bar(*args, **kwargs):
            task = threads.GeneratorTask(dsm.update_assets, None, 
                                         None, args=asset.get_all_assets())

            task.start()
            task.join()
            
            for a in asset.get_all_assets():
                self.assertNotEqual(a.date.year, 1970)
            
            self.counter += 1
            if self.counter == 2:
                Gtk.main_quit()
            else:
                # test if it works a second time (was a bug..)
                dsm.search("yahoo", callback=bar)
        
        def start():
            dsm.search("google", callback=bar)
            
        self.counter = 0
        GLib.idle_add(start)
        Gtk.main()





