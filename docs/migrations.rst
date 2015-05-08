.. _Migrations:

Migrations
##########

Migrations are a type of version control for your database.
They allow a team to modify the database schema and stay up to date on the current schema state.
Migrations are typically paired with the :ref:`SchemaBuilder` to easily manage your database's schema.


.. note::

    For the migrations to actually work, you need a configuration file describing your databases
    in a ``DATABASES`` dict, like so:

    .. code-block:: python

        DATABASES = {
            'mysql': {
                'driver': 'mysql',
                'host': 'localhost',
                'database': 'database',
                'username': 'root',
                'password': '',
                'prefix': ''
            }
        }

    This file needs to be precised when using migrations commands.


Creating Migrations
===================

To create a migration, you can use the ``migrate:make`` command on the Eloquent CLI:

.. code-block:: bash

    eloquent migrate:make create_users_table -c databases.py

This will create a migration file that looks like this:

.. code-block:: python

    from eloquent.migrations import Migration


    class CreateTableUsers(Migration):

        def up(self):
            """
            Run the migrations.
            """
            pass

        def down(self):
            """
            Revert the migrations.
            """
            pass


By default, the migration will be placed in a ``migrations`` folder relative to where the command has been executed,
and will contain a timestamp which allows the framework to determine the order of the migrations.

If you want the migrations to be stored in another folder, use the ``--path/-p`` option:

.. code-block:: bash

    eloquent migrate:make create_users_table -c databases.py -p my/path/to/migrations

The ``--table`` and ``--create`` options can also be used to indicate the name of the table,
and whether the migration will be creating a new table:

.. code-block:: bash

    eloquent migrate:make add_votes_to_users_table -c databases.py --table=users

    eloquent migrate:make create_users_table -c databases.py --table=users --create


Running Migrations
==================

To run all outstanding migrations, just use the ``migrate`` command:

.. code-block:: bash

    eloquent migrate -c databases.py


Rolling back migrations
=======================

Rollback the last migration operation
-------------------------------------

.. code-block:: bash

    eloquent migrate:rollback -c databases.py

Rollback all migrations
-----------------------

.. code-block:: bash

    eloquent migrate:reset -c databases.py
