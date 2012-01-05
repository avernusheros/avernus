#!/usr/bin/env python

import sqlite3
import os
from Queue import Queue
import threading
import shutil, time

class Store(threading.Thread):

    policy = {
                'retrieveOnGetAll':True,
                'createCompositeOnCreate':True,
                'retrieveCompositeOnCreate':False,
                }

    def __init__(self, db):
        if os.path.exists(db):
            self.new = False
        else: self.new = True
        super(Store, self).__init__()
        self.db = db
        self.reqs=Queue()
        self.batch = False

        self.start()

    def run(self):
        cnx = sqlite3.connect(self.db, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cnx.isolation_level = "DEFERRED"
        cnx.row_factory = sqlite3.Row
        cursor = cnx.cursor()
        while True:
            req, arg, res = self.reqs.get()
            if req=='--close--': break
            cursor.execute(req, arg)
            if res:
                for rec in cursor:
                    res.put(rec)
                res.put('--no more--')
            else:
                cnx.commit()
        cnx.close()

    def execute(self, req, arg=None, res=None):
        self.reqs.put((req, arg or tuple(), res))

    def select(self, req, arg=None):
        res=Queue()
        self.execute(req, arg, res)
        while True:
            rec=res.get()
            if rec=='--no more--': break
            yield rec

    def close(self):
        self.execute('--close--')

    def backup(self):
        backup_file = self.db+'.backup'+time.strftime(".%Y%m%d-%H%M")
        shutil.copyfile ( self.db, backup_file )


if __name__ == "__main__":
    sql = Store(":memory:")
    sql.execute("create table people(name,first)")
    sql.execute("insert into people values('VAN ROSSUM','Guido')")
    sql.execute("insert into people values(?,?)", ('TORVALDS','Linus'))
    for f, n in sql.select("select first, name from people"):
        print f, n
    sql.close()

