Schema Builder
##############

.. role:: python(code)
   :language: python

Introduction
============

The ``Schema`` class provides a database agnostic way of manipulating tables.

Before getting started, be sure to have configured a ``DatabaseManager`` as seen in the :ref:`BasicUsage` section.

.. code-block:: python

    from eloquent import DatabaseManager, Schema

    config = {
        'mysql': {
            'driver': 'mysql',
            'host': 'localhost',
            'database': 'database',
            'username': 'root',
            'password': '',
            'prefix': ''
        }
    }

    db = DatabaseManager(config)
    schema = Schema(db)


Creating and dropping tables
============================

To create a new database table, the ``create`` method is used:

.. code-block:: python

    with schema.create('users') as table:
        table.increments('id')

The ``table`` variable is a ``Blueprint`` instance which can be used to define the new table.

To rename an existing database table, the ``rename`` method can be used:

.. code-block:: python

    schema.rename('from', 'to')

To specify which connection the schema operation should take place on, use the ``connection`` method:

.. code-block:: python

    with schema.connection('foo').create('users') as table:
        table.increments('id')

To drop a table, you can use the ``drop`` or ``drop_if_exists`` methods:

.. code-block:: python

    schema.drop('users')

    schema.drop_if_exists('users')


Adding columns
==============

To update an existing table, you can use the ``table`` method:

.. code-block:: python

    with schema.table('users') as table:
        table.string('email')

The table builder contains a variety of column types that you may use when building your tables:

========================================================  =================================================
Command                                                   Description
========================================================  =================================================
:python:`table.big_increments('id')`                      Incrementing ID using a "big integer" equivalent
:python:`table.big_integer('votes')`                      BIGINT equivalent to the table
:python:`table.binary('data')`                            BLOB equivalent to the table
:python:`table.boolean('confirmed')`                      BOOLEAN equivalent to the table
:python:`table.char('name', 4)`                           CHAR equivalent with a length
:python:`table.date('created_on')`                        DATE equivalent to the table
:python:`table.datetime('created_at')`                    DATETIME equivalent to the table
:python:`table.decimal('amount', 5, 2)`                   DECIMAL equivalent to the table with a precision and scale
:python:`table.double('column', 15, 8)`                   DOUBLE equivalent to the table with precision, 15 digits in total and 8 after the decimal point
:python:`table.enum('choices', ['foo', 'bar'])`           ENUM equivalent to the table
:python:`table.float('amount')`                           FLOAT equivalent to the table
:python:`table.increments('id')`                          Incrementing ID to the table (primary key)
:python:`table.integer('votes')`                          INTEGER equivalent to the table
:python:`table.json('options')`                           JSON equivalent to the table
:python:`table.long_text('description')`                  LONGTEXT equivalent to the table
:python:`table.medium_integer('votes')`                   MEDIUMINT equivalent to the table
:python:`table.medium_text('description')`                MEDIUMTEXT equivalent to the table
:python:`table.morphs('taggable')`                        Adds INTEGER :python:`taggable_id` and STRING :python:`taggable_type`
:python:`table.nullable_timestamps()`                     Same as :python:`timestamps()`, except allows NULLs
:python:`table.small_integer('votes')`                    SMALLINT equivalent to the table
:python:`table.soft_deletes()`                            Adds **deleted_at** column for soft deletes
:python:`table.string('email')`                           VARCHAR equivalent column
:python:`table.string('votes', 100)`                      VARCHAR equivalent with a length
:python:`table.text('description')`                       TEXT equivalent to the table
:python:`table.time('sunrise')`                           TIME equivalent to the table
:python:`table.timestamp('added_at')`                     TIMESTAMP equivalent to the table
:python:`table.timestamps()`                              Adds **created_at** and **updated_at** columns
:python:`.nullable()`                                     Designate that the column allows NULL values
:python:`.default(value)`                                 Declare a default value for a column
:python:`.unsigned()`                                     Set INTEGER to UNSIGNED
========================================================  =================================================


Changing columns
================

Sometimes you may need to modify an existing column.
For example, you may wish to increase the size of a string column.
To do so, you can use the ``change`` method.
For example, let's increase the size of the ``name`` column from 25 to 50:

.. code-block:: python

    with schema.table('users') as table:
        table.string('name', 50).change()

You could also modify the column to be nullable:

.. code-block:: python

    with schema.table('user') as table:
        table.string('name', 50).nullable().change()


.. warning::

    The column change feature, while tested, is still considered in **beta** stage.
    Please report any encountered issue or bug on the `Github project <https://github.com/sdispater/eloquent>`_


Renaming columns
================

To rename a column, you can use use the ``rename_column`` method on the Schema builder:

.. code-block:: python

    with schema.table('users') as table:
        table.rename('from', 'to')

.. warning::

    The rename column feature, while tested, is still considered in **beta** stage (especially for SQLite).
    Please report any encountered issue or bug on the `Github project <https://github.com/sdispater/eloquent>`_


Dropping columns
================

To drop a column, you can use use the ``drop_column`` method on the Schema builder:

Dropping a column from a database table
---------------------------------------

.. code-block:: python

    with schema.table('users') as table:
        table.drop_column

Dropping multiple columns from a  database table
------------------------------------------------

.. code-block:: python

    with schema.table('users') as table:
        table.drop_column('votes', 'avatar', 'location')


Checking existence
==================

You can easily check for the existence of a table or column using the ``has_table`` and ``has_column`` methods:

Checking for existence of a table
---------------------------------

.. code-block:: python

    if schema.has_table('users'):
        # ...

Checking for existence of a column:

.. code-block:: python

    if schema.has_column('users', 'email'):
        # ...


Adding indexes
==============

The schema builder supports several types of indexes. There are two ways to add them.
First, you may fluently define them on a column definition:

.. code-block:: python

    table.string('email').unique()

Or, you may choose to add the indexes on separate lines. Below is a list of all available index types:

========================================================  =================================================
Command                                                   Description
========================================================  =================================================
:python:`table.primary('id')`                             Adds a primary key
:python:`table.primary(['first', 'last'])`                Adds composite keys
:python:`table.unique('email')`                           Adds a unique index
:python:`table.index('state')`                            Adds a basic index
========================================================  =================================================


Dropping indexes
================

To drop an index you must specify the index's name.
Eloquent assigns a reasonable name to the indexes by default.
Simply concatenate the table name, the names of the column in the index, and the index type.
Here are some examples:

========================================================  =================================================
Command                                                   Description
========================================================  =================================================
:python:`table.drop_primary('user_id_primary')`           Drops a primary key from the "users" table
:python:`table.drop_unique('user_email_unique')`          Drops a unique index from the "users" table
:python:`table.drop_index('geo_state_index')`             Drops a basic index from the "geo" table
========================================================  =================================================


Foreign keys
============

Eloquent also provides support for adding foreign key constraints to your tables:

.. code-block:: python

    table.integer('user_id').unsigned()
    table.foreign('user_id').references('id').on('users')

In this example, we are stating that the ``user_id``
column references the ``id`` column on the ``users`` table.
Make sure to create the foreign key column first!

You may also specify options for the "on delete" and "on update" actions of the constraint:

.. code-block:: python

    table.foreign('user_id')\
        .references('id').on('users')\
        .on_delete('cascade')

To drop a foreign key, you may use the ``drop_foreign`` method.
A similar naming convention is used for foreign keys as is used for other indexes:

.. code-block:: python

    table.drop_foreign('posts_user_id_foreign')

.. note::

    When creating a foreign key that references an incrementing integer,
    remember to always make the foreign key column ``unsigned``.


Dropping timestamps and soft deletes
====================================

To drop the ``timestamps``, ``nullable_timestamps`` or ``soft_deletes`` column types,
you may use the following methods:

========================================================  =================================================
Command                                                   Description
========================================================  =================================================
:python:`table.drop_timestamps()`                         Drops the **created_at** and **deleted_at** columns
:python:`table.drop_soft_deletes()`                       Drops the **deleted_at** column
========================================================  =================================================
