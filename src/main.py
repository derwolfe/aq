from __future__ import print_function

from alchimia import TWISTED_STRATEGY

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String
)
from sqlalchemy.schema import CreateTable

from twisted.internet import reactor, defer
from twisted.internet.task import react

from twisted.python.filepath import FilePath


Engine = create_engine(
        "sqlite://", reactor=reactor, strategy=TWISTED_STRATEGY
)
Metadata = MetaData(Engine)
Users = Table("users", Metadata,
              Column("id", Integer(), primary_key=True),
              Column("name", String()),
              keep_existing=True
        )

def setupDb(_engine):
    return _engine.execute(CreateTable(Users))

def addUsers(result, _engine):
    newUsers = [
        dict(name="Jeremy Goodwin"),
        dict(name="Natalie Hurley"),
        dict(name="Dan Rydell"),
        dict(name="Casey McCall"),
        dict(name="Dana Whitaker")
    ]
    return _engine.execute(Users.insert().values(newUsers))


def getUsersStartingWith(_result, _engine, queryLetter):
    d = _engine.execute(
        Users.select(Users.c.name.startswith(queryLetter))
    )
    def realize(results):
        return results.fetchall()
    d.addCallback(realize)
    return d


def printResults(users):
    if users:
        for user in users:
            print("Username: %s" % user[Users.c.name])
    else:
        print("Nobody home")


def main(reactor):
    d = setupDb(Engine)
    d.addCallback(addUsers, _engine=Engine)
    d.addCallback(getUsersStartingWith, _engine=Engine, queryLetter="j")
    d.addCallback(printResults)
    return d


if __name__ == "__main__":
    react(main, [])
