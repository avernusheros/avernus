#!/usr/bin/env python

import unittest
from avernus.objects import model, store


class A(model.SQLiteEntity):
    __primaryKey__ = "id"
    __tableName__ = "a"
    __columns__ = {
                    "id": "INTEGER",
                   "name": "VARCHAR",
                   "comment": "VARCHAR"
                   }

class B(model.SQLiteEntity):
    __primaryKey__ = "id"
    __tableName__ = "b"
    __columns__ = {
                    "id": "INTEGER",
                   "name": "VARCHAR",
                   "link": A
                   }
    __relations__ = {"theAs":A}


class TestDatabase(unittest.TestCase):

    def setUp(self, path=":memory:"):
        model.store = store.Store(path)
        for cl in [A,B]:
            cl.createTable()
        a = A(id=0, name='foo', comment='')
        a.insert()

    def test_one2one(self):
        a = A(id= 1, name='foo', comment='bar')
        b = B(id = 2, name="test", link=a)
        self.assertEquals(b.link,a)
        b.insert()
        self.assertEquals(b.link,a)
        b2 = B.getByPrimaryKey(b.id)
        self.assertEquals(b.link,a)

    def test_change_comment(self):
        a = A.getByPrimaryKey(1)
        self.assertEqual(a.comment, "")
        a.comment = "bla bla"
        a.update()
        self.assertEqual(a.comment, "bla bla")

    def test_remove(self):
        b = B(name="foo", link=None)
        b.insert()
        id = b.id
        b.delete()
        self.assertEqual(B.getByPrimaryKey(id), None)

    def test_relations(self):
        anA = A(id=33, name='foo', comment='bar')
        anotherA = A(id=44, name='foo2', comment='bar2')
        aB  = B(id=55, name='bar', link=None)
        aB.theAs.append(anA)
        aB.theAs.append(anotherA)
        self.assertEqual(aB.theAs[0], anA)
        self.assertEqual(aB.theAs[1], anotherA)
        aB.theAs.remove(anotherA)
        self.assertEqual(len(aB.theAs), 1)

if __name__ == '__main__':
    unittest.main()
