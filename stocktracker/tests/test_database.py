#!/usr/bin/env python

import unittest
from stocktracker.objects import model, store, controller

class A(model.SQLiteEntity):
    __primaryKey__ = "name"
    __tableName__ = "a"
    __columns__ = {
                   "name": "VARCHAR",
                   "comment": "TEXT"
                   }
    
class B(model.SQLiteEntity):
    __primaryKey__ = "name"
    __tableName__ = "b"
    __columns__ = {
                   "name": "VARCHAR",
                   "link": A
                   }
    __relations__ = {"theAs":A}


class TestDatabase(unittest.TestCase):
    
    def setUp(self, path=":memory:"):
        model.store = store.Store(path)
        for cl in [A,B]:
            cl.createTable()
        a = A(name='foo', comment='')
        a.insert()
    
    def test_one2one(self):
        a = A(name='foo')
        b = B(name="test", link=a)
        self.assertEquals(b.link,a)
        b.insert()
        self.assertEquals(b.link,a)
        b2 = B.getByPrimaryKey("test")
        self.assertEquals(b.link,a)
       
    def test_change_comment(self):
        a = A.getByPrimaryKey("foo")
        self.assertEqual(a.comment, "")
        a.comment = "bla bla"
        a.update()
        self.assertEqual(a.comment, "bla bla")
    
    def test_remove(self):
        b = B(name="foo", link=None)
        b.insert()
        b.delete()
        self.assertEqual(B.getByPrimaryKey("foo"), None)
                
    def test_relations(self):
        anA = A(name='foo')
        anotherA = A(name='foo2')
        aB  = B(name='bar')
        aB.theAs.append(anA)
        aB.theAs.append(anotherA)
        self.assertEqual(aB.theAs[0], anA)
        self.assertEqual(aB.theAs[1], anotherA)
        aB.theAs.remove(anotherA)
        self.assertEqual(len(aB.theAs), 1)

if __name__ == '__main__':
    unittest.main()
