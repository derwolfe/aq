from __future__ import absolute_import, division, print_function

from twisted.trial import unittest
from twisted.internet.defer import Deferred

from alchemia_fun import (
    Database,
    IDatabase,
    SearchCommandProtocol,
    engine,
    newUsers,
    users
)

from zope.interface import Interface, implementer, verify


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = Database()


    def test_setupCreatesUsersTable(self):
        """
        L{setup} creates a table named C{users}
        """
        d = self.db.setup(newUsers)

        def check(_):
            result = engine.has_table('users')
            self.assertTrue(result)

        d.addCallback(check)
        return d


    def test_setupAddsNewUsers(self):
        """
        L{setup} adds a given set of users to the C{users} table.
        """
        d = self.db.setup(newUsers)

        def check(_):
            dCount = engine.execute(users.count())
            dCount.addCallback(lambda x: x.fetchone())
            dCount.addCallback(lambda x: self.assertEqual(5, x[0]))
            return dCount

        d.addCallback(check)
        return d


    def test_getUsersStartedWithReturnsEmptyList(self):
        """
        L{getUsersStartingWith} returns an empty list when no users
        are present in the database
        """
        d = self.db.setup([])

        def check(_):
            d1 = self.db.getUsersStartingWith("j")
            d1.addCallback(lambda xs: self.assertEqual([], xs))
            return d1

        d.addCallback(check)
        return d


    def test_getUsersStartdWithReturnList(self):
        """
        L{getUsersStartingWith} returns a list of the users where the name the
        starts with the given query value.
        """
        name = u"don johnson"
        d = self.db.setup([dict(name=name)])

        def check(_):
            d1 = self.db.getUsersStartingWith("d")
            d1.addCallback(lambda xs: self.assertEqual(name, xs[0]["name"]))
            return d1

        d.addCallback(check)
        return d


    def test_addPersonCreatesRecord(self):
        """
        L{addPerson} adds a new user record to the database
        """
        name = u"maverick donvon"
        d = self.db.setup([])

        def add(_):
            return self.db.addPerson(name)

        def check(xs):
            d1 = engine.execute(users.select(users))
            d1.addCallback(lambda x: x.fetchone())
            d1.addCallback(lambda x: self.assertEqual(name, x["name"]))
            return d1

        d.addCallback(add)
        d.addCallback(check)
        return d

@implementer(IDatabase)
class FakeDatabase(object):

    """
    This is a simple, in memory version of the database that returns
    L{deferreds}.
    """

    def __init__(self):
        self.idNumber = 1
        self.names = []

    def _makeRecord(self, name):
        self.idNumber = id = self.idNumber + 1
        return dict(id=self.idNumber, name=unicode(name))

    def setup(self, names):
        d = Deferred()

        def add(names):
            for name in names:
                self.names.append(self._makeRecord(name))

        d.addCallback(add)
        d.callback(names)
        return d


    def getUsersStartingWith(self, letters):
        d = Deferred()

        def find(_):
            toReturn = []
            for name in self.names:
                if letters in name:
                    toReturn.append(name)
            return toReturn

        d.addCallback(find)
        d.callback(letters)

        return d

    def addPerson(self, name):
        d = Deferred()

        def add(name):
            self.names.append(self._makeRecord(name))

        d.addCallback(add)
        d.callback(name)
        return d


verify.verifyObject(IDatabase, FakeDatabase())

class VerifyFakeDb(unittest.TestCase):
    """
    The fake should have behaviour that mirrors the actual database
    """

    def setUp(self):
        self.realDb = Database()
        self.fakeDb = FakeDatabase()


    def test_setupAddsNewUsers(self):
        d = self.fakeDb.setup(newUsers)

        def check(_):
            self.assertTrue(5, len(self.fakeDb.names))

        d.addCallback(check)
        return d


    def test_getUsersStartedWithReturnsEmptyList(self):

        d = self.fakeDb.setup([])

        def check(_):
            d1 = self.fakeDb.getUsersStartingWith("j")
            d1.addCallback(lambda xs: self.assertEqual([], xs))
            return d1

        d.addCallback(check)
        return d


    def test_getUsersStartdWithReturnList(self):
        name = u"don johnson"
        d = self.fakeDb.setup([dict(name=name)])

        def check(_):
            d1 = self.fakeDb.getUsersStartingWith("d")
            d1.addCallback(lambda xs: self.assertEqual(name, xs[0]["name"]))
            return d1

        d.addCallback(check)
        return d


    def test_addPersonCreatesRecord(self):
        """
        L{addPerson} adds a new user record to the database
        """
        name = u"maverick donvon"
        d = self.fakeDb.setup([])

        def add(_):
            return self.fakeDb.addPerson(name)

        d.addCallback(add)
        d.addCallback(lambda x: self.assertEqual(name, x["name"]))
        return d



#class SearchCommandProtocolTests(unittest.TestCase):
#    def setUp(self):
#        self.protocol = SearchCommandProtocol(
