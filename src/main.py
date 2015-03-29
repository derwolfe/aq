from __future__ import print_function

from alchimia import TWISTED_STRATEGY

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String
)
from sqlalchemy.schema import CreateTable

from twisted.internet import reactor, defer, stdio
from twisted.internet.task import react

from twisted.python.filepath import FilePath
from twisted.protocols import basic


class Database(object):

    def __init__(self, reactor):
        self.engine = create_engine(
            "sqlite://", reactor=reactor, strategy=TWISTED_STRATEGY
        )
        self.metadata = MetaData(self.engine)
        self.users = Table("users",
                           self.metadata,
                           Column("id", Integer(), primary_key=True),
                           Column("name", String())
                       )

    def setupDb(self):
        d = self.engine.execute(CreateTable(self.users))
        def addUsers(_ignored):
            newUsers = [
                dict(name="Jeremy Goodwin"),
                dict(name="Natalie Hurley"),
                dict(name="Dan Rydell"),
                dict(name="Casey McCall"),
                dict(name="Dana Whitaker")
            ]
            return self.engine.execute(self.users.insert().values(newUsers))
        d.addCallback(addUsers)
        return d

    def getUsersStartingWith(self, queryLetter):
        d = self.engine.execute(
            self.users.select(self.users.c.name.startswith(queryLetter))
        )
        def realize(results):
            return results.fetchall()
        d.addCallback(realize)
        return d


class SearchCommandProtocol(basic.LineReceiver, object):

    delimiter = '\n' # unix terminal style newlines. remove this line
                     # for use with Telnet

    def __init__(self, Db):
        self.Db = Db
        #super(basic.LineReceiver, self).__init__()

    def connectionMade(self):
        self.sendLine("DB query system. Type 'help' for help.")

    def lineReceived(self, line):
        # Ignore blank lines
        if not line: return

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
            self.sendLine("Valid commands: " +" ".join(commands))

    def do_quit(self):
        """
        quit: Quit this session
        """
        self.sendLine('Goodbye.')
        self.transport.loseConnection()

    def do_find(self, startsWith):
        """
        Find <letter>: Find all of the names starting with the given letter
        """
        self.Db.getUsersStartingWith(startsWith).addCallback(
            self._checkSuccess).addErrback(
            self._checkFailure)

    def _checkSuccess(self, results):
        if not results:
            self.sendLine("No results")
        else:
            self._sendSeperator()
            column = self.Db.users.c.name
            for result in results:
                self.sendLine("%s" %(result[column].encode('utf-8'),))
            self._sendSeperator()

    def _sendSeperator(self, bufferText = "-"*10):
        self.sendLine(bufferText)

    def _checkFailure(self, failure):
         self.sendLine("Failure: " + failure.getErrorMessage())

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        reactor.stop()


if __name__ == "__main__":
    database = Database(reactor)
    database.setupDb()
    stdio.StandardIO(SearchCommandProtocol(Db=database))
    reactor.run()
