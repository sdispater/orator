.. _BasicUsage:

Basic Usage
===========

Configuration
-------------

All you need to get you started is the configuration describing your database connections
and passing it to a ``DatabaseManager`` instance.

.. code-block:: python

    from orator import DatabaseManager

    config = {
        'mysql': {
            'driver': 'mysql',
            'host': 'localhost',
            'database': 'database',
            'user': 'root',
            'password': '',
            'prefix': ''
        }
    }

    db = DatabaseManager(config)


If you have multiple databases configured you can specify which one is the default:

.. code-block:: python

    config = {
        'default': 'mysql',
        'mysql': {
            'driver': 'mysql',
            'host': 'localhost',
            'database': 'database',
            'user': 'root',
            'password': '',
            'prefix': ''
        }
    }

.. _read_write_connections:

Read / Write connections
------------------------

Sometimes you may wish to use one database connection for SELECT statements,
and another for INSERT, UPDATE, and DELETE statements. Orator makes this easy,
and the proper connections will always be used whether you use raw queries, the query
builder or the actual ORM

Here is an example of how read / write connections should be configured:

.. code-block:: python

    config = {
        'mysql': {
            'read': [
                'host': '192.168.1.1'
            ],
            'write': [
                'host': '192.168.1.2'
            ],
            'driver': 'mysql',
            'database': 'database',
            'username': 'root',
            'password': '',
            'prefix': ''
        }
    }

Note that two keys have been added to the configuration dictionary: ``read`` and ``write``.
Both of these keys have dictionary values containing a single key: ``host``.
The rest of the database options for the ``read`` and ``write`` connections
will be merged from the main ``mysql`` dictionary. So, you only need to place items
in the ``read`` and ``write`` dictionaries if you wish to override the values in the main dictionary.
So, in this case, ``192.168.1.1`` will be used as the "read" connection, while ``192.168.1.2``
will be used as the "write" connection. The database credentials, prefix, character set,
and all other options in the main ``mysql`` dictionary will be shared across both connections.

Running queries
---------------

Once you have configured your database connection, you can run queries.


Running a select query
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    results = db.select('select * from users where id = ?', [1])

The ``select`` method will always return a list of results.

Running an insert statement
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.insert('insert into users (id, name) values (?, ?)', [1, 'John'])

Running an update statement
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.update('update users set votes = 100 where name = ?', ['John'])

Running a delete statement
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.delete('delete from users')


.. note::

    The ``update`` and ``delete`` statements return the number of rows affected by the operation.

Running a general statement
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.statement('drop table users')


Database transactions
---------------------

To run a set of operations within a database transaction, you can use the ``transaction`` method
which is a context manager:

.. code-block:: python

    with db.transaction():
        db.table('users').update({votes: 1})
        db.table('posts').delete()

.. note::

    Any exception thrown within a transaction block will cause the transaction to be rolled back
    automatically.

Sometimes you may need to start a transaction yourself:

.. code-block:: python

    db.begin_transaction()

You can rollback a transaction with the ``rollback`` method:

.. code-block:: python

    db.rollback()

You can also commit a transaction via the ``commit`` method:

.. code-block:: python

    db.commit()


.. warning::

    By default, all underlying DBAPI connections are set to be in autocommit mode
    meaning that you don't need to explicitly commit after each operation.


Accessing connections
---------------------

When using multiple connections, you can access them via the ``connection()`` method:

.. code-block:: python

    users = db.connection('foo').table('users').get()

You also can access the raw, underlying dbapi connection instance:

.. code-block:: python

    db.connection().get_connection()

Sometimes, you may need to reconnect to a given database:

.. code-block:: python

    db.reconnect('foo')

If you need to disconnect from the given database, use the ``disconnect`` method:

.. code-block:: python

    db.disconnect('foo')


Query logging
-------------

Orator can log all queries that are executed.
By default, this is turned off to avoid unnecessary overhead, but if you want to activate it
you can either add a ``log_queries`` key to the config dictionary:

.. code-block:: python

    config = {
        'mysql': {
            'driver': 'mysql',
            'host': 'localhost',
            'database': 'database',
            'username': 'root',
            'password': '',
            'prefix': '',
            'log_queries': True
        }
    }

or activate it later on:

.. code-block:: python

    db.connection().enable_query_log()

Now, the logger ``orator.connection.queries`` will be logging queries at **debug** level:

.. code-block:: text

    Executed SELECT COUNT(*) AS aggregate FROM "users" in 1.18ms

    Executed INSERT INTO "users" ("email", "name", "updated_at") VALUES ('foo@bar.com', 'foo', '2015-04-01T22:59:25.810216'::timestamp) RETURNING "id" in 3.6ms

.. note::

    These log messages above are those logged for **MySQL** and **PostgreSQL** connections which support
    displaying full request sent to the database.
    For **SQLite** connections, the format is as follows:

    .. code-block:: text

        Executed ('SELECT COUNT(*) AS aggregate FROM "users"', []) in 0.12ms


Customizing log messages
~~~~~~~~~~~~~~~~~~~~~~~~

Each log record sent by the logger comes with the ``query`` and ``elapsed_time`` keywords so that
you can customize the log message:

.. code-block:: python

    import logging

    logger = logging.getLogger('orator.connection.queries')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        'It took %(elapsed_time)sms to execute the query %(query)s'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
