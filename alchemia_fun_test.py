from __future__ import print_function, absolute_import, division

from twisted.trial import unittest

from alchemia_fun import (
    Database,
    SearchCommandProtocol,
    engine,
    users,
    newUsers
)


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = Database()

    def test_setupCreatesUsersTable(self):
        """
        setup creates a table named 'users'
        """
        d = self.db.setup(newUsers)

        def check(_):
            result = engine.has_table('users')
            self.assertTrue(result)

        d.addCallback(check)
        return d

    def test_setupAddsNewUsers(self):
        """
        Users are added to the database.
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
        getUsersStartingWith returns an empty list when no users
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
        getUsersStartingWith returns a list of the users where the name the
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
        `addPerson` adds a new user record to the database
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
