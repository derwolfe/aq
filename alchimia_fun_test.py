from __future__ import absolute_import, division, print_function

from twisted.internet.defer import Deferred
from twisted.trial import unittest
from twisted.test import proto_helpers

from alchimia_fun import (
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
        L{alchimia_fun.setup} creates a table named C{users}
        """
        d = self.db.setup(newUsers)

        def check(_):
            result = engine.has_table('users')
            self.assertTrue(result)

        d.addCallback(check)
        return d


    def test_setupAddsNewUsers(self):
        """
        L{alchimia_fun.setup} adds a given set of users to the C{users} table.
        """
        d = self.db.setup(newUsers)

        def check(_):
            dCount = engine.execute(users.count())
            dCount.addCallback(lambda x: x.fetchone())
            dCount.addCallback(lambda x: self.assertEqual(5, x[0]))
            return dCount

        d.addCallback(check)
        return d


    def test_getUsersStartingWithReturnsEmptyList(self):
        """
        L{alchimia_fun.getUsersStartingWith} returns an empty list when no users
        are present in the database
        """
        d = self.db.setup([])

        def check(_):
            d1 = self.db.getUsersStartingWith("j")
            d1.addCallback(lambda xs: self.assertEqual([], xs))
            return d1

        d.addCallback(check)
        return d


    def test_getUsersStartingWithReturnList(self):
        """
        L{alchimia_fun.getUsersStartingWith} returns a list of the users where
        the name the starts with the given query value.
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
        L{alchimia_fun.addPerson} adds a new user record to the database
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
    An in-memory version of the database that returns
    L{twisted.internet.defer.Deferred}s.
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
                if letters in name['name'].lower():
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
        self.fakeDb = FakeDatabase()


    def test_setupAddsNewUsers(self):
        d = self.fakeDb.setup(newUsers)

        def check(_):
            self.assertTrue(5, len(self.fakeDb.names))

        d.addCallback(check)
        return d


    def test_getUsersStartingWithReturnsEmptyList(self):
        self.fakeDb.names = []
        d = self.fakeDb.getUsersStartingWith("j")
        d.addCallback(lambda xs: self.assertEqual([], xs))
        return d


    def test_getUsersStartingWithReturnList(self):
        name = u"don johnson"
        self.fakeDb.names = [{'id':1, 'name': name}]
        d = self.fakeDb.getUsersStartingWith(u"d")
        d.addCallback(lambda xs: self.assertEqual(name, xs[0]['name']))
        return d


    def test_addPersonCreatesRecord(self):
        name = u"maverick donvon"
        self.fakeDb.names = []
        d = self.fakeDb.addPerson(name)
        d.addCallback(
            lambda x: self.assertEqual(name, self.fakeDb.names[0]['name']))
        return d


class SearchCommandProtocolTests(unittest.TestCase):


    def setUp(self):
        self.db = FakeDatabase()
        self.protocol = SearchCommandProtocol(self.db)
        self.transport = proto_helpers.StringTransport()
        self.protocol.transport = self.transport


    def test_connectionMade(self):
        self.protocol.connectionMade()
        self.assertIn(
            "DB query system. Type 'help' for help.",
            self.transport.value()
        )


    def test_lineReceivedBareHelp(self):
        """
        When help is called without arguments, it returns the commands available
        to the user.
        """
        self.protocol.lineReceived('help\n')
        self.assertIn(
            "Valid commands: add find help quit",
            self.transport.value()
        )


    def test_doHelpReturns(self):
        """
        L{alchimia_fun.lineRecieived} returns the list of valid commands
        when ``help`` is received.
        """
        self.protocol.lineReceived('help\n')
        self.assertEqual(
            "Valid commands: add find help quit\n",
            self.transport.value()
        )


    def _test_returnsDocstring(self, command):
        """
        This is meant to be used a convenience method for testing the help
        function. This function asserts that the response from the help
        command is the docstring attached to the function whose help is
        being requested.
        """
        commandToExecute = 'help ' + command.__name__[3:] + '\n'
        self.protocol.lineReceived(commandToExecute)
        self.assertIn(command.__doc__, self.transport.value())


    def test_doHelpAdd(self):
        """
        L{alchimia_fun.SearchCommandProtocol.lineReceieved} returns the
        docstring attached to the
        L{alchimia_fun.SearchCommandProtocol.do_add}
        """
        self._test_returnsDocstring(self.protocol.do_add)


    def test_doHelpFind(self):
        """
        L{alchimia_fun.SearchCommandProtocol.lineReceieved} returns the
        docstring attached to the
        L{alchimia_fun.SearchCommandProtocol.do_find}
        """
        self._test_returnsDocstring(self.protocol.do_find)


    def test_doHelpHelp(self):
        """
        L{alchimia_fun.SearchCommandProtocol.lineReceieved} returns the
        docstring attached to the
        L{alchimia_fun.SearchCommandProtocol.do_help}
        """
        self._test_returnsDocstring(self.protocol.do_help)


    def test_doHelpQuit(self):
        """
        L{alchimia_fun.SearchCommandProtocol.lineReceieved} returns the
        docstring attached to the
        L{alchimia_fun.SearchCommandProtocol.do_quit}
        """
        self._test_returnsDocstring(self.protocol.do_quit)

    def test_lineReceivedIgnoreBlank(self):
        self.protocol.lineReceived("")
        self.assertEqual("", self.transport.value())

        self.protocol.lineReceived("\n")
        self.assertEqual("", self.transport.value())

        self.protocol.lineReceived("       \n")
        self.assertEqual("", self.transport.value())

    def test_lineReceivedBadInput(self):
        """
        On bad input, L{alchimia_fun.SearchCommandProtocol.lineReceived} returns
        an error message
        """
        self.protocol.lineReceived(" .... 23   \n")
        self.assertEqual("Error: no such command.\n", self.transport.value())

    def test_doQuitSendsGoodbye(self):
        self.protocol.do_quit()
        self.assertIn("Goodbye.", self.transport.value())

    def test_doQuitKillsReactor(self):
        self.protocol.do_quit()
        self.fail()

    # db tests
    def test_doAddAddsPerson(self):
        name = u"don johnson"
        first, last = name.split(' ')
        self.assertEqual([], self.db.names)
        self.protocol.do_add(first, last)
        self.assertIn(name.title(), self.transport.value())
        self.assertEqual(1, len(self.db.names))

    def test_doFindFindsPerson(self):
        name = u"don johnson"
        first, last = name.split(' ')
        self.db.names = [self.db._makeRecord(name)]

        self.protocol.do_find('d')
        self.assertIn(name, self.transport.value())

        self.protocol.do_find('don johnson')
        self.assertIn(name, self.transport.value())

    def test_doFindResults(self):
        name = u"don johnson"
        first, last = name.split(' ')
        self.protocol.do_find('d')
        self.assertIn("No results", self.transport.value())
