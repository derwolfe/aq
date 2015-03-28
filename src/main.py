from alchimia import TWISTED_STRATEGY

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String
)
from sqlalchemy.schema import CreateTable

from twisted.internet import reactor, defer
#from twisted.internet.task import react


def buildEngine(reactor):
    return create_engine(
        "sqlite://", reactor=reactor, strategy=TWISTED_STRATEGY
    )


def setupDb(_engine):
    metadata = MetaData()
    users = Table("users", metadata,
        Column("id", Integer(), primary_key=True),
        Column("name", String()),
    )
    return _engine.execute(CreateTable(users))


def addUsers(_engine):
    ds = defer.DeferredList([
        _engine.execute(users.insert().values(name="Jeremy Goodwin")),
        _engine.execute(users.insert().values(name="Natalie Hurley")),
        _engine.execute(users.insert().values(name="Dan Rydell")),
        _engine.execute(users.insert().values(name="Casey McCall")),
        _engine.execute(users.insert().values(name="Dana Whitaker"))
    ], consumeErrors=False)
    return ds

def getDUsers(_engine):
    deferredResult = engine.execute(users.select(users.c.name.startswith("D")))
    def realize(results):
        return results.fetchall()
    deferredResult.addCallback(realize)

def printResults(users):
    # Print out the users
    for user in d_users:
        print "Username: %s" % user[users.c.name]

def main(reactor):
    engine = buildEngine(reactor=reactor)
    d = setupDb(engine)
    d.addCallback(addUsers, engine)
    d.addCallback(getDUsers, engine)
    d.addCallback(printResults)

if __name__ == "__main__":
    main(reactor)
    reactor.run()
    #react(main, [])
