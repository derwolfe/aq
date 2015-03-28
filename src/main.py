from alchimia import TWISTED_STRATEGY

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String
)
from sqlalchemy.schema import CreateTable

from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import react


@inlineCallbacks
def main(reactor):
    engine = create_engine(
        "sqlite://", reactor=reactor, strategy=TWISTED_STRATEGY
    )

    metadata = MetaData()
    users = Table("users", metadata,
        Column("id", Integer(), primary_key=True),
        Column("name", String()),
    )

    # Create the table
    yield engine.execute(CreateTable(users))

    # Insert some users
    yield engine.execute(users.insert().values(name="Jeremy Goodwin"))
    yield engine.execute(users.insert().values(name="Natalie Hurley"))
    yield engine.execute(users.insert().values(name="Dan Rydell"))
    yield engine.execute(users.insert().values(name="Casey McCall"))
    yield engine.execute(users.insert().values(name="Dana Whitaker"))

    result = yield engine.execute(users.select(users.c.name.startswith("D")))
    d_users = yield result.fetchall()
    # Print out the users
    for user in d_users:
        print "Username: %s" % user[users.c.name]

if __name__ == "__main__":
    react(main, [])