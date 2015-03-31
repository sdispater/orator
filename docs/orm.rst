The ORM
#######

Introduction
============

The ORM provides a simple ActiveRecord implementation for working with your databases.
Each database table has a corresponding Model which is used to interact with that table.

Before getting started, be sure to have configured a ``DatabaseManager`` as seen in the :ref:`BasicUsage` section.

.. code-block:: python

    from eloquent import DatabaseManager

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


Basic Usage
===========

To actually get started, you need to tell the ORM to use the configured ``DatabaseManager`` for all models
inheriting from the ``Model`` class:

.. code-block:: python

    from eloquent import Model

    Model.set_connection_resolver(db)

And that's pretty much it. You can now define your models.


Defining a Model
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

.. note::

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

.. note::

    All methods available on the :ref:`QueryBuilder` are also available when querying models.


Retrieving a Model by primary key or raise an exception
-------------------------------------------------------

Sometimes it may be useful to throw an exception if a model is not found.
You can use the ``find_or_fail`` method for that, which will raise a ``ModelNotFound`` exception.

.. code-block:: python

    model = User.find_or_fail(1)

    model = User.where('votes', '>', 100).first_or_fail()


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

If you are using :ref:`read_write_connections`, you can force the query to use the "write" connection
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

.. warning::

    When using ``__guarded__``, you should still never pass any user input directly since
    any attribute that is not guarded can be mass-assigned.


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

.. note::

    Your models will probably have auto-incrementing primary keys. However, if you wish to maintain
    your own primary keys, set the ``__autoincrementing__`` property to ``False``.

You can also use the ``create`` method to save a model in a single line, but you will need to specify
either the ``__fillable__`` or ``__guarded__`` property on the model since all models are protected against
mass-assigment by default.

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

You can alsoe run a delete query on a set of models:

.. code-block:: python

    affected_rows = User.where('votes', '>' 100).delete()


Updating only the model's timestamps
------------------------------------

If you want to only update the timestamps on a model, you can use the ``touch`` method:

.. code-block:: python

    user.touch()


Relationships
=============

Eloquent makes managing and working with relationships easy. It supports many types of relationships:

* :ref:`OneToOne`
* :ref:`OneToMany`
* :ref:`ManyToMany`
* :ref:`HasManyThrough`

.. _OneToOne:

One To One
----------

Defining a One To One relationship
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A one-to-one relationship is a very basic relation. For instance, a ``User`` model might have a ``Phone``.
We can define this relation with the ORM:

.. code-block:: python

    class User(Model):

        @property
        def phone(self):
            return self.has_one(Phone)

The first argument passed to the ``has_one`` method is the class of the related model.
Once the relationship is defined, we can retrieve it using :ref:`dynamic_properties`:

.. code-block:: python

    phone = User.find(1).phone

The SQL performed by this statement will be as follow:

.. code-block:: sql

    SELECT * FROM users WHERE id = 1

    SELECT * FROM phones WHERE user_id = 1

The Eloquent ORM assumes the foreign key of the relationship based on the model name. In this case,
``Phone`` model is assumed to use a ``user_id`` foreign key. If you want to override this convention,
you can pass a second argument to the ``has_one`` method. Furthermore, you may pass a third argument
to the method to specify which local column should be used for the association:

.. code-block:: python

    return self.has_one(Phone, 'foreign_key')

    return self.has_one(Phone, 'foreign_key', 'local_key')


Defining the inverse of the relation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To define the inverse of the relationship on the ``Phone`` model, you can use the ``belongs_to`` method:

.. code-block:: python

    class Phone(Model):

        @property
        def user(self):
            return self.belongs_to(User)

In the example above, the Eloquent ORM will look for a ``user_id`` column on the ``phones`` table. You can
define a different foreign key column, you can pass it as the second argument of the ``belongs_to`` method:

.. code-block:: python

    return self.belongs_to(User, 'local_key')

Additionally, you pass the third parameter which specifies the name of the associated column on the parent table:

.. code-block:: python

    return self.belongs_to(User, 'local_key', 'parent_key')


.. _OneToMany:

One To Many
-----------

An example of a one-to-many relation is a blog post that has many comments:

.. code-block:: python

    class Post(Model):

        @property
        def comments(self):
            return self.has_many(Comment)

Now you can access the post's comments via :ref:`dynamic_properties`:

.. code-block:: python

    comments = Post.find(1).comments

Again, you may override the conventional foreign key by passing a second argument to the ``has_many`` method.
And, like the ``has_one`` relation, the local column may also be specified:

.. code-block:: python

    return self.has_many(Comment, 'foreign_key')

    return self.has_many(Comment, 'foreign_key', 'local_key')

Defining the inverse of the relation:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To define the inverse of the relationship on the ``Comment`` model, we use the ``belongs_to`` method:

.. code-block:: python

    class Comment(Model):

        @property
        def post(self):
            return self.belongs_to(Post)


.. _ManyToMany:

Many To Many
------------

Many-to-many relations are a more complicated relationship type.
An example of such a relationship is a user with many roles, where the roles are also shared by other users.
For example, many users may have the role of "Admin". Three database tables are needed for this relationship:
``users``, ``roles``, and ``roles_users``.
The ``roles_users`` table is derived from the alphabetical order of the related table names,
and should have the ``user_id`` and ``role_id`` columns.

We can define a many-to-many relation using the ``belongs_to_many`` method:

.. code-block:: python

    class User(Model):

        @property
        def roles(self):
            return self.belongs_to_many(Role)

Now, we can retrieve the roles through the ``User`` model:

.. code-block:: python

    roles = User.find(1).roles

If you want to use an unconventional table name for your pivot table, you can pass it as the second argument
to the ``belongs_to_many`` method:

.. code-block:: python

    return self.belongs_to_many(Role, 'user_role')

You can also override the conventional associated keys:

.. code-block:: python

    return self.belongs_to_many(Role, 'user_role', 'user_id', 'foo_id')

Of course, you also can define the inverse og the relationship on the ``Role`` model:

.. code-block:: python

    class Role(Model):

        @property
        def users(self):
            return self.belongs_to_many(Role)


.. _HasManyThrough:

Has Many Through
----------------

The "has many through" relation provides a convenient short-cut
for accessing distant relations via an intermediate relation.
For example, a ``Country`` model might have many ``Post`` through a ``User`` model.
The tables for this relationship would look like this:

.. code-block:: yaml

    countries:
        id: integer
        name: string

    users:
        id: integer
        country_id: integer
        name: string

    posts:
        id: integer
        user_id: integer
        title: string

Even though the ``posts`` table does not contain a ``country_id`` column, the ``has_many_through`` relation
will allow access a country's posts via ``country.posts``:

.. code-block:: python

    class Country(Model):

        @property
        def posts(self):
            return self.has_many_through(Post, User)

If you want to manually specify the keys of the relationship,
you can pass them as the third and fourth arguments to the method:

.. code-block:: python

    return self.has_many_through(Post, User, 'country_id', 'user_id')


Querying relations
==================

.. _dynamic_properties:

Dynamic properties
------------------

The Eloquent ORM allows you to access your relations via dynamic properties.
It will automatically load the relationship for you. It will then be accessible via
a dynamic property by the same name as the relation. For example, with the following model ``Post``:

.. code-block:: python

    class Phone(Model):

        @property
        def user(self):
            return self.belongs_to(User)

    phone = Phone.find(1)


You can then print the user's email like this:

.. code-block:: python

    print(phone.user.email)

Now, for one-to-many relationships:

.. code-block:: python

    class Post(Model):

        @property
        def comments(self):
            return self.has_many(Comment)

    post = Post.find(1)

You can then access the post's comments like this:

.. code-block:: python

    comments = post.comments

If you need to add further constraints to which comments are retrieved,
you may call the ``comments`` method and continue chaining conditions:

.. code-block:: python

    comments = post.comments().where('title', 'foo').first()

.. note::

    Relationships that return many results will return an instance of the ``Collection`` class.


Inserting related models
========================

You will often need to insert new related models, like inserting a new comment for a post.
Instead of manually setting the ``post_id`` foreign key, you can insert the new comment from its parent ``Post``model
directly:

.. code-block:: python

    comment = Comment(message='A new comment')

    post = Post.find(1)

    comment = post.comments().save(comment)

If you need to save multiple comments:

.. code-block:: python

    comments = [
        Comment(message='Comment 1'),
        Comment(message='Comment 2'),
        Comment(message='Comment 3')
    ]

    post = Post.find(1)

    post.comments().save_many(comments)

Associating models (Belongs To)
-------------------------------

When updatings a ``belongs_to`` relationship, you can use the associate method:

.. code-block:: python

    account = Account.find(1)

    user.account().associate(account)

    user.save()

Inserting related models (Many to Many)
---------------------------------------

You can also insert related models when working with many-to-many relationship.
For example, with ``User`` and ``Roles`` models:

Attaching many to many models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    user = User.find(1)
    role = Roles.find(3)

    user.roles().attach(role)

    # or
    user.roles().attach(3)


You can also pass a dictionary of attributes that should be stored on the pivot table for the relation:

.. code-block:: python

    user.roles().attach(3, {'expires': expires})

The opposite of ``attach`` is ``detach``:

.. code-block:: python

    user.roles().detach(3)

Both ``attach`` and ``detach`` also take list of IDs as input:

.. code-block:: python

    user = User.find(1)

    user.roles().detach([1, 2, 3])

    user.roles().attach([{1: {'attribute1': 'value1'}}, 2, 3])


Using sync to attach many to many models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also use the ``sync`` method to attach related models. The ``sync`` method accepts a list of IDs
to place on the pivot table. After this operation, only the IDs in the list will be on the pivot table:

.. code-block:: python

    user.roles().sync([1, 2, 3])


Adding pivot data when syncing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also associate other pivot table values with the given IDs:

.. code-block:: python

    user.roles().sync([{1: {'expires': True}}])

Sometimes you might want to create a new related model and attach it in a single command.
For that, you can use the save method:

.. code-block:: python

    role = Role(name='Editor')

    User.find(1).roles().save(role)

You can also pass attributes to place on the pivot table:

.. code-block:: python

    User.find(1).roles().save(role, {'expires': True})


Touching parent timestamps
==========================

When a model ``belongs_to`` another model, like a ``Comment`` belonging to a ``Post``, it is often helpful
to update the parent's timestamp when the chil model is updated. For instance, when a ``Comment`` model is updated,
you may want to automatically touch the ``updated_at`` timestamp of the owning ``Post``. For this to actually happen,
you just have to add a ``__touches__`` property containing the names of the relationships:

.. code-block:: python

    class Comment(Model):

        __touches__ = ['posts']

        @property
        def post(self):
            return self.belongs_to(Post)

Now, when you update a ``Comment``, the owning ``Post`` will have its ``updated_at`` column updated.


Working with pivot table
========================

Working with many-to-many reationships requires the presence of an intermediate table. Eloquent makes it easy to
interact with this table. Let's take the ``User`` and ``Roles`` models and see how you can access the ``pivot`` table:

.. code-block:: python

    user = User.find(1)

    for role in user.roles:
        print(role.pivot.created_at)

Note that each retrieved ``Role`` model is automatically assigned a ``pivot`` attribute. This attribute contains e model
instance representing the intermediate table, and can be used as any other model.

By default, only the keys will be present on the ``pivot`` object. If your pivot table contains extra attributes,
you must specify them when defining the relationship:

.. code-block:: python

    return self.belongs_to_many(Role).with_pivot('foo', 'bar')

Now the ``foo`` and ``bar`` attributes will be accessible on the ``pivot`` object for the ``Role`` model.

If you want your pivot table to have automatically maintained ``created_at`` and ``updated_at`` timestamps,
use the ``with_timestamps`` method on the relationship definition:

.. code-block:: python

    return self.belongs_to_many(Role).with_timestamps()


Deleting records on a pivot table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To delete all records on the pivot table for a model, you can use the ``detach`` method:

.. code-block:: python

    User.find(1).roles().detach()


Updating a record on the pivot table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you may need to update your pivot table, but not detach it.
If you wish to update your pivot table in place you may use ``update_existing_pivot`` method like so:

.. code-block:: python

    User.find(1).roles().update_existing_pivot(role_id, attributes)


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

If you whish to customize the format of your timestamps (the default is the ISO Format) that will be returned when using the ``to_dict``
or the ``to_json`` methods, you can override the ``get_date_format`` method:

.. code-block:: python

    class User(Model):

        def get_date_format():
            return 'DD-MM-YY'


Date mutators
=============

By default, the ORM will convert the ``created_at`` and ``updated_at`` columns to instances of `Arrow <http://arrow.readthedocs.org>`_,
which eases date and datetime manipulation while behaving pretty much like the native Python date and datetime.

You can customize which fields are automatically mutated, by either adding them with the ``__dates__`` property or
by completely overriding the ``get_dates`` method:

.. code-block:: python

    class User(Model):

        __dates__ = ['synchronized_at']

.. code-block:: python

    class User(Model):

        def get_dates():
            return ['created_at']

When a column is considered a date, you can set its value to a UNIX timestamp, a date string ``YYYY-MM-DD``,
a datetime string, a native ``date`` or ``datetime`` and of course an ``Arrow`` instance.

To completely disable date mutations, simply return an empty list from the ``get_dates`` method.

.. code-block:: python

    class User(Model):

        def get_dates():
            return []


Attributes casting
==================

If you have some attributes that you want to always convert to another data-type,
you may add the attribute to the ``__casts__`` property of your model.
Otherwise, you will have to define a mutator for each of the attributes, which can be time consuming.
Here is an example of using the ``__casts__`` property:

.. code-block:: python

    __casts__ = {
        'is_admin': 'bool'
    }

Now the ``is_admin`` attribute will always be cast to a boolean when you access it,
even if the underlying value is stored in the database as an integer.
Other supported cast types are: ``int``, ``float``, ``str``, ``bool``, ``dict``, ``list``.

The ``dict`` cast is particularly useful for working with columns that are stored as serialized JSON.
For example, if your database has a TEXT type field that contains serialized JSON,
adding the ``dict`` cast to that attribute will automatically deserialize the attribute
to a dictionary when you access it on your model:

.. code-block:: python

    __casts__ = {
        'options': 'dict'
    }

Now, when you utilize the model:

.. code-block:: python

    user = User.find(1)

    # options is a dict
    options = user.options

    # options is automatically serialized back to JSON
    user.options = {'foo': 'bar'}


Converting to dictionaries / JSON
=================================

Converting a model to a dictionary
----------------------------------

When building JSON APIs, you may often need to convert your models and relationships to dictionaries or JSON.
So, Eloquent includes methods for doing so. To convert a model and its loaded relationship to a dictionary,
you may use the ``to_dict`` method:

.. code-block:: python

    user = User.with('roles').first()

    return user.to_dict()

Note that entire collections of models can also be converted to dictionaries:

.. code-block:: python

    return User.all().to_dict()


Converting a model to JSON
--------------------------

To convert a model to JSON, you can use the ``to_json`` method!

.. code-block:: python

    return User.find(1).to_json()


Hiding attributes from dictionary or JSON conversion
----------------------------------------------------

Sometimes you may wish to limit the attributes that are included in you model's dictionary or JSON form,
such as passwords. To do so, add a ``__hidden__`` property definition to you model:

.. code-block:: python

    class User(model):

        __hidden__ = ['password']

Alternatively, you may use the ``__visible__`` property to define a whitelist:

.. code-block:: python

    __visible__ = ['first_name', 'last_name']
