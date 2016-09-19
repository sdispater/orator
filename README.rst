Orator
######

.. image:: https://travis-ci.org/sdispater/orator.png
   :alt: Orator Build status
   :target: https://travis-ci.org/sdispater/orator

The Orator ORM provides a simple yet beautiful ActiveRecord implementation.

It is inspired by the database part of the `Laravel framework <http://laravel.com>`_,
but largely modified to be more pythonic.

The full documentation is available here: http://orator-orm.com/docs


Installation
============

You can install Orator in 2 different ways:

* The easier and more straightforward is to use pip

.. code-block:: bash

    pip install orator

* Install from source using the official repository (https://github.com/sdispater/orator)

The different dbapi packages are not part of the package dependencies,
so you must install them in order to connect to corresponding databases:

* Postgres: ``psycopg2``
* MySQL: ``PyMySQL`` or ``mysqlclient``
* Sqlite: The ``sqlite3`` module is bundled with Python by default


Basic Usage
===========

Configuration
-------------

All you need to get you started is the configuration describing your database connections
and passing it to a ``DatabaseManager`` instance.

.. code-block:: python

    from orator import DatabaseManager, Model

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
    Model.set_connection_resolver(db)


Defining a model
----------------

.. code-block:: python

    class User(Model):
        pass

Note that we did not tell the ORM which table to use for the ``User`` model. The plural "snake case" name of the
class name will be used as the table name unless another name is explicitly specified.
In this case, the ORM will assume the ``User`` model stores records in the ``users`` table.
You can specify a custom table by defining a ``__table__`` property on your model:

.. code-block:: python

    class User(Model):

        __table__ = 'my_users'

The ORM will also assume that each table has a primary key column named ``id``.
You can define a ``__primary_key__`` property to override this convention.
Likewise, you can define a ``__connection__`` property to override the name of the database
connection that should be used when using the model.

Once a model is defined, you are ready to start retrieving and creating records in your table.
Note that you will need to place ``updated_at`` and ``created_at`` columns on your table by default.
If you do not wish to have these columns automatically maintained,
set the ``__timestamps__`` property on your model to ``False``.


Retrieving all models
---------------------

.. code-block:: python

    users = User.all()


Retrieving a record by primary key
----------------------------------

.. code-block:: python

    user = User.find(1)

    print(user.name)


Querying using models
---------------------

.. code-block:: python

    users = User.where('votes', '>', 100).take(10).get()

    for user in users:
        print(user.name)


Aggregates
----------

You can also use the query builder aggregate functions:

.. code-block:: python

    count = User.where('votes', '>', 100).count()

If you feel limited by the builder's fluent interface, you can use the ``where_raw`` method:

.. code-block:: python

    users = User.where_raw('age > ? and votes = 100', [25]).get()


Chunking Results
----------------

If you need to process a lot of records, you can use the ``chunk`` method to avoid
consuming a lot of RAM:

.. code-block:: python

    for users in User.chunk(100):
        for user in users:
            # ...


Specifying the query connection
-------------------------------

You can specify which database connection to use when querying a model by using the ``on`` method:

.. code-block:: python

    user = User.on('connection-name').find(1)

If you are using read / write connections, you can force the query to use the "write" connection
with the following method:

.. code-block:: python

    user = User.on_write_connection().find(1)


Mass assignment
===============

When creating a new model, you pass attributes to the model constructor.
These attributes are then assigned to the model via mass-assignment.
Though convenient, this can be a serious security concern when passing user input into a model,
since the user is then free to modify **any** and **all** of the model's attributes.
For this reason, all models protect against mass-assignment by default.

To get started, set the ``__fillable__`` or ``__guarded__`` properties on your model.


Defining fillable attributes on a model
---------------------------------------

The ``__fillable__`` property specifies which attributes can be mass-assigned.

.. code-block:: python

    class User(Model):

        __fillable__ = ['first_name', 'last_name', 'email']


Defining guarded attributes on a model
--------------------------------------

The ``__guarded__`` is the inverse and acts as "blacklist".

.. code-block:: python

    class User(Model):

        __guarded__ = ['id', 'password']


You can also block **all** attributes from mass-assignment:

.. code-block:: python

    __guarded__ = ['*']


Insert, update and delete
=========================


Saving a new model
------------------

To create a new record in the database, simply create a new model instance and call the ``save`` method.

.. code-block:: python

    user = User()

    user.name = 'John'

    user.save()

You can also use the ``create`` method to save a model in a single line, but you will need to specify
either the ``__fillable__`` or ``__guarded__`` property on the model since all models are protected against
mass-assignment by default.

After saving or creating a new model with auto-incrementing IDs, you can retrieve the ID by accessing
the object's ``id`` attribute:

.. code-block:: python

    inserted_id = user.id


Using the create method
-----------------------

.. code-block:: python

    # Create a new user in the database
    user = User.create(name='John')

    # Retrieve the user by attributes, or create it if it does not exist
    user = User.first_or_create(name='John')

    # Retrieve the user by attributes, or instantiate it if it does not exist
    user = User.first_or_new(name='John')


Updating a retrieved model
--------------------------

.. code-block:: python

    user = User.find(1)

    user.name = 'Foo'

    user.save()

You can also run updates as queries against a set of models:

.. code-block:: python

    affected_rows = User.where('votes', '>', 100).update(status=2)

..
    TODO: push method


Deleting an existing model
--------------------------

To delete a model, simply call the ``delete`` model:

.. code-block:: python

    user = User.find(1)

    user.delete()


Deleting an existing model by key
---------------------------------

.. code-block:: python

    User.destroy(1)

    User.destroy(1, 2, 3)

You can also run a delete query on a set of models:

.. code-block:: python

    affected_rows = User.where('votes', '>' 100).delete()


Updating only the model's timestamps
------------------------------------

If you want to only update the timestamps on a model, you can use the ``touch`` method:

.. code-block:: python

    user.touch()


Timestamps
==========

By default, the ORM will maintain the ``created_at`` and ``updated_at`` columns on your database table
automatically. Simply add these ``timestamp`` columns to your table. If you do not wish for the ORM to maintain
these columns, just add the ``__timestamps__`` property:

.. code-block:: python

    class User(Model):

        __timestamps__ = False


Providing a custom timestamp format
-----------------------------------

If you wish to customize the format of your timestamps (the default is the ISO Format) that will be returned when using the ``to_dict``
or the ``to_json`` methods, you can override the ``get_date_format`` method:

.. code-block:: python

    class User(Model):

        def get_date_format():
            return 'DD-MM-YY'


Converting to dictionaries / JSON
=================================

Converting a model to a dictionary
----------------------------------

When building JSON APIs, you may often need to convert your models and relationships to dictionaries or JSON.
So, Orator includes methods for doing so. To convert a model and its loaded relationship to a dictionary,
you may use the ``to_dict`` method:

.. code-block:: python

    user = User.with_('roles').first()

    return user.to_dict()

Note that entire collections of models can also be converted to dictionaries:

.. code-block:: python

    return User.all().serailize()


Converting a model to JSON
--------------------------

To convert a model to JSON, you can use the ``to_json`` method!

.. code-block:: python

    return User.find(1).to_json()


Query Builder
=============


Introduction
------------

The database query builder provides a fluent interface to create and run database queries.
It can be used to perform most database operations in your application, and works on all supported database systems.


Selects
-------

Retrieving all row from a table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').get()

    for user in users:
        print(user['name'])


Chunking results from a table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    for users in db.table('users').chunk(100):
        for user in users:
            # ...


Retrieving a single row from a table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    user = db.table('users').where('name', 'John').first()
    print(user['name'])

Retrieving a single column from a row
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    user = db.table('users').where('name', 'John').pluck('name')

Retrieving a list of column values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    roles = db.table('roles').lists('title')

This method will return a list of role titles. It can return a dictionary
if you pass an extra key parameter.

.. code-block:: python

    roles = db.table('roles').lists('title', 'name')

Specifying a select clause
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').select('name', 'email').get()

    users = db.table('users').distinct().get()

    users = db.table('users').select('name as user_name').get()

Adding a select clause to an existing query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    query = db.table('users').select('name')

    users = query.add_select('age').get()

Using where operators
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').where('age', '>', 25).get()

Or statements
~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').where('age', '>', 25).or_where('name', 'John').get()

Using Where Between
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').where_between('age', [25, 35]).get()

Using Where Not Between
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').where_not_between('age', [25, 35]).get()

Using Where In
~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').where_in('id', [1, 2, 3]).get()

    users = db.table('users').where_not_in('id', [1, 2, 3]).get()

Using Where Null to find records with null values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').where_null('updated_at').get()

Order by, group by and having
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    query = db.table('users').order_by('name', 'desc')
    query = query.group_by('count')
    query = query.having('count', '>', 100)

    users = query.get()

Offset and limit
~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').skip(10).take(5).get()

    users = db.table('users').offset(10).limit(5).get()


Joins
-----

The query builder can also be used to write join statements.

Basic join statement
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users') \
        .join('contacts', 'users.id', '=', 'contacts.user_id') \
        .join('orders', 'users.id', '=', 'orders.user_id') \
        .select('users.id', 'contacts.phone', 'orders.price') \
        .get()

Left join statement
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').left_join('posts', 'users.id', '=', 'posts.user_id').get()

You can also specify more advance join clauses:

.. code-block:: python

    clause = JoinClause('contacts').on('users.id', '=', 'contacts.user_id').or_on(...)

    db.table('users').join(clause).get()

If you would like to use a "where" style clause on your joins,
you may use the ``where`` and ``or_where`` methods on a join.
Instead of comparing two columns, these methods will compare the column against a value:


.. code-block:: python

    clause = JoinClause('contacts').on('users.id', '=', 'contacts.user_id').where('contacts.user_id', '>', 5)

    db.table('users').join(clause).get()


Advanced where
--------------

Sometimes you may need to create more advanced where clauses such as "where exists" or nested parameter groupings.
It is pretty easy to do with the Orator query builder

Parameter grouping
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users') \
        .where('name', '=', 'John') \
        .or_where(
            db.query().where('votes', '>', 100).where('title', '!=', 'admin')
        ).get()

The query above will produce the following SQL:

.. code-block:: sql

    SELECT * FROM users WHERE name = 'John' OR (votes > 100 AND title != 'Admin')

Exists statement
~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').where_exists(
        db.table('orders').select(db.raw(1)).where_raw('order.user_id = users.id')
    )

The query above will produce the following SQL:

.. code-block:: sql

    SELECT * FROM users
    WHERE EXISTS (
        SELECT 1 FROM orders WHERE orders.user_id = users.id
    )


Aggregates
----------

The query builder also provides a variety of aggregate methods, `
such as ``count``, ``max``, ``min``, ``avg``, and ``sum``.

.. code-block:: python

    users = db.table('users').count()

    price = db.table('orders').max('price')

    price = db.table('orders').min('price')

    price = db.table('orders').avg('price')

    total = db.table('users').sum('votes')


Raw expressions
---------------

Sometimes you may need to use a raw expression in a query.
These expressions will be injected into the query as strings, so be careful not to create any SQL injection points!
To create a raw expression, you may use the ``raw()`` method:

.. code-block:: python

    db.table('users') \
        .select(db.raw('count(*) as user_count, status')) \
        .where('status', '!=', 1) \
        .group_by('status') \
        .get()


Inserts
-------

Insert records into a table
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').insert(email='foo@bar.com', votes=0)

    db.table('users').insert({
        'email': 'foo@bar.com',
        'votes': 0
    })


It is important to note that there is two notations available.
The reason is quite simple: the dictionary notation, though a little less practical, is here to handle
columns names which cannot be passed as keywords arguments.

Inserting records into a table with an auto-incrementing ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the table has an auto-incrementing id, use ``insert_get_id`` to insert a record and retrieve the id:

.. code-block:: python

    id = db.table('users').insert_get_id({
        'email': 'foo@bar.com',
        'votes': 0
    })

Inserting multiple record into a table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').insert([
        {'email': 'foo@bar.com', 'votes': 0},
        {'email': 'bar@baz.com', 'votes': 0}
    ])

Updates
-------

Updating records
~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').where('id', 1).update(votes=1)

    db.table('users').where('id', 1).update({'votes': 1})

Like the ``insert`` statement, there is two notations available.
The reason is quite simple: the dictionary notation, though a little less practical, is here to handle
columns names which cannot be passed as keywords arguments.


Incrementing or decrementing the value of a column
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').increment('votes')  # Increment the value by 1

    db.table('users').increment('votes', 5)  # Increment the value by 5

    db.table('users').decrement('votes')  # Decrement the value by 1

    db.table('users').decrement('votes', 5)  # Decrement the value by 5

You can also specify additional columns to update:

.. code-block:: python

    db.table('users').increment('votes', 1, name='John')


Deletes
-------

Deleting records
~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').where('age', '<', 25).delete()

Delete all records
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    db.table('users').delete()

Truncate
~~~~~~~~

.. code-block:: python

    db.table('users').truncate()


Unions
------

The query builder provides a quick and easy way to "union" two queries:

.. code-block:: python

    first = db.table('users').where_null('first_name')

    users = db.table('users').where_null('last_name').union(first).get()

The ``union_all`` method is also available.


.. _read_write_connections:

Read / Write connections
========================

Sometimes you may wish to use one database connection for SELECT statements,
and another for INSERT, UPDATE, and DELETE statements. Orator makes this easy,
and the proper connections will always be used whether you use raw queries, the query
builder or the actual ORM

Here is an example of how read / write connections should be configured:

.. code-block:: python

    config = {
        'mysql': {
            'read': {
                'host': '192.168.1.1'
            },
            'write': {
                'host': '192.168.1.2'
            },
            'driver': 'mysql',
            'database': 'database',
            'user': 'root',
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


Database transactions
=====================

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

By default, all underlying DBAPI connections are set to be in autocommit mode
meaning that you don't need to explicitly commit after each operation.


Accessing connections
=====================

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
