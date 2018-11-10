# -*- coding: utf-8 -*-

import simplejson as json
import pendulum
import inflection
import inspect
import uuid
import datetime
from warnings import warn
from six import add_metaclass
from collections import OrderedDict
from ..utils import basestring, deprecated
from ..exceptions.orm import MassAssignmentError, RelatedClassNotFound
from ..query import QueryBuilder
from .builder import Builder
from .collection import Collection
from .relations import (
    Relation,
    HasOne,
    HasMany,
    BelongsTo,
    BelongsToMany,
    HasManyThrough,
    MorphOne,
    MorphMany,
    MorphTo,
    MorphToMany,
)
from .relations.wrapper import Wrapper, BelongsToManyWrapper
from .utils import mutator, accessor
from .scopes import Scope
from ..events import Event


class ModelRegister(dict):
    def __init__(self, *args, **kwargs):
        self.inverse = {}

        super(ModelRegister, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super(ModelRegister, self).__setitem__(key, value)

        self.inverse[value] = key

    def __delitem__(self, key):
        del self.inverse[self[key]]

        super(ModelRegister, self).__delitem__(key)


class MetaModel(type):

    __register__ = {}

    def __init__(cls, *args, **kwargs):
        name = cls.__table__ or inflection.tableize(cls.__name__)
        cls._register[name] = cls

        super(MetaModel, cls).__init__(*args, **kwargs)

    def __getattr__(cls, item):
        try:
            return type.__getattribute__(cls, item)
        except AttributeError:
            query = cls.query()

            return getattr(query, item)


@add_metaclass(MetaModel)
class Model(object):

    __connection__ = None

    __table__ = None

    __primary_key__ = "id"

    __incrementing__ = True

    __fillable__ = []
    __guarded__ = ["*"]
    __unguarded__ = False

    __hidden__ = []
    __visible__ = []
    __appends__ = []

    __timestamps__ = True
    __dates__ = []

    __casts__ = {}

    __touches__ = []

    __morph_name__ = None

    _per_page = 15

    _with = []

    _booted = {}
    _global_scopes = {}
    _registered = []

    _accessor_cache = {}
    _mutator_cache = {}

    __resolver = None
    __columns__ = []

    __dispatcher__ = Event()
    __observables__ = []

    _register = ModelRegister()

    __attributes__ = {}

    many_methods = ["belongs_to_many", "morph_to_many", "morphed_by_many"]

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

    def __init__(self, _attributes=None, **attributes):
        """
        :param attributes: The instance attributes
        """
        self._boot_if_not_booted()

        self._exists = False
        self._original = {}

        # Setting default attributes' values
        self._attributes = dict((k, v) for k, v in self.__attributes__.items())
        self._relations = {}

        self.sync_original()

        if _attributes is not None:
            attributes.update(_attributes)

        self.fill(**attributes)

    def _boot_if_not_booted(self):
        """
        Check if the model needs to be booted and if so, do it.
        """
        klass = self.__class__

        if not klass._booted.get(klass):
            klass._booted[klass] = True

            self._fire_model_event("booting")

            klass._boot()

            self._fire_model_event("booted")

    @classmethod
    def _boot(cls):
        """
        The booting method of the model.
        """
        cls._accessor_cache[cls] = {}
        cls._mutator_cache[cls] = {}

        for name, method in cls.__dict__.items():
            if isinstance(method, accessor):
                cls._accessor_cache[cls][method.attribute] = method
            elif isinstance(method, mutator):
                cls._mutator_cache[cls][method.attribute] = method

        cls._boot_mixins()

    @classmethod
    def _boot_columns(cls):
        connection = cls.resolve_connection()
        columns = connection.get_schema_manager().list_table_columns(
            cls.__table__ or inflection.tableize(cls.__name__)
        )
        cls.__columns__ = list(columns.keys())

    @classmethod
    def _boot_mixins(cls):
        """
        Boot the mixins
        """
        for mixin in cls.__bases__:
            # if mixin == Model:
            #    continue

            method = "boot_%s" % inflection.underscore(mixin.__name__)
            if hasattr(mixin, method):
                getattr(mixin, method)(cls)

    @classmethod
    def add_global_scope(cls, scope, implementation=None):
        """
        Register a new global scope on the model.

        :param scope: The scope to register
        :type scope: orator.orm.scopes.scope.Scope or callable or str

        :param implementation: The scope implementation
        :type implementation: callbale or None
        """
        if cls not in cls._global_scopes:
            cls._global_scopes[cls] = OrderedDict()

        if isinstance(scope, basestring) and implementation is not None:
            cls._global_scopes[cls][scope] = implementation
        elif callable(scope):
            cls._global_scopes[cls][uuid.uuid4().hex] = scope
        elif isinstance(scope, Scope):
            cls._global_scopes[cls][scope.__class__] = scope
        else:
            raise Exception("Global scope must be an instance of Scope or a callable")

    @classmethod
    def has_global_scope(cls, scope):
        """
        Determine if a model has a global scope.

        :param scope: The scope to register
        :type scope: orator.orm.scopes.scope.Scope or str
        """
        return cls.get_global_scope(scope) is not None

    @classmethod
    def get_global_scope(cls, scope):
        """
        Get a global scope registered with the model.

        :param scope: The scope to register
        :type scope: orator.orm.scopes.scope.Scope or str
        """
        for key, value in cls._global_scopes[cls].items():
            if isinstance(scope, key):
                return value

    def get_global_scopes(self):
        """
        Get the global scopes for this class instance.

        :rtype: dict
        """
        return self.__class__._global_scopes.get(self.__class__, {})

    @classmethod
    def observe(cls, observer):
        """
        Register an observer with the Model.

        :param observer: The observer
        """
        for event in cls.get_observable_events():
            if hasattr(observer, event):
                cls._register_model_event(event, getattr(observer, event))

    def fill(self, _attributes=None, **attributes):
        """
        Fill the model with attributes.

        :param attributes: The instance attributes
        :type attributes: dict

        :return: The model instance
        :rtype: Model

        :raises: MassAssignmentError
        """
        if _attributes is not None:
            attributes.update(_attributes)

        totally_guarded = self.totally_guarded()

        for key, value in self._fillable_from_dict(attributes).items():
            key = self._remove_table_from_key(key)

            if self.is_fillable(key):
                self.set_attribute(key, value)
            elif totally_guarded:
                raise MassAssignmentError(key)

        return self

    def force_fill(self, _attributes=None, **attributes):
        """
        Fill the model with attributes. Force mass assignment.

        :param attributes: The instance attributes
        :type attributes: dict

        :return: The model instance
        :rtype: Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        self.unguard()

        self.fill(**attributes)

        self.reguard()

        return self

    def _fillable_from_dict(self, attributes):
        """
        Get the fillable attributes from a given dictionary.

        :type attributes: dict

        :return: The fillable attributes
        :rtype: dict
        """
        if self.__fillable__ and not self.__unguarded__:
            return {x: attributes[x] for x in attributes if x in self.__fillable__}

        return attributes

    def new_instance(self, attributes=None, exists=False):
        """
        Create a new instance for the given model.

        :param attributes: The instance attributes
        :type attributes: dict

        :param exists:
        :type exists: bool

        :return: A new instance for the current model
        :rtype: Model
        """
        if attributes is None:
            attributes = {}

        model = self.__class__(**attributes)

        model.set_connection(self.get_connection_name())
        model.set_exists(exists)

        return model

    def new_from_builder(self, attributes=None, connection=None):
        """
        Create a new model instance that is existing.

        :param attributes: The model attributes
        :type attributes: dict

        :param connection: The connection name
        :type connection: str

        :return: A new instance for the current model
        :rtype: Model
        """
        model = self.new_instance({}, True)

        if attributes is None:
            attributes = {}

        model.set_raw_attributes(attributes, True)

        model.set_connection(connection or self.__connection__)

        return model

    @classmethod
    def hydrate(cls, items, connection=None):
        """
        Create a collection of models from plain lists.

        :param items:
        :param connection:
        :return:
        """
        instance = cls().set_connection(connection)

        collection = instance.new_collection(items)

        return collection.map(lambda item: instance.new_from_builder(item))

    @classmethod
    def hydrate_raw(cls, query, bindings=None, connection=None):
        """
        Create a collection of models from a raw query.

        :param query: The SQL query
        :type query: str

        :param bindings: The query bindings
        :type bindings: list

        :param connection: The connection name

        :rtype: Collection
        """
        instance = cls().set_connection(connection)

        items = instance.get_connection().select(query, bindings)

        return cls.hydrate(items, connection)

    @classmethod
    def create(cls, _attributes=None, **attributes):
        """
        Save a new model an return the instance.

        :param attributes: The instance attributes
        :type attributes: dict

        :return: The new instance
        :rtype: Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        model = cls(**attributes)

        model.save()

        return model

    @classmethod
    def force_create(cls, **attributes):
        """
        Save a new model an return the instance. Allow mass assignment.

        :param attributes: The instance attributes
        :type attributes: dict

        :return: The new instance
        :rtype: Model
        """
        cls.unguard()

        model = cls.create(**attributes)

        cls.reguard()

        return model

    @classmethod
    def first_or_create(cls, **attributes):
        """
        Get the first record matching the attributes or create it.

        :param attributes: The instance attributes
        :type attributes: dict

        :return: The new instance
        :rtype: Model
        """
        instance = cls().new_query_without_scopes().where(attributes).first()

        if instance is not None:
            return instance

        return cls.create(**attributes)

    @classmethod
    def first_or_new(cls, **attributes):
        """
        Get the first record matching the attributes or instantiate it.

        :param attributes: The instance attributes
        :type attributes: dict

        :return: The new instance
        :rtype: Model
        """
        instance = cls().new_query_without_scopes().where(attributes).first()

        if instance is not None:
            return instance

        return cls(**attributes)

    @classmethod
    def update_or_create(cls, attributes, values=None):
        """
        Create or update a record matching the attributes, and fill it with values.

        :param attributes: The instance attributes
        :type attributes: dict

        :param values: The values
        :type values: dict

        :return: The new instance
        :rtype: Model
        """
        instance = cls.first_or_new(**attributes)

        if values is None:
            values = {}

        instance.fill(**values).save()

        return instance

    @classmethod
    def query(cls):
        """
        Begin querying the model.

        :return: A Builder instance
        :rtype: orator.orm.Builder
        """
        return cls().new_query()

    @classmethod
    def on(cls, connection=None):
        """
        Begin querying the model on a given connection.

        :param connection: The connection name
        :type connection: str

        :return: A Builder instance
        :rtype: orator.orm.Builder
        """
        instance = cls()

        instance.set_connection(connection)

        return instance.new_query()

    @classmethod
    def on_write_connection(cls):
        """
        Begin querying the model on the write connection.

        :return: A Builder instance
        :rtype: QueryBuilder
        """
        instance = cls()

        return instance.new_query().use_write_connection()

    @classmethod
    def all(cls, columns=None):
        """
        Get all og the models from the database.

        :param columns: The columns to retrieve
        :type columns: list

        :return: A Collection instance
        :rtype: Collection
        """
        instance = cls()

        return instance.new_query().get(columns)

    @classmethod
    def find(cls, id, columns=None):
        """
        Find a model by its primary key.

        :param id: The id of the model
        :type id: mixed

        :param columns: The columns to retrieve
        :type columns: list

        :return: Either a Model instance or a Collection
        :rtype: Model
        """
        instance = cls()

        if isinstance(id, list) and not id:
            return instance.new_collection()

        if columns is None:
            columns = ["*"]

        return instance.new_query().find(id, columns)

    @classmethod
    def find_or_new(cls, id, columns=None):
        """
        Find a model by its primary key or return new instance.

        :param id: The id of the model
        :type id: mixed

        :param columns: The columns to retrieve
        :type columns: list

        :return: A Model instance
        :rtype: Model
        """
        instance = cls.find(id, columns)

        if instance is not None:
            return instance

        return cls()

    def fresh(self, with_=None):
        """
        Reload a fresh instance from the database.

        :param with_: The list of relations to eager load
        :type with_: list

        :return: The current model instance
        :rtype: Model
        """
        if with_ is None:
            with_ = ()

        key = self.get_key_name()

        if self.exists:
            return self.with_(*with_).where(key, self.get_key()).first()

    def load(self, *relations):
        """
        Eager load relations on the model

        :param relations: The relations to eager load
        :type relations: str or list

        :return: The current model instance
        :rtype: Model
        """
        query = self.new_query().with_(*relations)

        query.eager_load_relations([self])

        return self

    @classmethod
    def with_(cls, *relations):
        """
        Begin querying a model with eager loading

        :param relations: The relations to eager load
        :type relations: str or list

        :return: A Builder instance
        :rtype: Builder
        """
        instance = cls()

        return instance.new_query().with_(*relations)

    def has_one(
        self, related, foreign_key=None, local_key=None, relation=None, _wrapped=True
    ):
        """
        Define a one to one relationship.

        :param related: The related model:
        :type related: Model or str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param local_key: The local key
        :type local_key: str

        :param relation: The name of the relation (defaults to method name)
        :type relation: str

        :rtype: HasOne
        """
        if relation is None:
            name = inspect.stack()[1][3]
        else:
            name = relation

        if name in self._relations:
            return self._relations[name]

        if not foreign_key:
            foreign_key = self.get_foreign_key()

        instance = self._get_related(related, True)

        if not local_key:
            local_key = self.get_key_name()

        rel = HasOne(
            instance.new_query(),
            self,
            "%s.%s" % (instance.get_table(), foreign_key),
            local_key,
        )

        if _wrapped:
            warn(
                "Using has_one method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[name] = rel

        return rel

    def morph_one(
        self,
        related,
        name,
        type_column=None,
        id_column=None,
        local_key=None,
        relation=None,
        _wrapped=True,
    ):
        """
        Define a polymorphic one to one relationship.

        :param related: The related model:
        :type related: Model or str

        :param type_column: The name of the type column
        :type type_column: str

        :param id_column: The name of the id column
        :type id_column: str

        :param local_key: The local key
        :type local_key: str

        :param relation: The name of the relation (defaults to method name)
        :type relation: str

        :rtype: HasOne
        """
        if relation is None:
            relation = inspect.stack()[1][3]

        if relation in self._relations:
            return self._relations[name]

        instance = self._get_related(related, True)

        type_column, id_column = self.get_morphs(name, type_column, id_column)

        table = instance.get_table()

        if not local_key:
            local_key = self.get_key_name()

        rel = MorphOne(
            instance.new_query(),
            self,
            "%s.%s" % (table, type_column),
            "%s.%s" % (table, id_column),
            local_key,
        )

        if _wrapped:
            warn(
                "Using morph_one method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[relation] = rel

        return rel

    def belongs_to(
        self, related, foreign_key=None, other_key=None, relation=None, _wrapped=True
    ):
        """
        Define an inverse one to one or many relationship.

        :param related: The related model:
        :type related: Model or str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param other_key: The other key
        :type other_key: str

        :type relation: str

        :rtype: BelongsTo
        """
        if relation is None:
            relation = inspect.stack()[1][3]

        if relation in self._relations:
            return self._relations[relation]

        if foreign_key is None:
            foreign_key = "%s_id" % inflection.underscore(relation)

        instance = self._get_related(related, True)

        query = instance.new_query()

        if not other_key:
            other_key = instance.get_key_name()

        rel = BelongsTo(query, self, foreign_key, other_key, relation)

        if _wrapped:
            warn(
                "Using belongs_to method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[relation] = rel

        return rel

    def morph_to(self, name=None, type_column=None, id_column=None, _wrapped=True):
        """
        Define a polymorphic, inverse one-to-one or many relationship.

        :param name: The name of the relation
        :type name: str

        :param type_column: The type column
        :type type_column: str

        :param id_column: The id column
        :type id_column: str

        :rtype: MorphTo
        """
        if not name:
            name = inspect.stack()[1][3]

        if name in self._relations:
            return self._relations[name]

        type_column, id_column = self.get_morphs(name, type_column, id_column)

        # If the type value is null it is probably safe to assume we're eager loading
        # the relationship. When that is the case we will pass in a dummy query as
        # there are multiple types in the morph and we can't use single queries.
        if not hasattr(self, type_column):
            return MorphTo(self.new_query(), self, id_column, None, type_column, name)

        # If we are not eager loading the relationship we will essentially treat this
        # as a belongs-to style relationship since morph-to extends that class and
        # we will pass in the appropriate values so that it behaves as expected.
        klass = self.get_actual_class_for_morph(getattr(self, type_column))

        instance = klass()
        instance.set_connection(self.get_connection_name())

        rel = MorphTo(
            instance.new_query(),
            self,
            id_column,
            instance.get_key_name(),
            type_column,
            name,
        )

        if _wrapped:
            warn(
                "Using morph_to method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[name] = rel

        return rel

    def get_actual_class_for_morph(self, slug):
        """
        Retrieve the class from a slug.

        :param slug: The slug
        :type slug: str
        """
        for cls in self.__class__._register.values():
            morph_name = cls.get_morph_name()
            if morph_name == slug:
                return cls

    def has_many(
        self, related, foreign_key=None, local_key=None, relation=None, _wrapped=True
    ):
        """
        Define a one to many relationship.

        :param related: The related model
        :type related: Model or str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param local_key: The local key
        :type local_key: str

        :param relation: The name of the relation (defaults to method name)
        :type relation: str

        :rtype: HasOne
        """
        if relation is None:
            name = inspect.stack()[1][3]
        else:
            name = relation

        if name in self._relations:
            return self._relations[name]

        if not foreign_key:
            foreign_key = self.get_foreign_key()

        instance = self._get_related(related, True)

        if not local_key:
            local_key = self.get_key_name()

        rel = HasMany(
            instance.new_query(),
            self,
            "%s.%s" % (instance.get_table(), foreign_key),
            local_key,
        )

        if _wrapped:
            warn(
                "Using has_many method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[name] = rel

        return rel

    def has_many_through(
        self,
        related,
        through,
        first_key=None,
        second_key=None,
        relation=None,
        _wrapped=True,
    ):
        """
        Define a has-many-through relationship.

        :param related: The related model
        :type related: Model or str

        :param through: The through model
        :type through: Model or str

        :param first_key: The first key
        :type first_key: str

        :param second_key: The second_key
        :type second_key: str

        :param relation: The name of the relation (defaults to method name)
        :type relation: str

        :rtype: HasManyThrough
        """
        if relation is None:
            name = inspect.stack()[1][3]
        else:
            name = relation

        if name in self._relations:
            return self._relations[name]

        through = self._get_related(through, True)

        if not first_key:
            first_key = self.get_foreign_key()

        if not second_key:
            second_key = through.get_foreign_key()

        rel = HasManyThrough(
            self._get_related(related)().new_query(),
            self,
            through,
            first_key,
            second_key,
        )

        if _wrapped:
            warn(
                "Using has_many_through method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[name] = rel

        return rel

    def morph_many(
        self,
        related,
        name,
        type_column=None,
        id_column=None,
        local_key=None,
        relation=None,
        _wrapped=True,
    ):
        """
        Define a polymorphic one to many relationship.

        :param related: The related model:
        :type related: Model or str

        :param type_column: The name of the type column
        :type type_column: str

        :param id_column: The name of the id column
        :type id_column: str

        :param local_key: The local key
        :type local_key: str

        :param relation: The name of the relation (defaults to method name)
        :type relation: str

        :rtype: MorphMany
        """
        if relation is None:
            relation = inspect.stack()[1][3]

        if relation in self._relations:
            return self._relations[relation]

        instance = self._get_related(related, True)

        type_column, id_column = self.get_morphs(name, type_column, id_column)

        table = instance.get_table()

        if not local_key:
            local_key = self.get_key_name()

        rel = MorphMany(
            instance.new_query(),
            self,
            "%s.%s" % (table, type_column),
            "%s.%s" % (table, id_column),
            local_key,
        )

        if _wrapped:
            warn(
                "Using morph_many method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[name] = rel

        return rel

    def belongs_to_many(
        self,
        related,
        table=None,
        foreign_key=None,
        other_key=None,
        relation=None,
        _wrapped=True,
    ):
        """
        Define a many-to-many relationship.

        :param related: The related model
        :type related: Model or str

        :param table: The pivot table
        :type table: str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param other_key: The other key
        :type other_key: str

        :type relation: str

        :rtype: BelongsToMany
        """
        if relation is None:
            relation = inspect.stack()[1][3]

        if relation in self._relations:
            return self._relations[relation]

        if not foreign_key:
            foreign_key = self.get_foreign_key()

        instance = self._get_related(related, True)

        if not other_key:
            other_key = instance.get_foreign_key()

        if table is None:
            table = self.joining_table(instance)

        query = instance.new_query()

        rel = BelongsToMany(query, self, table, foreign_key, other_key, relation)

        if _wrapped:
            warn(
                "Using belongs_to_many method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = BelongsToManyWrapper(rel)

        self._relations[relation] = rel

        return rel

    def morph_to_many(
        self,
        related,
        name,
        table=None,
        foreign_key=None,
        other_key=None,
        inverse=False,
        relation=None,
        _wrapped=True,
    ):
        """
        Define a polymorphic many-to-many relationship.

        :param related: The related model:
        :type related: Model or str

        :param name: The relation name
        :type name: str

        :param table: The pivot table
        :type table: str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param other_key: The other key
        :type other_key: str

        :param relation: The name of the relation (defaults to method name)
        :type relation: str

        :rtype: MorphToMany
        """
        if relation is None:
            caller = inspect.stack()[1][3]
        else:
            caller = relation

        if caller in self._relations:
            return self._relations[caller]

        if not foreign_key:
            foreign_key = name + "_id"

        instance = self._get_related(related, True)

        if not other_key:
            other_key = instance.get_foreign_key()

        query = instance.new_query()

        if not table:
            table = inflection.pluralize(name)

        rel = MorphToMany(
            query, self, name, table, foreign_key, other_key, caller, inverse
        )

        if _wrapped:
            warn(
                "Using morph_to_many method directly is deprecated. "
                "Use the appropriate decorator instead.",
                category=DeprecationWarning,
            )

            rel = Wrapper(rel)

        self._relations[caller] = rel

        return rel

    def morphed_by_many(
        self,
        related,
        name,
        table=None,
        foreign_key=None,
        other_key=None,
        relation=None,
        _wrapped=False,
    ):
        """
        Define a polymorphic many-to-many relationship.

        :param related: The related model:
        :type related: Model or str

        :param name: The relation name
        :type name: str

        :param table: The pivot table
        :type table: str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param other_key: The other key
        :type other_key: str

        :param relation: The name of the relation (defaults to method name)
        :type relation: str

        :rtype: MorphToMany
        """
        if not foreign_key:
            foreign_key = self.get_foreign_key()

        if not other_key:
            other_key = name + "_id"

        return self.morph_to_many(
            related, name, table, foreign_key, other_key, True, relation, _wrapped
        )

    def _get_related(self, related, as_instance=False):
        """
        Get the related class.

        :param related: The related model or table
        :type related: Model or str

        :rtype: Model class
        """
        if not isinstance(related, basestring) and issubclass(related, Model):
            if as_instance:
                instance = related()
                instance.set_connection(self.get_connection_name())

                return instance

            return related

        related_class = self.__class__._register.get(related)

        if related_class:
            if as_instance:
                instance = related_class()
                instance.set_connection(self.get_connection_name())

                return instance

            return related_class

        raise RelatedClassNotFound(related)

    def joining_table(self, related):
        """
        Get the joining table name for a many-to-many relation

        :param related: The related model
        :type related: Model

        :rtype: str
        """
        base = self.get_table()

        related = related.get_table()

        models = sorted([related, base])

        return "_".join(models)

    @classmethod
    def destroy(cls, *ids):
        """
        Destroy the models for the given IDs

        :param ids: The ids of the models to destroy
        :type ids: tuple

        :return: The number of models destroyed
        :rtype: int
        """
        count = 0

        if len(ids) == 1 and isinstance(ids[0], list):
            ids = ids[0]

        ids = list(ids)

        instance = cls()

        key = instance.get_key_name()

        for model in instance.new_query().where_in(key, ids).get():
            if model.delete():
                count += 1

        return count

    def delete(self):
        """
        Delete the model from the database.

        :rtype: bool or None

        :raises: Exception
        """
        if self.__primary_key__ is None:
            raise Exception("No primary key defined on the model.")

        if self._exists:
            if self._fire_model_event("deleting") is False:
                return False

            self.touch_owners()

            self._perform_delete_on_model()

            self._exists = False

            self._fire_model_event("deleted")

            return True

    def force_delete(self):
        """
        Force a hard delete on a soft deleted model.
        """
        return self.delete()

    def _perform_delete_on_model(self):
        """
        Perform the actual delete query on this model instance.
        """
        if hasattr(self, "_do_perform_delete_on_model"):
            return self._do_perform_delete_on_model()

        return self.new_query().where(self.get_key_name(), self.get_key()).delete()

    @classmethod
    def saving(cls, callback):
        """
        Register a saving model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("saving", callback)

    @classmethod
    def saved(cls, callback):
        """
        Register a saved model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("saved", callback)

    @classmethod
    def updating(cls, callback):
        """
        Register a updating model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("updating", callback)

    @classmethod
    def updated(cls, callback):
        """
        Register a updated model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("updated", callback)

    @classmethod
    def creating(cls, callback):
        """
        Register a creating model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("creating", callback)

    @classmethod
    def created(cls, callback):
        """
        Register a created model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("created", callback)

    @classmethod
    def deleting(cls, callback):
        """
        Register a deleting model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("deleting", callback)

    @classmethod
    def deleted(cls, callback):
        """
        Register a deleted model event with the dispatcher.

        :type callback: callable
        """
        cls._register_model_event("deleted", callback)

    @classmethod
    def flush_event_listeners(cls):
        """
        Remove all of the event listeners for the model.
        """
        if not cls.__dispatcher__:
            return

        for event in cls.get_observable_events():
            cls.__dispatcher__.forget("%s: %s" % (event, cls.__name__))

    @classmethod
    def _register_model_event(cls, event, callback):
        """
        Register a model event with the dispatcher.

        :param event: The event
        :type event: str

        :param callback: The callback
        :type callback: callable
        """
        if cls.__dispatcher__:
            cls.__dispatcher__.listen("%s: %s" % (event, cls.__name__), callback)

    @classmethod
    def get_observable_events(cls):
        """
        Get the observable event names.

        :rtype: list
        """
        default_events = [
            "creating",
            "created",
            "updating",
            "updated",
            "deleting",
            "deleted",
            "saving",
            "saved",
            "restoring",
            "restored",
        ]

        return default_events + cls.__observables__

    def _increment(self, column, amount=1):
        """
        Increment a column's value

        :param column: The column to increment
        :type column: str

        :param amount: The amount by which to increment
        :type amount: int

        :return: The new column value
        :rtype: int
        """
        return self._increment_or_decrement(column, amount, "increment")

    def _decrement(self, column, amount=1):
        """
        Decrement a column's value

        :param column: The column to increment
        :type column: str

        :param amount: The amount by which to increment
        :type amount: int

        :return: The new column value
        :rtype: int
        """
        return self._increment_or_decrement(column, amount, "decrement")

    def _increment_or_decrement(self, column, amount, method):
        """
        Runthe increment or decrement method on the model

        :param column: The column to increment or decrement
        :type column: str

        :param amount: The amount by which to increment or decrement
        :type amount: int

        :param method: The method
        :type method: str

        :return: The new column value
        :rtype: int
        """
        query = self.new_query()

        if not self._exists:
            return getattr(query, method)(column, amount)

        self._increment_or_decrement_attribute_value(column, amount, method)

        query = query.where(self.get_key_name(), self.get_key())

        return getattr(query, method)(column, amount)

    def _increment_or_decrement_attribute_value(self, column, amount, method):
        """
        Increment the underlying attribute value and sync with original.

        :param column: The column to increment or decrement
        :type column: str

        :param amount: The amount by which to increment or decrement
        :type amount: int

        :param method: The method
        :type method: str

        :return: None
        """
        setattr(
            self,
            column,
            getattr(self, column) + (amount if method == "increment" else amount * -1),
        )

        self.sync_original_attribute(column)

    def update(self, _attributes=None, **attributes):
        """
        Update the model in the database.

        :param attributes: The model attributes
        :type attributes: dict

        :return: The number of rows affected
        :rtype: int
        """
        if _attributes is not None:
            attributes.update(_attributes)

        if not self._exists:
            return self.new_query().update(**attributes)

        return self.fill(**attributes).save()

    def push(self):
        """
        Save the model and all of its relationship.
        """
        if not self.save():
            return False

        for models in self._relations.values():
            if isinstance(models, Collection):
                models = models.all()
            else:
                models = [models]

            for model in models:
                if not model:
                    continue

                if not model.push():
                    return False

        return True

    def save(self, options=None):
        """
        Save the model to the database.
        """
        if options is None:
            options = {}

        query = self.new_query()

        if self._fire_model_event("saving") is False:
            return False

        if self._exists:
            saved = self._perform_update(query, options)
        else:
            saved = self._perform_insert(query, options)

        if saved:
            self._finish_save(options)

        return saved

    def _finish_save(self, options):
        """
        Finish processing on a successful save operation.
        """
        self._fire_model_event("saved")

        self.sync_original()

        if options.get("touch", True):
            self.touch_owners()

    def _perform_update(self, query, options=None):
        """
        Perform a model update operation.

        :param query: A Builder instance
        :type query: Builder

        :param options: Extra options
        :type options: dict
        """
        if options is None:
            options = {}

        dirty = self.get_dirty()

        if len(dirty):
            if self._fire_model_event("updating") is False:
                return False

            if self.__timestamps__ and options.get("timestamps", True):
                self._update_timestamps()

            dirty = self.get_dirty()

            if len(dirty):
                self._set_keys_for_save_query(query).update(dirty)

                self._fire_model_event("updated")

        return True

    def _perform_insert(self, query, options=None):
        """
        Perform a model update operation.

        :param query: A Builder instance
        :type query: Builder

        :param options: Extra options
        :type options: dict
        """
        if options is None:
            options = {}

        if self._fire_model_event("creating") is False:
            return False

        if self.__timestamps__ and options.get("timestamps", True):
            self._update_timestamps()

        attributes = self._attributes

        if self.__incrementing__:
            self._insert_and_set_id(query, attributes)
        else:
            query.insert(attributes)

        self._exists = True

        self._fire_model_event("created")

        return True

    def _insert_and_set_id(self, query, attributes):
        """
        Insert the given attributes and set the ID on the model.

        :param query: A Builder instance
        :type query: Builder

        :param attributes: The attributes to insert
        :type attributes: dict
        """
        key_name = self.get_key_name()

        id = query.insert_get_id(attributes, key_name)

        self.set_attribute(key_name, id)

    def touch_owners(self):
        """
        Touch the owning relations of the model.
        """
        for relation in self.__touches__:
            if hasattr(self, relation):
                _relation = getattr(self, relation)

                if _relation:
                    _relation.touch()
                    _relation.touch_owners()

    def touches(self, relation):
        """
        Determine if a model touches a given relation.

        :param relation: The relation to check.
        :type relation: str

        :rtype: bool
        """
        return relation in self.__touches__

    def _fire_model_event(self, event):
        """
        Fire the given event for the model.

        :type event: str
        """
        if not self.__dispatcher__:
            return True

        # We will append the names of the class to the event to distinguish it from
        # other model events that are fired, allowing us to listen on each model
        # event set individually instead of catching event for all the models.
        event = "%s: %s" % (event, self.__class__.__name__)

        return self.__dispatcher__.fire(event, self)

    def _set_keys_for_save_query(self, query):
        """
        Set the keys for a save update query.

        :param query: A Builder instance
        :type query: Builder

        :return: The Builder instance
        :rtype: Builder
        """
        query.where(self.get_key_name(), self._get_key_for_save_query())

        return query

    def _get_key_for_save_query(self):
        """
        Get the primary key value for a save query.
        """
        if self.get_key_name() in self._original:
            return self._original[self.get_key_name()]

        return self._attributes[self.get_key_name()]

    def touch(self):
        """
        Update the model's timestamps.

        :rtype: bool
        """
        if not self.__timestamps__:
            return False

        self._update_timestamps()

        return self.save()

    def _update_timestamps(self):
        """
        Update the model's timestamps.
        """
        time = self.fresh_timestamp()

        if not self.is_dirty(self.UPDATED_AT) and self._should_set_timestamp(
            self.UPDATED_AT
        ):
            self.set_updated_at(time)

        if (
            not self._exists
            and not self.is_dirty(self.CREATED_AT)
            and self._should_set_timestamp(self.CREATED_AT)
        ):
            self.set_created_at(time)

    def _should_set_timestamp(self, timestamp):
        """
        Determine if a timestamp should be set.

        :param timestamp: The timestamp to check
        :type timestamp: str

        :rtype: bool
        """
        if isinstance(self.__timestamps__, bool):
            return self.__timestamps__

        return timestamp in self.__timestamps__

    def set_created_at(self, value):
        """
        Set the value of the "created at" attribute.

        :param value: The value
        :type value: datetime
        """
        self.set_attribute(self.CREATED_AT, value)

    def set_updated_at(self, value):
        """
        Set the value of the "updated at" attribute.

        :param value: The value
        :type value: datetime
        """
        self.set_attribute(self.UPDATED_AT, value)

    def get_created_at_column(self):
        """
        Get the name of the "created at" column.

        :rtype: str
        """
        return self.CREATED_AT

    def get_updated_at_column(self):
        """
        Get the name of the "updated at" column.

        :rtype: str
        """
        return self.UPDATED_AT

    def fresh_timestamp(self):
        """
        Get a fresh timestamp for the model.

        :return: pendulum.Pendulum
        """
        return pendulum.utcnow()

    def fresh_timestamp_string(self):
        """
        Get a fresh timestamp string for the model.

        :return: str
        """
        return self.from_datetime(self.fresh_timestamp())

    def new_query(self):
        """
        Get a new query builder for the model's table

        :return: A Builder instance
        :rtype: Builder
        """
        builder = self.new_query_without_scopes()

        for identifier, scope in self.get_global_scopes().items():
            builder.with_global_scope(identifier, scope)

        return builder

    def new_query_without_scope(self, scope):
        """
        Get a new query builder for the model's table without a given scope

        :return: A Builder instance
        :rtype: Builder
        """
        builder = self.new_query()

        return builder.without_global_scope(scope)

    def new_query_without_scopes(self):
        """
        Get a new query builder without any scopes.

        :return: A Builder instance
        :rtype: Builder
        """
        builder = self.new_orm_builder(self._new_base_query_builder())

        return builder.set_model(self).with_(*self._with)

    @classmethod
    def query(cls):
        return cls().new_query()

    def new_orm_builder(self, query):
        """
        Create a new orm query builder for the model

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: A Builder instance
        :rtype: Builder
        """
        return Builder(query)

    def _new_base_query_builder(self):
        """
        Get a new query builder instance for the connection.

        :return: A QueryBuilder instance
        :rtype: QueryBuilder
        """
        conn = self.get_connection()

        return conn.query()

    def new_collection(self, models=None):
        """
        Create a new Collection instance.

        :param models: A list of models
        :type models: list

        :return: A new Collection instance
        :rtype: Collection
        """
        if models is None:
            models = []

        return Collection(models)

    def new_pivot(self, parent, attributes, table, exists):
        """
        Create a new pivot model instance.

        :param parent: The parent model
        :type parent: Model

        :param attributes: The pivot attributes
        :type attributes: dict

        :param table: the pivot table
        :type table: str

        :param exists: Whether the pivot exists or not
        :type exists: bool

        :rtype: Pivot
        """
        from .relations.pivot import Pivot

        return Pivot(parent, attributes, table, exists)

    def get_table(self):
        """
        Get the table associated with the model.

        :return: The name of the table
        :rtype: str
        """
        return self.__class__._register.inverse[self.__class__]

    def set_table(self, table):
        """
        Set the table associated with the model.

        :param table: The table name
        :type table: str
        """
        old_table = self.__class__._register.inverse.get(self.__class__, None)
        self.__table__ = table

        if old_table:
            del self.__class__._register[old_table]

        self.__class__._register[self.__table__] = self.__class__

    def get_key(self):
        """
        Get the value of the model's primary key.
        """
        return self.get_attribute(self.get_key_name())

    def get_key_name(self):
        """
        Get the primary key for the model.

        :return: The primary key name
        :rtype: str
        """
        return self.__primary_key__

    def set_key_name(self, name):
        """
        Set the primary key for the model.

        :param name: The primary key name
        :type name: str
        """
        self.__primary_key__ = name

    def get_qualified_key_name(self):
        """
        Get the table qualified key name.

        :rtype: str
        """
        return "%s.%s" % (self.get_table(), self.get_key_name())

    def uses_timestamps(self):
        """
        Determine if the model uses timestamps.

        :rtype: bool
        """
        return self.__timestamps__

    def get_morphs(self, name, type, id):
        """
        Get the polymorphic relationship columns.
        """
        if not type:
            type = name + "_type"

        if not id:
            id = name + "_id"

        return type, id

    @classmethod
    def get_morph_name(cls):
        """
        Get the name for polymorphic relations.
        """
        if not cls.__morph_name__:
            return cls._register.inverse[cls]

        return cls.__morph_name__

    def get_per_page(self):
        """
        Get the number of models to return per page.

        :rtype: int
        """
        return self._per_page

    def get_foreign_key(self):
        """
        Get the default foreign key name for the model

        :rtype: str
        """
        return "%s_id" % inflection.singularize(self.get_table())

    def get_hidden(self):
        """
        Get the hidden attributes for the model.
        """
        return self.__hidden__

    def set_hidden(self, hidden):
        """
        Set the hidden attributes for the model.

        :param hidden: The attributes to add
        :type hidden: list
        """
        self.__hidden__ = hidden

        return self

    def add_hidden(self, *attributes):
        """
        Add hidden attributes to the model.

        :param attributes: The attributes to hide
        :type attributes: list
        """
        self.__hidden__ += attributes

    def get_visible(self):
        """
        Get the visible attributes for the model.
        """
        return self.__visible__

    def set_visible(self, visible):
        """
        Set the visible attributes for the model.

        :param visible: The attributes to make visible
        :type visible: list
        """
        self.__visible__ = visible

        return self

    def add_visible(self, *attributes):
        """
        Add visible attributes to the model.

        :param attributes: The attributes to make visible
        :type attributes: list
        """
        self.__visible__ += attributes

    def get_fillable(self):
        """
        Get the fillable attributes for the model.

        :rtype: list
        """
        return self.__fillable__

    def fillable(self, fillable):
        """
        Set the fillable attributes for the model.

        :param fillable: The fillable attributes
        :type fillable: list

        :return: The current Model instance
        :rtype: Model
        """
        self.__fillable__ = fillable

        return self

    def get_guarded(self):
        """
        Get the guarded attributes.
        """
        return self.__guarded__

    def guard(self, guarded):
        """
        Set the guarded attributes.

        :param guarded: The guarded attributes
        :type guarded: list

        :return: The current Model instance
        :rtype: Model
        """
        self.__guarded__ = guarded

        return self

    @classmethod
    def unguard(cls):
        """
        Disable the mass assigment restrictions.
        """
        cls.__unguarded__ = True

    @classmethod
    def reguard(cls):
        """
        Enable the mass assignment restrictions.
        :return:
        """
        cls.__unguarded__ = False

    def is_fillable(self, key):
        """
        Determine if the given attribute can be mass assigned.

        :param key: The attribute to check
        :type key: str

        :return: Whether the attribute can be mass assigned or not
        :rtype: bool
        """
        if self.__unguarded__:
            return True

        if key in self.__fillable__:
            return True

        if self.is_guarded(key):
            return False

        return not self.__fillable__ and not key.startswith("_")

    def is_guarded(self, key):
        """
        Determine if the given attribute is guarded.

        :param key: The attribute to check
        :type key: str

        :return: Whether the attribute is guarded or not
        :rtype: bool
        """
        return key in self.__guarded__ or self.__guarded__ == ["*"]

    def totally_guarded(self):
        """
        Determine if the model is totally guarded.

        :rtype: bool
        """
        return len(self.__fillable__) == 0 and self.__guarded__ == ["*"]

    def _remove_table_from_key(self, key):
        """
        Remove the table name from a given key.

        :param key: The key to remove the table name from.
        :type key: str

        :rtype: str
        """
        if "." not in key:
            return key

        return key.split(".")[-1]

    def get_incrementing(self):
        return self.__incrementing__

    def set_incrementing(self, value):
        self.__incrementing__ = value

    def to_json(self, **options):
        """
        Convert the model instance to JSON.

        :param options: The JSON options
        :type options: dict

        :return: The JSON encoded model instance
        :rtype: str
        """
        return json.dumps(self.to_dict(), **options)

    def serialize(self):
        """
        Convert the model instance to a dictionary.

        :return: The dictionary version of the model instance
        :rtype: dict
        """
        attributes = self.attributes_to_dict()

        attributes.update(self.relations_to_dict())

        return attributes

    @deprecated
    def to_dict(self):
        """
        Convert the model instance to a dictionary.

        :return: The dictionary version of the model instance
        :rtype: dict
        """
        return self.serialize()

    def attributes_to_dict(self):
        """
        Convert the model's attributes to a dictionary.

        :rtype: dict
        """
        attributes = self._get_dictable_attributes()
        mutated_attributes = self._get_mutated_attributes()

        for key in self.get_dates():
            if not key in attributes or key in mutated_attributes:
                continue

            attributes[key] = self._format_date(attributes[key])

        for key in mutated_attributes:
            if key not in attributes:
                continue

            attributes[key] = self._mutate_attribute_for_dict(key)

        # Next we will handle any casts that have been setup for this model and cast
        # the values to their appropriate type. If the attribute has a mutator we
        # will not perform the cast on those attributes to avoid any confusion.
        for key, value in self.__casts__.items():
            if key not in attributes or key in mutated_attributes:
                continue

            attributes[key] = self._cast_attribute(key, attributes[key])

        # Here we will grab all of the appended, calculated attributes to this model
        # as these attributes are not really in the attributes array, but are run
        # when we need to array or JSON the model for convenience to the coder.
        for key in self._get_dictable_appends():
            attributes[key] = self._mutate_attribute_for_dict(key)

        return attributes

    def _get_dictable_attributes(self):
        """
        Get an attribute dictionary of all dictable attributes.

        :rtype: dict
        """
        return self._get_dictable_items(self._attributes)

    def _get_dictable_appends(self):
        """
        Get all the appendable values that are dictable.

        :rtype: list
        """
        if not self.__appends__:
            return []

        return self._get_dictable_items(dict(zip(self.__appends__, self.__appends__)))

    def relations_to_dict(self):
        """
        Get the model's relationships in dictionary form.

        :rtype: dict
        """
        attributes = {}

        for key, value in self._get_dictable_relations().items():
            if key in self.get_hidden():
                continue

            relation = None
            if hasattr(value, "serialize"):
                relation = value.serialize()
            elif hasattr(value, "to_dict"):
                relation = value.to_dict()
            elif value is None:
                relation = value

            if relation is not None or value is None:
                attributes[key] = relation

        return attributes

    def _get_dictable_relations(self):
        """
        Get an attribute dict of all dictable relations.
        """
        return self._get_dictable_items(self._relations)

    def _get_dictable_items(self, values):
        """
        Get an attribute dictionary of all dictable values.

        :param values: The values to check
        :type values: dict

        :rtype: dict
        """
        if len(self.__visible__) > 0:
            return {x: values[x] for x in values.keys() if x in self.__visible__}

        return {
            x: values[x]
            for x in values.keys()
            if x not in self.__hidden__ and not x.startswith("_")
        }

    def get_attribute(self, key, original=None):
        """
        Get an attribute from the model.

        :param key: The attribute to get
        :type key: str
        """
        in_attributes = key in self._attributes

        if in_attributes:
            return self._get_attribute_value(key)

        if key in self._relations:
            return self._relations[key]

        relation = original or super(Model, self).__getattribute__(key)

        if relation:
            return self._get_relationship_from_method(key, relation)

        raise AttributeError(key)

    def get_raw_attribute(self, key):
        """
        Get the raw underlying attribute.

        :param key: The attribute to get
        :type key: str
        """
        return self._attributes[key]

    def _get_attribute_value(self, key):
        """
        Get a plain attribute.

        :param key: The attribute to get
        :type key: str
        """
        value = self._get_attribute_from_dict(key)

        if self._has_cast(key):
            value = self._cast_attribute(key, value)
        elif key in self.get_dates():
            if value is not None:
                return self.as_datetime(value)

        return value

    def _get_attribute_from_dict(self, key):
        return self._attributes.get(key)

    def _get_relationship_from_method(self, method, relations=None):
        """
        Get a relationship value from a method.

        :param method: The method name
        :type method: str

        :rtype: mixed
        """
        relations = relations or super(Model, self).__getattribute__(method)

        if not isinstance(relations, Relation):
            raise RuntimeError(
                "Relationship method must return an object of type Relation"
            )

        self._relations[method] = relations

        return self._relations[method]

    def has_get_mutator(self, key):
        """
        Determine if a get mutator exists for an attribute.

        :param key: The attribute name
        :type key: str

        :rtype: bool
        """
        return hasattr(self, "get_%s_attribute" % inflection.underscore(key))

    def _mutate_attribute_for_dict(self, key):
        """
        Get the value of an attribute using its mutator for dict conversion.

        :param key: The attribute name
        :type key: str
        """
        value = getattr(self, key)

        if hasattr(value, "to_dict"):
            return value.to_dict()

        if key in self.get_dates():
            return self._format_date(value)

        return value

    def _has_cast(self, key):
        """
        Determine whether an attribute should be casted to a native type.

        :param key: The attribute to check
        :type key: str

        :rtype: bool
        """
        return key in self.__casts__

    def _has_set_mutator(self, key):
        """
        Determine whether an attribute has a set mutator.

        :param key: The attribute
        :type key: str

        :rtype: bool
        """
        klass = self.__class__
        if key not in self._mutator_cache[klass]:
            return False

        return self._mutator_cache[klass][key].mutator is not None

    def _is_json_castable(self, key):
        """
        Determine whether a value is JSON castable.

        :param key: The key to check
        :type key: str

        :rtype: bool
        """
        if self._has_cast(key):
            type = self._get_cast_type(key)

            return type in ["list", "dict", "json", "object"]

        return False

    def _get_cast_type(self, key):
        """
        Get the type of the cast for a model attribute.

        :param key: The attribute to get the cast for
        :type key: str

        :rtype: str
        """
        return self.__casts__[key].lower().strip()

    def _cast_attribute(self, key, value):
        """
        Cast an attribute to a native Python type

        :param key: The attribute key
        :type key: str

        :param value: The attribute value
        :type value: The attribute value

        :rtype: mixed
        """
        if value is None:
            return None

        type = self._get_cast_type(key)
        if type in ["int", "integer"]:
            return int(value)
        elif type in ["real", "float", "double"]:
            return float(value)
        elif type in ["string", "str"]:
            return str(value)
        elif type in ["bool", "boolean"]:
            return bool(value)
        elif type in ["dict", "list", "json"] and isinstance(value, basestring):
            return json.loads(value)
        else:
            return value

    def get_dates(self):
        """
        Get the attributes that should be converted to dates.

        :rtype: list
        """
        defaults = [self.CREATED_AT, self.UPDATED_AT]

        return self.__dates__ + defaults

    def from_datetime(self, value):
        """
        Convert datetime to a storable string.
        
        :param value: The datetime value
        :type value: pendulum.Pendulum or datetime.date or datetime.datetime

        :rtype: str
        """
        date_format = self.get_connection().get_query_grammar().get_date_format()

        if isinstance(value, pendulum.Pendulum):
            return value.format(date_format)

        if isinstance(value, datetime.date) and not isinstance(
            value, (datetime.datetime)
        ):
            value = pendulum.date.instance(value)

            return value.format(date_format)

        return pendulum.instance(value).format(date_format)

    def as_datetime(self, value):
        """
        Return a timestamp as a datetime.

        :rtype: pendulum.Pendulum or pendulum.Date
        """
        if isinstance(value, basestring):
            return pendulum.parse(value)

        if isinstance(value, (int, float)):
            return pendulum.from_timestamp(value)

        if isinstance(value, datetime.date) and not isinstance(
            value, (datetime.datetime)
        ):
            return pendulum.date.instance(value)

        return pendulum.instance(value)

    def get_date_format(self):
        """
        Get the format to use for timestamps and dates.

        :rtype: str
        """
        return "iso"

    def _format_date(self, date):
        """
        Format a date or timestamp.

        :param date: The date or timestamp
        :type date: datetime.datetime or datetime.date or pendulum.Pendulum

        :rtype: str
        """
        if date is None:
            return date

        format = self.get_date_format()

        if format == "iso":
            if isinstance(date, basestring):
                return pendulum.parse(date).isoformat()

            return date.isoformat()
        else:
            if isinstance(date, basestring):
                return pendulum.parse(date).format(format)

            return date.strftime(format)

    def set_attribute(self, key, value):
        """
        Set a given attribute on the model.
        """
        if self._has_set_mutator(key):
            return super(Model, self).__setattr__(key, value)

        if key in self.get_dates() and value:
            value = self.from_datetime(value)

        if self._is_json_castable(key):
            value = json.dumps(value)

        self._attributes[key] = value

    def replicate(self, except_=None):
        """
        Clone the model into a new, non-existing instance.

        :param except_: The attributes that should not be cloned
        :type except_: list

        :rtype: Model
        """
        if except_ is None:
            except_ = [
                self.get_key_name(),
                self.get_created_at_column(),
                self.get_updated_at_column(),
            ]

            attributes = {
                x: self._attributes[x] for x in self._attributes if x not in except_
            }

            instance = self.new_instance(attributes)

            instance.set_relations(dict(**self._relations))

            return instance

    def get_attributes(self):
        """
        Get all of the current attributes on the model.

        :rtype: dict
        """
        return self._attributes

    def set_raw_attributes(self, attributes, sync=False):
        """
        Set the dictionary of model attributes. No checking is done.

        :param attributes: The model attributes
        :type attributes: dict

        :param sync: Whether to sync the attributes or not
        :type sync: bool
        """
        self._attributes = dict(attributes.items())

        if sync:
            self.sync_original()

    def set_raw_attribute(self, key, value, sync=False):
        """
        Set an attribute. No checking is done.

        :param key: The attribute name
        :type key: str

        :param value: The attribute value
        :type value: mixed

        :param sync: Whether to sync the attributes or not
        :type sync: bool
        """
        self._attributes[key] = value

        if sync:
            self.sync_original()

    def get_original(self, key=None, default=None):
        """
        Get the original values

        :param key: The original key to get
        :type key: str

        :param default: The default value if the key does not exist
        :type default: mixed

        :rtype: mixed
        """
        if key is None:
            return self._original

        return self._original.get(key, default)

    def sync_original(self):
        """
        Sync the original attributes with the current.

        :rtype: Builder
        """
        self._original = dict(self._attributes.items())

        return self

    def sync_original_attribute(self, attribute):
        """
        Sync a single original attribute with its current value.

        :param attribute: The attribute to sync
        :type attribute: str

        :rtype: Model
        """
        self._original[attribute] = self._attributes[attribute]

        return self

    def is_dirty(self, *attributes):
        """
        Determine if the model or given attributes have been modified.

        :param attributes: The attributes to check
        :type attributes: list

        :rtype: boolean
        """
        dirty = self.get_dirty()

        if not attributes:
            return len(dirty) > 0

        for attribute in attributes:
            if attribute in dirty:
                return True

        return False

    def get_dirty(self):
        """
        Get the attribute that have been change since last sync.

        :rtype: list
        """
        dirty = {}

        for key, value in self._attributes.items():
            if key not in self._original:
                dirty[key] = value
            elif value != self._original[key]:
                dirty[key] = value

        return dirty

    @property
    def exists(self):
        return self._exists

    def set_exists(self, exists):
        self._exists = exists

    def set_appends(self, appends):
        """
        Sets the appendable attributes.

        :param appends: The appendable attributes
        :type appends: list
        """
        self.__appends__ = appends

        return self

    def get_relations(self):
        """
        Get all the loaded relations for the instance.

        :rtype: dict
        """
        return self._relations

    def get_relation(self, relation):
        """
        Get a specific relation.

        :param relation: The name of the relation.
        :type relation: str

        :rtype: mixed
        """
        return self._relations[relation]

    def set_relation(self, relation, value):
        """
        Set the specific relation in the model.

        :param relation: The name of the relation
        :type relation: str

        :param value: The relation
        :type value: mixed

        :return: The current Model instance
        :rtype: Model
        """
        self._relations[relation] = value

        return self

    def set_relations(self, relations):
        self._relations = relations

        return self

    def get_connection(self):
        """
        Get the database connection for the model

        :rtype: orator.connections.Connection
        """
        return self.resolve_connection(self.__connection__)

    def get_connection_name(self):
        """
        Get the database connection name for the model.

        :rtype: str
        """
        return self.__connection__

    def set_connection(self, name):
        """
        Set the connection associated with the model.

        :param name: The connection name
        :type name: str

        :return: The current model instance
        :rtype: Model
        """
        self.__connection__ = name

        return self

    @classmethod
    def resolve_connection(cls, connection=None):
        """
        Resolve a connection instance.

        :param connection: The connection name
        :type connection: str

        :rtype: orator.connections.Connection
        """
        return cls.__resolver.connection(connection)

    @classmethod
    def get_connection_resolver(cls):
        """
        Get the connection resolver instance.
        """
        return cls.__resolver

    @classmethod
    def set_connection_resolver(cls, resolver):
        """
        Set the connection resolver instance.
        """
        cls.__resolver = resolver

    @classmethod
    def unset_connection_resolver(cls):
        """
        Unset the connection resolver instance.
        """
        cls._resolver = None

    def _get_mutated_attributes(self):
        """
        Get the mutated attributes.

        :return: list
        """
        klass = self.__class__

        if klass in self._accessor_cache:
            return self._accessor_cache[klass]

        return []

    def __getattr__(self, item):
        return self.get_attribute(item)

    def __setattr__(self, key, value):
        if key in [
            "_attributes",
            "_exists",
            "_relations",
            "_original",
        ] or key.startswith("__"):
            return object.__setattr__(self, key, value)

        if self._has_set_mutator(key):
            return self.set_attribute(key, value)

        try:
            if object.__getattribute__(self, key):
                return object.__setattr__(self, key, value)
        except AttributeError:
            pass

        if callable(getattr(self, key, None)):
            return super(Model, self).__setattr__(key, value)
        else:
            self.set_attribute(key, value)

    def __delattr__(self, item):
        try:
            super(Model, self).__delattr__(item)
        except AttributeError:
            del self._attributes[item]

    def __getstate__(self):
        return {
            "attributes": self._attributes,
            "relations": self._relations,
            "exists": self._exists,
        }

    def __setstate__(self, state):
        self._boot_if_not_booted()

        self.set_raw_attributes(state["attributes"], True)
        self.set_relations(state["relations"])
        self.set_exists(state["exists"])
