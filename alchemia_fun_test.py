from __future__ import print_function, absolute_import, division

from twisted.trial import unittest
from alchemia_fun import (
    Database,
    SearchCommandProtocol,
    connectionString,
    engine,
    metadata,
    users
)

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = Database()

    def test_setupCreatesUsersTable(self):
        """
        setup creates a table named 'users'
        """
        d = self.db.setup()
        def check(_):
            result = engine.has_table('users')
            self.assertTrue(result)
        d.addCallback(check)
        return d


    def test_setupAddsNewUsers(self):
        """
        Users are added to the database.
        """

        self.fail()
