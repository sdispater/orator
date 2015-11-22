.. _Collections:

Collections
###########

Introduction
============

The ``Collection`` class provides a fluent, convenient wrapper for working with list or dictionaries of data.

It's behind every ORM queries that return multiple results.
For example, check out the following code:

.. code-block:: python

    users = User.all()
    names = users.map(lambda user: user.name.lower())
    names = names.reject(lambda name: len(name) == 0)

This returns very users names that are not empty.


Available Methods
=================

For the remainder of this documentation, we'll discuss each method available on the ``Collection`` class.
Remember, all of these methods may be chained for fluently manipulating the underlying list or dict.
Furthermore, almost every method returns a new ``Collection`` instance,
allowing you to preserve the original copy of the collection when necessary.

You may select any method from this table to see an example of its usage:

* all_
* avg_
* chunk_
* collapse_
* contains_
* count_
* diff_
* each_
* every_
* filter_
* first_
* flip_
* forget_
* for_page_
* get_
* implode_
* is_empty_
* keys_
* last_
* map_
* merge_
* only_
* pluck_
* pop_
* prepend_
* pull_
* push_
* put_
* reduce_
* reject_
* reverse_
* serialize_
* shift_
* sort_
* sum_
* take_
* to_json_
* transform_
* unique_
* values_
* where_
* without_
* zip_


Methods Listing
===============

.. _all:

``all()``
---------

The ``all`` method simply returns the underlying list or dict represented by the collection:

.. code-block:: python

    Collection([1, 2, 3]).all()

    # [1, 2, 3]


.. _avg:

``avg()``
---------

The ``avg`` method returns the average of all items in the collection:

.. code-block:: python

    Collection([1, 2, 3, 4, 5]).avg()

    # 3

If the collection contains nested objects or dictionaries, you must pass a key to use for determining
which values to calculate the average:

.. code-block:: python

    collection = Collection([
        {'name': 'JavaScript: The Good Parts', 'pages': 176},
        {'name': 'JavaScript: The Defnitive Guide', 'pages': 1096}
    ])

    collection.avg('pages')

    # 636


.. _chunk:

``chunk()``
-----------

The ``chunk`` method breaks the collection into multiple, smaller collections of a given size:

.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5, 6, 7])

    chunks = collection.chunk(4)

    chunks.serialize()

    # [[1, 2, 3, 4], [5, 6, 7]]


.. _collapse:

``collapse()``
--------------

The ``collapse`` method collapses a collection of lists into a flat collection:

.. code-block:: python

    collection = Collection([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    collapsed = collection.collapse()

    collapsed.all()

    # [1, 2, 3, 4, 5, 6, 7, 8, 9]


.. _contains:

``contains()``
--------------

The ``contains`` method determines whether the collection contains a given item:

.. code-block:: python

    collection = Collection(['foo', 'bar'])

    collection.contains('foo')

    # True

    collection = Collection({'foo': 'bar'})

    collection.contains('foo')

    # True

You can also use the ``in`` keyword:

.. code-block:: python

    'foo' in collection

    # True

You can also pass a key / value pair to the ``contains`` method,
which will determine if the given pair exists in the collection:

.. code-block:: python

    collection = Collection([
        {'name': 'John', 'id': 1},
        {'name': 'Jane', 'id': 2}
    ])

    collection.contains('name', 'Simon')

    # False

Finally, you may also pass a callback to the ``contains`` method to perform your own truth test:


.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5])

    collection.contains(lambda item: item > 5)

    # False


.. _count:

``count()``
-----------

The ``count`` method returns the total number of items in the collection:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    collection.count()

    # 4

The ``len`` function can also be used:

.. code-block:: python

    len(collection)

    # 4


.. _diff:

``diff()``
----------

The ``diff`` method compares the collection against another collection, a ``list`` or a ``dict``:

.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5])

    diff = collection.diff([2, 4, 6, 8])

    diff.all()

    # [1, 3, 5]


.. _each:

``each()``
----------

The ``each`` method iterates over the items in the collection and passes each item to a given callback:

.. code-block:: python

    posts.each(lambda post: post.author().save(author))

Return ``False`` from your callback to break out of the loop:

.. code-block:: python

    posts.each(lambda post: post.author().save(author) if author.name == 'John' else False)


.. _every:

``every()``
-----------

The ``every`` method creates a new collection consisting of every n-th element:

.. code-block:: python

    collection = Collection(['a', 'b', 'c', 'd', 'e', 'f'])

    collection.every(4).all()

    # ['a', 'e']

You can optionally pass the offset as the second argument:


.. code-block:: python

    collection.every(4, 1).all()

    # ['b', 'f']


.. _filter:

``filter()``
------------

The ``filter`` method filters the collection by a given callback,
keeping only those items that pass a given truth test:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    filtered = collection.filter(lambda item: item > 2)

    filtered.all()

    # [3, 4]


.. _first:

``first()``
-----------

The ``first`` method returns the first element in the collection
that passes a given truth test:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    collection.first(lambda item: item > 2)

    # 3

You can also call the ``first`` method with no arguments
to get the first element in the collection.
If the collection is empty, ``None`` is returned:

.. code-block:: python

    collection.first()

    # 1


.. _flip:

``flip()``
----------

The ``flip`` method swaps the collection's keys with their corresponding values:

.. code-block:: python

    collection = Collection({'name': 'john', 'votes': 100})

    flipped = collection.flip()

    flipped.all()

    # {'john': 'name', 100: 'votes'}


.. _forget:

``forget()``
------------

The ``forget`` method removes an item from the collection by its key:

.. code-block:: python

    collection = Collection({'name': 'john', 'votes': 100})

    collection.forget('name')

    collection.all()

    # {'votes': 100}

.. warning::

    Unlike most other collection methods, ``forget`` does not return a new modified collection;
    it modifies the collection it is called on.


.. _for_page:

``for_page``
------------

The ``for_page`` method returns a new collection containing
the items that would be present on a given page number:

.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5, 6, 7, 8, 9])

    chunk = collection.for_page(2, 3)

    chunk.all()

    # 4, 5, 6

The method requires the page number and the number of items to show per page, respectively.


.. _get:

``get()``
---------

The ``get`` method returns the item at a given key. If the key does not exist, ``None`` is returned:

.. code-block:: python

    collection = Collection({'name': 'john', 'votes': 100})

    collection.get('name')

    # john

    collection = Collection([1, 2, 3])

    collection.get(3)

    # None

You can optionally pass a default value as the second argument:

.. code-block:: python

    collection = Collection({'name': 'john', 'votes': 100})

    collection.get('foo', 'default-value')

    # default-value


.. _implode:

``implode()``
-------------

The ``implode`` method joins the items in a collection.
Its arguments depend on the type of items in the collection.

If the collection contains dictionaries or objects,
you must pass the key of the attributes you wish to join,
and the "glue" string you wish to place between the values:

.. code-block:: python

    collection = Collection([
        {'account_id': 1, 'product': 'Desk'},
        {'account_id': 2, 'product': 'Chair'}
    ])

    collection.implode('product', ', ')

    # Desk, Chair

If the collection contains simple strings,
simply pass the "glue" as the only argument to the method:

.. code-block:: python

    collection = Collection(['foo', 'bar', 'baz'])

    collection.implode('-')

    # foo-bar-baz


.. _is_empty:

``is_empty()``
--------------

The ``is_empty`` method returns ``True`` if the collection is empty; otherwise, ``False`` is returned:

.. code-block:: python

    Collection([]).is_empty()

    # True


.. _keys:

``keys()``
----------

The ``keys`` method returns all of the collection's keys:

.. code-block:: python

    collection = Collection({
        'account_id': 1,
        'product': 'Desk'
    })

    keys = collection.keys()

    keys.all()

    # ['account_id', 'product']


.. _last:

``last()``
----------

The ``last`` method returns the last element in the collection that passes a given truth test:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    last = collection.last(lambda item: item < 3)

    # 2

You can also call the ``last`` method with no arguments to get the last element in the collection.
If the collection is empty, ``None`` is returned:

.. code-block:: python

    collection.last()

    # 4


.. _map:

``map()``
---------

The ``map`` method iterates through the collection and passes each value to the given callback.
The callback is free to modify the item and return it, thus forming a new collection of modified items:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    multiplied = collection.map(lambda item: item * 2)

    multiplied.all()

    # [2, 4, 6, 8]

.. warning::

    Like most other collection methods, ``map`` returns a new ``Collection`` instance;
    it does not modify the collection it is called on.
    If you want to transform the original collection, use the transform_ method.


.. _merge:

``merge()``
-----------

The merge method merges the given dict or list into the collection:

.. code-block:: python

    collection = Collection({
        'product_id': 1, 'name': 'Desk'
    })

    collection.merge({
        'price': 100,
        'discount': False
    })

    collection.all()

    # {
    #     'product_id': 1,
    #     'name': 'Desk',
    #     'price': 100,
    #     'discount': False
    # }

For lists collections, the values will be appended to the end of the collection:

.. code-block:: python

    collection = Collection(['Desk', 'Chair'])

    collection.merge(['Bookcase', 'Door'])

    collection.all()

    # ['Desk', 'Chair', 'Bookcase', 'Door']

.. warning::

    Unlike most other collection methods, ``merge`` does not return a new modified collection;
    it modifies the collection it is called on.


.. _only:

``only()``
----------

The ``only`` method returns the items in the collection with the specified keys:

.. code-block:: python

    collection = Collection({
        'product_id': 1,
        'name': 'Desk',
        'price': 100,
        'discount': False
    })

    filtered = collection.only('product_id', 'name')

    filtered.all()

    # {'product_id': 1, 'name': 'Desk'}

For the inverse of ``only``, see the without_ method.


.. _pluck:

``pluck()``
-----------

The ``pluck`` method retrieves all of the collection values for a given key:

.. code-block:: python

    collection = Collection([
        {'product_id': 1, 'product': 'Desk'},
        {'product_id': 2, 'product': 'Chair'}
    ])

    plucked = collection.pluck('product')

    plucked.all()

    # ['Desk', 'Chair']

You can also specify how you wish the resulting collection to be keyed:

.. code-block:: python

    plucked = collection.pluck('name', 'product_id')

    plucked.all()

    # {1: 'Desk', 2: 'Chair'}


.. _pop:

``pop()``
---------

The ``pop`` method removes and returns the last item from the collection:

.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5])

    collection.pop()

    # 5

    collection.all()

    # [1, 2, 3, 4]


.. _prepend:

``prepend()``
-------------

The ``prepend`` method adds an item to the beginning of the collection:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    collection.prepend(0)

    collection.all()

    # [0, 1, 2, 3, 4]


.. _pull:

``pull()``
----------

The ``pull`` method removes and returns an item from the collection by its key:

.. code-block:: python

    collection = Collection({
        'product_id': 1, 'product': 'Desk'
    })

    collection.pull('product_id')

    collection.all()

    # {'product': 'Desk'}


.. _push:

``push()``/``append()``
-----------------------

The ``push`` (or ``append``) method appends an item to the end of the collection:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    collection.push(5)

    collection.all()

    # [1, 2, 3, 4, 5]


.. _put:

``put()``
---------

The ``put`` method sets the given key and value in the collection:

.. code-block:: python

    collection = Collection({
        'product_id': 1, 'product': 'Desk'
    })

    collection.put('price', 100)

    collection.all()

    # {'product_id': 1, 'product': 'Desk', 'price': 100}

.. note::

    It is equivalent to:

    .. code-block:: python

        collection['price'] = 100


.. _reduce:

``reduce()``
------------

The ``reduce`` method reduces the collection to a single value,
passing the result of each iteration into the subsequent iteration:

.. code-block:: python

    collection = Collection([1, 2, 3])

    collection.reduce(lambda result, item: (result or 0) + item)

    # 6

The value for ``result`` on the first iteration is ``None``;
however, you can specify its initial value by passing a second argument to reduce:

.. code-block:: python

    collection.reduce(lambda result, item: result + item, 4)

    # 10


.. _reject:

``reject()``
------------

The ``reject`` method filters the collection using the given callback.
The callback should return ``True`` for any items it wishes to remove from the resulting collection:

.. code-block:: python

    collection = Collection([1, 2, 3, 4])

    filtered = collection.reject(lambda item: item > 2)

    filtered.all()

    # [1, 2]

For the inverse of ``reject``, see the filter_ method.


.. _reverse:

``reverse()``
-------------

The ``reverse`` method reverses the order of the collection's items:

.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5])

    reverse = collection.reverse()

    reverse.all()

    # [5, 4, 3, 2, 1]


.. _serialize:

``serialize``
-------------

The ``serialize`` method converts the collection into a ``dict`` or a ``list``.
If the collection's values are :ref:`ORM` models, the models will also be converted to dictionaries:

.. code-block:: python

    collection = Collection({'name': 'Desk', 'product_id': 1})

    collection.serialize()

    # {'name': 'Desk', 'product_id': 1}

    collection = Collection([User.find(1)])

    collection.serialize()

    # [{'id': 1, 'name': 'John'}]


.. _shift:

``shift()``
-----------

The ``shift`` method removes and returns the first item from the collection:

.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5])

    collection.shift()

    # 1

    collection.all()

    # [2, 3, 4, 5]


.. _sort:

``sort()``
----------

The ``sort`` method sorts the collection:

.. code-block:: python

    collection = Collection([5, 3, 1, 2, 4])

    sorted = collection.sort()

    sorted.all()

    # [1, 2, 3, 4, 5]


.. _sum:

``sum()``
---------

The ``sum`` method returns the sum of all items in the collection:

.. code-block:: python

    Collection([1, 2, 3, 4, 5]).sum()

    # 15

If the collection contains dictionaries or objects, you must pass a key to use for determining which values to sum:

.. code-block:: python

    collection = Collection([
        {'name': 'JavaScript: The Good Parts', 'pages': 176},
        {'name': 'JavaScript: The Defnitive Guide', 'pages': 1096}
    ])

    collection.sum('pages')

    # 1272

In addition, you can pass your own callback to determine which values of the collection to sum:

.. code-block:: python

    collection = Collection([
        {'name': 'Chair', 'colors': ['Black']},
        {'name': 'Desk', 'colors': ['Black', 'Mahogany']},
        {'name': 'Bookcase', 'colors': ['Red', 'Beige', 'Brown']}
    ])

    collection.sum(lambda product: len(product['colors']))

    # 6


.. _take:

``take()``
----------

The ``take`` method returns a new collection with the specified number of items:

.. code-block:: python

    collection = Collection([0, 1, 2, 3, 4, 5])

    chunk = collection.take(3)

    chunk.all()

    # [0, 1, 2]

You can also pass a negative integer to take the specified amount of items from the end of the collection:

.. code-block:: python

    chunk = collection.chunk(-2)

    chunk.all()

    # [4, 5]

.. warning::

    ``serialize`` also converts all of its nested objects.
    If you want to get the underlying items as is, use the all_ method instead.


.. _to_json:

``to_json()``
-------------

The ``to_json`` method converts the collection into JSON:

.. code-block:: python

    collection = Collection({'name': 'Desk', 'price': 200})

    collection.to_json()

    # '{"name": "Desk", "price": 200}'


.. _transform:

``transform()``
---------------

The ``transform`` method iterates over the collection and calls the given callback
with each item in the collection.
The items in the collection will be replaced by the values returned by the callback:

.. code-block:: python

    collection = Collection([1, 2, 3, 4, 5])

    collection.transform(lambda item: item * 2)

    collection.all()

    # [2, 4, 6, 8, 10]

.. warning::

    Unlike most other collection methods, ``transform`` modifies the collection itself.
    If you wish to create a new collection instead, use the map_ method.


.. _unique:

``unique()``
------------

The ``unique`` method returns all of the unique items in the collection:

.. code-block:: python

    collection = Collection([1, 1, 2, 2, 3, 4, 2])

    unique = collection.unique()

    unique.all()

    # [1, 2, 3, 4]

When dealing with dictionaries or objects, you can specify the key used to determine uniqueness:
    
.. code-block:: python

    collection = Collection([
        {'name': 'iPhone 6', 'brand': 'Apple', 'type': 'phone'},
        {'name': 'iPhone 5', 'brand': 'Apple', 'type': 'phone'},
        {'name': 'Apple Watch', 'brand': 'Apple', 'type': 'watch'},
        {'name': 'Galaxy S6', 'brand': 'Samsung', 'type': 'phone'},
        {'name': 'Galaxy Gear', 'brand': 'Samsung', 'type': 'watch'}
    ])

    unique = collection.unique('brand')

    unique.all()

    # [
    #     {'name': 'iPhone 6', 'brand': 'Apple', 'type': 'phone'},
    #     {'name': 'Galaxy S6', 'brand': 'Samsung', 'type': 'phone'}
    # ]

You can also pass your own callback to determine item uniqueness:

.. code-block:: python

    unique = collection.unique(lambda item: item['brand'] + item['type'])

    unique.all()

    # [
    #     {'name': 'iPhone 6', 'brand': 'Apple', 'type': 'phone'},
    #     {'name': 'Apple Watch', 'brand': 'Apple', 'type': 'watch'},
    #     {'name': 'Galaxy S6', 'brand': 'Samsung', 'type': 'phone'},
    #     {'name': 'Galaxy Gear', 'brand': 'Samsung', 'type': 'watch'}
    # ]


.. _values:

``values()``
------------

The ``values`` method returns all of the collection's values:

.. code-block:: python

    collection = Collection({
        'account_id': 1,
        'product': 'Desk'
    })

    values = collection.values()

    values.all()

    # [1, 'Desk']


.. _where:

``where()``
-----------

The ``where`` method filters the collection by a given key / value pair:

.. code-block:: python

    collection = Collection([
        {'name': 'Desk', 'price': 200},
        {'name': 'Chair', 'price': 100},
        {'name': 'Bookcase', 'price': 150},
        {'name': 'Door', 'price': 100},
    ])

    filtered = collection.where('price', 100)

    filtered.all()

    # [
    #     {'name': 'Chair', 'price': 100},
    #     {'name': 'Door', 'price': 100}
    # ]


.. _without:

``without()``
-------------

The ``without`` method returns all items in the collection except for those with the specified keys:

.. code-block:: python

    collection = Collection({
        'product_id': 1,
        'name': 'Desk',
        'price': 100,
        'discount': False
    })

    filtered = collection.without('price', 'discount')

    filtered.all()

    # {'product_id': 1, 'name': 'Desk'}

For the inverse of ``without``, see the only_ method.


.. _zip:

``zip()``
---------

The ``zip`` method merges together the values of the given list
with the values of the collection at the corresponding index:

.. code-block:: python

    collection = Collection(['Chair', 'Desk'])

    zipped = collection.zip([100, 200])

    zipped.all()

    # [('Chair', 100), ('Desk', 200)]
