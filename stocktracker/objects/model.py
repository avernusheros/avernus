#!/usr/bin/env python

from stocktracker.logger import logger
from inspect import isclass

store = None

def checkTableExistence(name):
    c = store.con.cursor()
    c.execute("pragma table_info("+name+")")
    return len(c.fetchall())>0


class Cache(object):
    """
    Caches Objects that have already been retrieved from the database.
    Prevents both duplicate but different objects and unnecessary queries.
    """

    def __init__(self):
        self.objects = {}

    def cache(self, obj):
        """
        Caches an object. Key to caching is the tuple (class,primary key)
        """
        logger.debug("Caching "+str(obj))
        self.objects[(obj.__class__,obj.getPrimaryKey())] = obj

    def isCached(self, t, k):
        return (t,k) in self.objects

    def get(self, t, k):
        logger.debug("Return cached object for (type,key) " + str((t,k)))
        return self.objects[(t,k)]

    def unCache(self, obj):
        logger.debug("UnCaching " +str(obj))
        del self.objects[(obj.__class__,obj.getPrimaryKey())]

# module global cache
cache = Cache()

class SQList(list):
    """
    Subclass of the generic python list type to hook into appending and removing.
    Append and remove are the only two supported operations.
    Because duplicate relations are not supported by the table structure, this list
    does not support duplicate entries and is therefore more like an ordered Set.
    Because database tables do not guarantee order preservation, this list is not
    even ordered, so it is a set.
    """
    
    def __init__(self, parent, *args, **kwargs):
        """
        for the callback to the database, the parent is stored in the list
        """
        list.__init__(self,*args,**kwargs)
        self.parent = parent
    
    def append(self,x,store=True):
        """
        if x is already present, nothing happens.
        if x is new, the parent gets noticed
        """
        if x in self:
            logger.error("Duplicate Relation Entry parent: " + str(self.parent) + " entity " + str(x))
            return None
        list.append(self,x)
        if store:
            self.parent.addRelationEntry(self,x)
            
    def extend(self, other,store=True):
        """
        simluation with multiple appends
        """
        for some in other:
            self.append(some,store)
            
    def insert(self, i, x, store=True):
        """
        as ordering is not guaranteed, an insert is an append with ignoring the position
        """
        self.append(x,store)
        
    def remove(self,x):
        """
        the removal of the object is passed on to the parent to remove the database entry
        """
        list.remove(self,x)
        self.parent.removeRelationEntry(self,x)

class SQLiteEntity(object):
    """
    SQLiteEntity is the common base class for all persistent entities.
    """

    #Define the columns that the database table shall have like name:type
    __columns__ = {}
    #the name of the table to store the entity's information in
    __tableName__ = None
    #name of the primary key. this is mandatory EXACTLY one of the __columns__
    __primaryKey__ = None
    #non one2one relations to other entities like name:type
    __relations__ = {}
    __callbacks__ = {}

    def __init__(self, *args, **kwargs):
        """
        The constructor always shall receive all the values for the database relevant
        attributes in kwargs, at the very least the primary key.
        """
        self.__composite_retrieved__ = False
        for arg, val in kwargs.items():
            #process the keyword args
            #does the colum the arg refers to denote a one2one?
            if isclass(self.__columns__[arg]):
                #yes it does
                #did we receive a key or an object
                if isinstance(val, SQLiteEntity):#an object
                    self.__setattr__(arg, val, True)
                else:#a key
                    #retrieve the object to reference
                    self.__setattr__(
                                     arg, 
                                     self.__columns__[arg].getByPrimaryKey(val),
                                     True
                                     )
            else:#a non-complex value
                self.__setattr__(arg, val, True)
        #the entity shall retrieve its relations upon creation
        #loop all relations
        for name,relation in self.__relations__.items():
            erg = SQList(self)
            #policy gate for resolving of composite relations
            if store.policy['retrieveCompositeOnCreate']:
                erg = self.retrieveComposite(name, relation)
            #attach the list under the name specified by the relations dict
            self.__setattr__(name,erg, True)
        if 'onInit' in self.__callbacks__:
            self.__callbacks__['onInit'](self)
    
    def __setattr__(self, name, val, insert = False):
        object.__setattr__(self, name, val)
        if not insert and name in self.__columns__.keys():
            self.update()
            
    def retrieveAllComposite(self):
        for name,relation in self.__relations__.items():
            self.__setattr__(name,self.retrieveComposite(name, relation))
        self.__composite_retrieved__ = True
            
    def retrieveComposite(self, name, relation):
        #the column name of the partner in the relations table
        relKey = self.__class__.generateRelationTableOtherKey(relation)
        #the column name of myself in the relations table
        myKey = self.__class__.generateRelationTableMyKey()
        #select all of my relations
        query = "SELECT " + relKey
        query += " FROM " + self.__class__.generateRelationTableName(relation, name)
        query += " WHERE " + myKey +"=:temp"
        vals = {'temp':self.getPrimaryKey()}
        logger.info(query+str(vals))
        c = store.con.cursor()
        c.execute(query,vals)
        rows = c.fetchall()
        erg = SQList(self)
        #retrieve all related objects by their primary key
        for row in rows:
            erg.append(relation.getByPrimaryKey(row[relKey]), store=False)
        if 'onRetrieveComposite' in self.__callbacks__:
            self.__callbacks__['onRetrieveComposite'](self, name=name,relation=relation,erg=erg)
        return erg
           
    def getPrimaryKey(self):
        return self.__getattribute__(self.__primaryKey__)
    
    def getRelationNameFromList(self, li):
        for na in self.__relations__:
            if li == self.__getattribute__(na):
                return na
    
    def addRelationEntry(self, li, other):
        name = self.getRelationNameFromList(li)
        tName = self.__class__.generateRelationTableName(other.__class__, name)
        mKey = self.__class__.generateRelationTableMyKey()
        oKey = self.__class__.generateRelationTableOtherKey(other.__class__)
        query = "INSERT INTO "
        query += tName
        query += " ( " + mKey
        query += ", " + oKey
        query += ") VALUES (?,?)"
        vals = [self.getPrimaryKey(), other.getPrimaryKey()]
        c = store.con.cursor()
        logger.info(query+str(vals))
        c.execute(query,vals)
        if store.policy['commitAfterInsert']:
            store.commit()
        else:
            store.dirty = True
        if 'onAddRelationEntry' in self.__callbacks__:
            self.__callbacks__['onAddRelationEntry'](self,name=name,li=li,other=other)
            
    def removeRelationEntry(self, li, other):
        name = self.getRelationNameFromList(li)
        tName = self.__class__.generateRelationTableName(other.__class__, name)
        mKey = self.__class__.generateRelationTableMyKey()
        oKey = self.__class__.generateRelationTableOtherKey(other.__class__)
        query = "DELETE FROM " + tName + " WHERE "
        query += mKey + "=? AND " + oKey + "=?"
        vals = [self.getPrimaryKey(), other.getPrimaryKey()]
        c = store.con.cursor()
        logger.info(query+str(vals))
        c.execute(query,vals)
        if store.policy['commitAfterDelete']:
            store.commit()
        else:
            store.dirty = True
        if 'onRemoveRelationEntry' in self.__callbacks__:
            self.__callbacks__['onRemoveRelationEntry'](self,name=name,li=li,other=other)

    @classmethod
    def argumentList(cls, cols, types = False, additions = False, prefix=""):
        erg = ""
        for col in cols:
        #for name,type in cls.__columns__.items():
            erg += prefix+col
            if types:
                if isclass(cls.__columns__[col]):
                    erg += " " + cls.__columns__[col].__columns__[cls.__columns__[col].__primaryKey__]
                else:
                    erg += " " + cls.__columns__[col]
            if additions and col == cls.__primaryKey__:
                erg += " NOT NULL"
            if cols.index(col) < len(cols) - 1:
                    erg += ", "
        return erg
    
    @classmethod
    def primaryKeyExists(cls, primary):
        return not cls.getByPrimaryKey(primary, True) == None

    @classmethod
    def getByPrimaryKey(cls, primary, internal = False):
        if primary is None:
            return None
        if not checkTableExistence(cls.__tableName__):
            logger.error("Table not existent: "+cls.__tableName__)
            return None
        if cache.isCached(cls, primary):
            return cache.get(cls, primary)
        erg = "SELECT * FROM " + cls.__tableName__ + " WHERE "
        erg += cls.__primaryKey__ + "=?" #+ cls.__primaryKey__
        c = store.con.cursor()
        logger.info(erg+str(primary))
        c.execute(erg,[primary])
        row = c.fetchone()
        if not row:
            if not internal:
                logger.error("Primary Key not found in Database: " + str(primary))
            return None
        res = cls(**row)
        cache.cache(res)
        return res

    @classmethod
    def getAllFromOneColumn(cls, column, value):
        query = "SELECT * FROM " + cls.__tableName__
        query += " WHERE " + column +"=?"
        c = store.con.cursor()
        logger.info(query+str(value))
        c.execute(query,[value])
        rows = c.fetchall()
        erg = []
        for row in rows:
            pk = row[cls.__primaryKey__]
            if cache.isCached(cls, pk):
                erg.append(cache.get(cls, pk))
            else:
                obj = cls(**row)
                erg.append(obj)
                cache.cache(obj)
        return erg

    @classmethod
    def getAll(cls):
        if not checkTableExistence(cls.__tableName__):
            logger.error("Table not existent: "+cls.__tableName__)
            return []
        query = "SELECT * FROM " + cls.__tableName__
        c = store.con.cursor()
        c.execute(query)
        rows = c.fetchall()
        erg = []
        for row in rows:
            primary = row[cls.__primaryKey__]
            if cache.isCached(cls, primary):
                erg.append(cache.get(cls, primary))
            else:
                new = cls(**row)
                cache.cache(new)
                erg.append(new)
        return erg

    @classmethod
    def createTable(cls):
        erg = "CREATE TABLE IF NOT EXISTS "
        erg += cls.__tableName__
        erg += " ( "
        erg += cls.argumentList(cls.__columns__.keys(), True, True)
        erg += " , "
        erg += "PRIMARY KEY "+ " ("
        erg += cls.__primaryKey__
        erg += " ) "
        erg += " ) "
        c = store.con.cursor()
        logger.info(erg)
        c.execute(erg)
        if store.policy['createCompositeOnCreate']:
            cls.createCompositeTable()

    @classmethod
    def generateRelationTableName(cls, relation, name):
        return cls.__tableName__ + name + relation.__tableName__

    @classmethod
    def generateRelationTableMyKey(cls):
        return cls.argumentList([cls.__primaryKey__], False, False, cls.__tableName__)

    @classmethod
    def generateRelationTableOtherKey(cls, relation):
        return relation.argumentList([relation.__primaryKey__], False, False, relation.__tableName__)

    @classmethod
    def createCompositeTable(cls):
        for relation,other in cls.__relations__.items():
            query = "CREATE TABLE IF NOT EXISTS "
            query += cls.generateRelationTableName(other,relation)
            query += " ( "
            query += cls.argumentList([cls.__primaryKey__], True, True, cls.__tableName__)
            query += ", "
            query += other.argumentList([other.__primaryKey__], True, True, other.__tableName__)
            query += " , PRIMARY KEY ("
            query += cls.generateRelationTableMyKey()
            query += ", "
            query += cls.generateRelationTableOtherKey(other)
            query += " )"
            query += " )"
            c = store.con.cursor()
            logger.info(query)
            c.execute(query)

    def attributeList(self, cols):
        ret = []
        for c in cols:
            if isinstance(self.__getattribute__(c),SQLiteEntity):
                ret.append(self.__getattribute__(c).getPrimaryKey())
            else:
                ret.append(self.__getattribute__(c))
        return ret

    def nonPrimaryAttributes(self):
        erg = []
        for col in self.__columns__:
            if not col == self.__primaryKey__:
                erg.append(col)
        return erg

    def attributeDict(self, cols):
        erg = {}
        for c in cols:
            if isinstance(self.__getattribute__(c),SQLiteEntity):
                erg[c] = self.__getattribute__(c).getPrimaryKey()
            else:
                erg[c] = self.__getattribute__(c)
        return erg

    def primaryKeyString(self):
        prim = self.__primaryKey__
        return prim+"=:"+prim

    def insert(self):
        if not checkTableExistence(self.__tableName__):
            logger.error("Insert into nonExistent table: " + str(self.__tableName__))
            return None
        erg = "INSERT INTO "
        erg += self.__tableName__
        erg += " ( "
        cols = self.__columns__.keys()
        erg += self.__class__.argumentList(cols)
        erg += " ) VALUES ("
        for i in range(0,len(cols)):
            erg += "?"
            if i < len(cols) - 1:
                erg += ","
        erg += ")"
        if not self.__primaryKey__ in dir(self):
            #we do not yet have a primary key
            #set a dummy
            self.__setattr__(self.__primaryKey__,None)
        vals = self.attributeList(cols)
        logger.info(erg + str(vals))
        c = store.con.cursor()
        c.execute(erg,vals)
        rowID = c.lastrowid
        if 'id' in dir(self) and not rowID == self.__getattribute__('id'):
            logger.info("Setting id of " + str(self) + " to " + str(rowID))
            self.__setattr__('id', rowID)
        if store.policy['commitAfterInsert']:
            store.commit()
        else:
            store.dirty = True
        cache.cache(self)
        if 'onInsert' in self.__callbacks__:
            self.__callbacks__['onInsert'](self,vals=vals)

    def update(self):
        erg = "UPDATE " + self.__tableName__ + " SET "
        nonPrim = self.nonPrimaryAttributes()
        for c in nonPrim:
            erg += c+"=:"+c
            if nonPrim.index(c) < len(nonPrim) - 1:
                erg+= ", "
            else:
                erg += " "
        erg += "WHERE "
        erg += self.primaryKeyString()
        vals = self.attributeDict(self.__columns__.keys())
        logger.info(erg + str(vals))
        c = store.con.cursor()
        c.execute(erg,vals)
        if store.policy['commitAfterUpdate']:
            store.commit()
        else:
            store.dirty = True
        if 'onUpdate' in self.__callbacks__:
            self.__callbacks__['onUpdate'](self,vals=vals)

    def delete(self):
        erg = "DELETE FROM " + self.__tableName__ + " WHERE " + self.primaryKeyString()
        vals = self.attributeDict([self.__primaryKey__])
        logger.info(erg + str(vals))
        c = store.con.cursor()
        c.execute(erg,vals)
        cache.unCache(self)
        if store.policy['commitAfterDelete']:
            store.commit()
        else:
            store.dirty = True
        if 'onDelete' in self.__callbacks__:
            self.__callbacks__['onDelete'](self)

    def __repr__(self):
        erg = self.__class__.__name__ +"@"+str(id(self))+ "["
        erg += self.__primaryKey__+":"+str(self.getPrimaryKey())
        #erg = erg[:-1]
        erg += "]"
        return erg
        


if __name__ == '__main__':
    print "Falche Datei oder nix gecoded... DUMMKOPP!!"
