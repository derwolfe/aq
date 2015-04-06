from __future__ import absolute_import, division, print_function

from alchimia import TWISTED_STRATEGY

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine
)
from sqlalchemy.schema import CreateTable

from twisted.internet import reactor, stdio
from twisted.protocols import basic

from zope.interface import Interface, implementer

# db setup, how to make this readonly?
connectionString = 'sqlite://'
engine = create_engine(
    connectionString, reactor=reactor, strategy=TWISTED_STRATEGY
)
metadata = MetaData()
users = Table("users", metadata,
              Column("id", Integer(), primary_key=True),
              Column("name", String())
              )

newUsers = [
    dict(name="Jeremy Goodwin"),
    dict(name="Natalie Hurley"),
    dict(name="Dan Rydell"),
    dict(name="Casey McCall"),
    dict(name="Dana Whitaker")
]


class IDatabase(Interface):

    def setup(newUsers):
        """
        Setup creates a the database table and seeds it with the L{newUsers}.

        @param newUsers: a list of dictionaries with a L{name} key.

        @return: a deferred object that fires once the table has been created
            and seeded with data.
        """

    def getUsersStartingWith(letters):
        """
        Return users whose name starts with L{letters}

        @param letters: the string to search
        @type letters: a string

        @return: a list of results containing the database rows. In the format:
            "id, u"name""
        """

    def addPerson(name, plop):
        """
        Add a new person to the database with the given L{name}.

        @param name: the new to use
        @type name: a string
        """


@implementer(IDatabase)
class Database(object):

    def setup(self, newUsers=newUsers):
        d = engine.execute(CreateTable(users))

        def addUsers(_ignored):
            if newUsers:
                return engine.execute(users.insert().values(newUsers))

        d.addCallback(addUsers)
        return d

    def getUsersStartingWith(self, queryLetter):
        d = engine.execute(
            users.select(users.c.name.startswith(queryLetter))
        )
        d.addCallback(lambda x: x.fetchall())
        return d

    def addPerson(self, name):
        return engine.execute(
            users.insert().values(dict(name=name))
        )


class SearchCommandProtocol(basic.LineReceiver, object):

    delimiter = '\n'

    def __init__(self, database):
        self.database = database

    def connectionMade(self):
        self.sendLine("DB query system. Type 'help' for help.")

    def lineReceived(self, line):
        # Ignore blank lines
        if not line:
            return

        # Parse the command
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]

        # Dispatch the command to the appropriate method.  Note that all you
        # need to do to implement a new command is add another do_* method.
        try:
            method = getattr(self, 'do_' + command)
        except AttributeError, e:
            self.sendLine('Error: no such command.')
        else:
            try:
                method(*args)
            except Exception, e:
                self.sendLine('Error: ' + str(e))

    def do_help(self, command=None):
        """
        help [command]: List commands, or show help on the given command
        """
        if command:
            self.sendLine(getattr(self, 'do_' + command).__doc__)
        else:
            commands = [cmd[3:] for cmd in dir(self) if cmd.startswith('do_')]
            self.sendLine("Valid commands: " + " ".join(commands))

    def do_quit(self):
        """
        quit: Quit this session
        """
        self.sendLine('Goodbye.')
        self.transport.loseConnection()

    def do_find(self, startsWith):
        """
        find <letter>: Find all of the names starting with the given letter
        """
        self.database.getUsersStartingWith(startsWith).addCallback(
            self._checkSuccess).addErrback(
            self._checkFailure)

    def do_add(self, first, last):
        """
        add <name>: Add a new name to the system
        """
        name = "%s %s" % (first, last)
        self.database.addPerson(name.title()).addCallback(
            lambda _: self.do_find(name))

    def _checkSuccess(self, results):
        if not results:
            self.sendLine("No results")
        else:
            self._sendSeperator()
            for result in results:
                formatted = "%d - %s" % (
                    result['id'],
                    result['name'].encode('utf-8')
                )
                self.sendLine(formatted)
            self._sendSeperator()

    def _sendSeperator(self, bufferText="-" * 10):
        self.sendLine(bufferText)

    def _checkFailure(self, failure):
        self.sendLine("Failure: " + failure.getErrorMessage())

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        reactor.stop()


if __name__ == "__main__":
    database = Database()
    database.setup().addCallback(
        lambda _: stdio.StandardIO(SearchCommandProtocol(database=database)))
    reactor.run()
