Installation
------------

You can install Orator in 2 different ways:

* The easier and more straightforward is to use pip

.. code-block:: bash

    pip install orator

* Install from source using the official repository (https://github.com/sdispater/orator)

.. note::

    The different dbapi packages are not part of the package dependencies,
    so you must install them in order to connect to corresponding databases:

    * PostgreSQL: ``psycopg2``
    * MySQL: ``PyMySQL`` or ``mysqlclient``
    * SQLite: The ``sqlite3`` module is bundled with Python by default
