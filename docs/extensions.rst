.. _Extensions:

Extensions
##########

This section is a list of all the official Orator extensions that provide additional functionalities
not bundled in the core package.

.. _Cache:

Cache
=====

Installation
------------

.. code-block:: text

    pip install orator-cache

Introduction
------------

The ``orator-cache`` package provides query results caching to Orator.
It uses the `Cachy <https://github.com/sdispater/cachy>`_ library to ease cache manipulation.

To activate the caching ability you just need to use the provided ``DatabaseManager`` class instead of
the default one and passing it a ``Cache`` instance:

.. code-block:: python

    from orator_cache import DatabaseManager, Cache

    stores = {
        'stores': {
            'redis': {
                'driver': 'redis',
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'memcached': {
                'driver' 'memcached',
                'servers': [
                    '127.0.0.1:11211'
                ]
            }
        }
    }

    cache = Cache(stores)

    db = DatabaseManager(config, cache=cache)

.. note::

    Since the ``Cache`` class is just a subclass of the Cachy ``CacheManager`` class. You can refer
    to the Cachy `documentation <http://cachy.readthedocs.org>`_ to configure the underlying stores.

.. warning::

    Even though, the extension provides a way to cache queries, the invalidation of the caches
    is the responsability of the developer.


Caching queries
---------------

You can easily cache the results of a query using the ``remember`` or ``remember_forever`` methods:

.. code-block:: python

    users = db.table('users').remember(10).get()

In this example, the results of the query will be cached for ten minutes.
While the results are cached, the query will not be run against the database,
and the results will be loaded from the default cache driver.

.. note::

    You can also specify which cache driver to use:

    .. code-block:: python

        users = db.table('users').cache_driver('redis').remember(10).get()

If you are using a `supported cache driver <http://cachy.readthedocs.org/en/latest/cache_tags.html>`_, you can also add tags to the caches:

.. code-block:: python

    users = db.table('users').cache_tags(['people', 'authors']).remember(10).get()
