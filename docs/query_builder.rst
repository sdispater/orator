Query Builder
=============


Introduction
------------

The database query builder provides a fluent interface to create and run database queries.
It can be used to perform most database operations in your application, and works on all supported database systems.


.. note::

    Since Eloquent uses DBAPI packages under the hood, there is no need to clean
    parameters passed as bindings.

.. note::

    The underlying DBAPI connections are automatically configured to return dictionaries
    rather than the default tuple representation.


Selects
-------

Retrieving all row from a table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    users = db.table('users').get()

    for user in users:
        print(user['name'])

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

    users = db.table('users').where_not_between('age', [25, 35]).get()~

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
you may use the where and orWhere methods on a join.
Instead of comparing two columns, these methods will compare the column against a value:


.. code-block:: python

    clause = JoinClause('contacts').on('users.id', '=', 'contacts.user_id').where('contacts.user_id', '>', 5)

    db.table('users').join(clause).get()


Advanced where
--------------

Sometimes you may need to create more advanced where clauses such as "where exists" or nested parameter groupings.
It is pretty easy to do with the Eloquent query builder

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

.. note::

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

.. note::

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


Pessimistic locking
-------------------

The query builder includes a few functions to help you do "pessimistic locking" on your SELECT statements.

To run the SELECT statement with a "shared lock", you may use the ``shared_lock`` method on a query:

.. code-block:: python

    db.table('users').where('votes', '>', 100).shared_lock().get()

To "lock for update" on a SELECT statement, you may use the ``lock_for_update`` method on a query:

.. code-block:: python

   db.table('users').where('votes', '>', 100).lock_for_update().get()
