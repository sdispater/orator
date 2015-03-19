Installation
------------

You can install Eloquent in 2 different ways:

* The easier and more straightforward is to use pip

    .. code-block:: bash

        $ pip install eloquent

* Install from source using the official repository (https://github.com/sdispater/eloquent)

.. note::

    The different dbapi packages are not part of the package dependencies,
    so you must install them in order to connect to corresponding databases:

        * Postgres: ``pyscopg2``
        * MySQL: ``PyMySQL`` or ``MySQL-python``
        * Sqlite: The ``sqlite3`` module is bundled with Python by default
