.. _Testing:

Testing
#######

.. _ModelFactories:

Model Factories
===============

When testing, it is common to need to insert a few records into your database before executing your test.
Instead of manually specifying the value of each column when you create this test data,
Orator allows you to define a default set of attributes for each of your models using "factories":

.. code-block:: python

    from orator.orm import Factory

    factory = Factory()

    @factory.define(User)
    def users_factory(faker):
        return {
            'name': faker.name(),
            'email': faker.email()
        }


Within the function (here ``users_factory``), which serves as the factory definition,
you can return the default test values of all attributes on the model.
The function will receive an instance of the `Faker <https://github.com/joke2k/faker>`_ library,
which allows you to conveniently generate various kinds of random data for testing.


Multiple Factory Types
----------------------

Sometimes you may wish to have multiple factories for the same model class.
For example, perhaps you would like to have a factory for "Administrator" users in addition to normal users.
You can define these factories using the ``define_as`` method:

.. code-block:: python

    @factory.define_as(User, 'admin')
    def admins_factory(faker):
        return {
            'name': faker.name(),
            'email': faker.email(),
            'admin': True
        }

Instead of duplicating all of the attributes from your base user factory,
you can use the ``raw`` method to retrieve the base attributes.
Once you have the attributes, simply supplement them with any additional values you require:

.. code-block:: python

    @factory.define_as(User, 'admin')
    def admins_factory(faker):
        user = factory.raw(User)

        user.update({
            'admin': True
        })

        return user


Using Factories In Tests
------------------------

Once you have defined your factories, you can use them in your tests or database seed files
to generate model instances calling the ``Factory`` instance.
So, let's take a look at a few examples of creating models.
First, we'll use the ``make`` method, which creates models but does not save them to the database:

.. code-block:: python

    def test_database():
        user = factory(User).make()

        # Use model in tests


If you would like to override some of the default values of your models,
you can pass keyword arguments to the ``make`` method.
Only the specified values will be replaced while the rest of the values remain
set to their default values as specified by the factory:

.. code-block:: python

    def test_database():
        user = factory(User).make(name='John')

You can also create a ``Collection`` of many models or create models of a given type:

.. code-block:: python

    # Create 3 User instances
    users = factory(User, 3).make()

    # Create a User "admin" instance
    admin = factory(User, 'admin').make()

    # Create three User "admin" instances
    admins = factory(User, 'admin', 3).make()


Persisting Factory Models
-------------------------

The ``create`` method not only creates the model instances,
but also saves them to the database using models' ``save`` method:

.. code-block:: python

    def test_database():
        user = factory(User).create()

        # Use model in tests

Again, you can override attributes on the model by passing an array to the ``create`` method:

.. code-block:: python

    def test_database():
        user = factory(User).create(name='John')


Adding Relations To Models
--------------------------

You may even persist multiple models to the database.
In this example, we'll even attach a relation to the created models.
When using the ``create`` method to create multiple models, a ``Collection`` instance is returned,
allowing you to use any of the convenient functions provided by the collection, such as ``each``:

.. code-block:: python

    users = factory(User, 3).create()
    users.each(lambda u: u.save(factory(Post).make()))
