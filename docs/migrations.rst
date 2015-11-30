.. _Migrations:

Migrations
##########

Migrations are a type of version control for your database.
They allow a team to modify the database schema and stay up to date on the current schema state.
Migrations are typically paired with the :ref:`SchemaBuilder` to easily manage your database's schema.


.. note::

    For the migrations to actually work, you need a configuration file describing your databases.
    It can be a ``orator.yml`` file or a ``orator.py`` located where the ``orator`` command is executed,
    or any other yaml or python file (these must then be explicitely specified when executing commands with the ``--config\-c``)
    which follow the following requirements:

    * yaml files must follow this structure:

    .. code-block:: yaml

        databases:
            mysql:
                driver: mysql
                host: localhost
                database: database
                username: root
                password: ''
                prefix: ''

    * python files must follow this structure

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


Creating Migrations
===================

To create a migration, you can use the ``migrations:make`` command on the Orator CLI:

.. code-block:: bash

    orator migrations:make create_users_table

This will create a migration file that looks like this:

.. code-block:: python

    from orator.migrations import Migration


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

    orator migrations:make create_users_table -p my/path/to/migrations

The ``--table`` and ``--create`` options can also be used to indicate the name of the table,
and whether the migration will be creating a new table:

.. code-block:: bash

    orator migrations:make add_votes_to_users_table --table=users

    orator migrations:make create_users_table --table=users --create

These commands would respectively create the following migrations:

.. code-block:: python

    from orator.migrations import Migration


    class AddVotesToUsersTable(Migration):

        def up(self):
            """
            Run the migrations.
            """
            with self.schema.table('users') as table:
                pass

        def down(self):
            """
            Revert the migrations.
            """
            with self.schema.table('users') as table:
                pass

.. code-block:: python

    from orator.migrations import Migration


    class CreateTableUsers(Migration):

        def up(self):
            """
            Run the migrations.
            """
            with self.schema.create('users') as table:
                table.increments('id')
                table.timestamps()

        def down(self):
            """
            Revert the migrations.
            """
            self.schema.drop('users')


.. note::

    ``Migration`` instances have a ``db`` attribute which is an instance of the current
    ``Connection``.


Running Migrations
==================

To run all outstanding migrations, just use the ``migrations:run`` command:

.. code-block:: bash

    orator migrations:run -c databases.py

.. note::

    By default, all migrations are run inside a transaction.
    If you want queries to be executed directly just set the ``transactional`` attribute to ``False``. You
    then must explicitely declare the transactions:

    .. code-block:: python

        class CreateTableUsers(Migration):

            transactional = False

            def up(self):
                """
                Run the migrations.
                """
                with self.db.transaction():
                    with self.schema.create('users') as table:
                        table.increments('id')
                        table.timestamps()

            def down(self):
                """
                Revert the migrations.
                """
                with self.db.transaction():
                    self.schema.drop('users')


Rolling back migrations
=======================

Rollback the last migration operation
-------------------------------------

.. code-block:: bash

    orator migrations:rollback

Rollback all migrations
-----------------------

.. code-block:: bash

    orator migrations:reset


Getting migrations status
=========================

To see the status of the migrations, just use the ``migrations:status`` command:

.. code-block:: bash

    orator migrations:status

This would output something like this:

.. code-block:: bash

    +----------------------------------------------------+------+
    | Migration                                          | Ran? |
    +----------------------------------------------------+------+
    | 2015_05_02_04371430559457_create_users_table       | Yes  |
    | 2015_05_04_02361430725012_add_votes_to_users_table | No   |
    +----------------------------------------------------+------+
