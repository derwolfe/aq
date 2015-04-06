from __future__ import print_function, absolute_import, division

from twisted.trial import unittest
from alchemia_fun import (
    Database,
    SearchCommandProtocol,
    connectionString,
    engine,
    metadata,
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
            return self.db.getUsersStartingWith("j")

        def res(xs):
            self.assertEqual([], xs)

        d.addCallback(check)
        d.addCallback(res)
        return d

    def test_getUsersStartdWithReturnList(self):
        """
        getUsersStartingWith returns a list of the users where the name the
        starts with the given query value.
        """
        name = u"don johnson"
        d = self.db.setup([dict(name=name)])

        def check(_):
            return self.db.getUsersStartingWith("d")

        def res(xs):
            self.assertEqual(name, xs[0][1])

        d.addCallback(check)
        d.addCallback(res)
        return d
