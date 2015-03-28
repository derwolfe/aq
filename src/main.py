from __future__ import print_function

from alchimia import TWISTED_STRATEGY

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String
)
from sqlalchemy.schema import CreateTable

from twisted.internet import reactor, defer
from twisted.internet.task import react


Engine = create_engine(
        "sqlite://", reactor=reactor, strategy=TWISTED_STRATEGY
)
Metadata = MetaData(Engine)
Users = Table("users", Metadata,
            Column("id", Integer(), primary_key=True),
            Column("name", String()),
        )


def setupDb(_engine):
    d = _engine.execute(CreateTable(Users))
    def exists(ignored):
        print("exists?")
    d.addCallback(exists)
    return d

def addUsers(result, _engine):
    newUsers = [
        dict(name="Jeremy Goodwin"),
        dict(name="Natalie Hurley"),
        dict(name="Dan Rydell"),
        dict(name="Casey McCall"),
        dict(name="Dana Whitaker")
    ]
    return _engine.execute(Users.insert().values(newUsers))

def getDUsers(_result, _engine):
    d = _engine.execute(
        Users.select(Users.c.name.startswith("D"))
    )
    def realize(results):
        return results.fetchall()
    d.addCallback(realize)
    return d

def printResults(users):
    for user in users:
        print("Username: %s" % user[Users.c.name])

def main(reactor):
    d = setupDb(Engine)
    d.addCallback(addUsers, _engine=Engine)
    d.addCallback(getDUsers, _engine=Engine)
    d.addCallback(printResults)
    return d


if __name__ == "__main__":
    #main(reactor)
    #reactor.run()
    react(main, [])
