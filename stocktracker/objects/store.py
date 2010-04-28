#!/usr/bin/env python

import sqlite3 as db
import os


class Store(object):

    commitDirty = True
    policy = {
                'commitAfterInsert': True,
                'commitAfterUpdate': True,
                'commitAfterDelete': True,
                'retrieveOnGetAll':True,
                'createCompositeOnCreate':True,
                'retrieveCompositeOnCreate':False,
                }

    def __init__(self, fileName):
        if os.path.exists(fileName):
            self.new = False
        else: self.new = True
        
        self.fileName = fileName
        self.con = None
        self.dirty = False
        self.connect()

    def connect(self):
        if self.dirty and self.commitDirty:
            self.con.commit()
        self.con = db.connect(self.fileName, detect_types=db.PARSE_DECLTYPES|db.PARSE_COLNAMES)
        self.con.row_factory = db.Row
        self.dirty = False

    def commit(self):
        self.con.commit()
        self.dirty = False
