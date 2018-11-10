# -*- coding: utf-8 -*-

import copy
from collections import OrderedDict
from ..exceptions.orm import ModelNotFound
from ..utils import Null, basestring
from ..query.expression import QueryExpression
from ..pagination import Paginator, LengthAwarePaginator
from ..support import Collection
from .scopes import Scope


class Builder(object):

    _passthru = [
        "to_sql",
        "lists",
        "insert",
        "insert_get_id",
        "pluck",
        "count",
        "min",
        "max",
        "avg",
        "sum",
        "exists",
        "get_bindings",
        "raw",
    ]

    def __init__(self, query):
        """
        Constructor

        :param query: The underlying query builder
        :type query: QueryBuilder
        """
        self._query = query

        self._model = None
        self._eager_load = {}
        self._macros = {}
        self._scopes = OrderedDict()

        self._on_delete = None

    def with_global_scope(self, identifier, scope):
        """
        Register a new global scope.

        :param identifier: The scope's identifier
        :type identifier: str

        :param scope: The scope to register
        :type scope: Scope or callable

        :rtype: Builder
        """
        self._scopes[identifier] = scope

        return self

    def without_global_scope(self, scope):
        """
        Remove a registered global scope.

        :param scope: The scope to remove
        :type scope: Scope or str

        :rtype: Builder
        """
        if isinstance(scope, basestring):
            del self._scopes[scope]

            return self

        keys = []
        for key, value in self._scopes.items():
            if scope == value.__class__ or isinstance(scope, value.__class__):
                keys.append(key)

        for key in keys:
            del self._scopes[key]

        return self

    def without_global_scopes(self):
        """
        Remove all registered global scopes.

        :rtype: Builder
        """
        self._scopes = OrderedDict()

        return self

    def find(self, id, columns=None):
        """
        Find a model by its primary key

        :param id: The primary key value
        :type id: mixed

        :param columns: The columns to retrieve
        :type columns: list

        :return: The found model
        :rtype: orator.Model
        """
        if columns is None:
            columns = ["*"]

        if isinstance(id, list):
            return self.find_many(id, columns)

        self._query.where(self._model.get_qualified_key_name(), "=", id)

        return self.first(columns)

    def find_many(self, id, columns=None):
        """
        Find a model by its primary key

        :param id: The primary key values
        :type id: list

        :param columns: The columns to retrieve
        :type columns: list

        :return: The found model
        :rtype: orator.Collection
        """
        if columns is None:
            columns = ["*"]

        if not id:
            return self._model.new_collection()

        self._query.where_in(self._model.get_qualified_key_name(), id)

        return self.get(columns)

    def find_or_fail(self, id, columns=None):
        """
        Find a model by its primary key or raise an exception

        :param id: The primary key value
        :type id: mixed

        :param columns: The columns to retrieve
        :type columns: list

        :return: The found model
        :rtype: orator.Model

        :raises: ModelNotFound
        """
        result = self.find(id, columns)

        if isinstance(id, list):
            if len(result) == len(set(id)):
                return result
        elif result:
            return result

        raise ModelNotFound(self._model.__class__)

    def first(self, columns=None):
        """
        Execute the query and get the first result

        :param columns: The columns to get
        :type columns: list

        :return: The result
        :rtype: mixed
        """
        if columns is None:
            columns = ["*"]

        return self.take(1).get(columns).first()

    def first_or_fail(self, columns=None):
        """
        Execute the query and get the first result or raise an exception

        :param columns: The columns to get
        :type columns: list

        :return: The result
        :rtype: mixed
        """
        model = self.first(columns)

        if model is not None:
            return model

        raise ModelNotFound(self._model.__class__)

    def get(self, columns=None):
        """
        Execute the query as a "select" statement.

        :param columns: The columns to get
        :type columns: list

        :rtype: orator.Collection
        """
        models = self.get_models(columns)

        # If we actually found models we will also eager load any relationships that
        # have been specified as needing to be eager loaded, which will solve the
        # n+1 query issue for the developers to avoid running a lot of queries.
        if len(models) > 0:
            models = self.eager_load_relations(models)

        collection = self._model.new_collection(models)

        return collection

    def pluck(self, column):
        """
        Pluck a single column from the database.

        :param column: THe column to pluck
        :type column: str

        :return: The column value
        :rtype: mixed
        """
        result = self.first([column])

        if result:
            return result[column]

    def chunk(self, count):
        """
        Chunk the results of the query

        :param count: The chunk size
        :type count: int

        :return: The current chunk
        :rtype: list
        """
        connection = self._model.get_connection_name()
        for results in self.apply_scopes().get_query().chunk(count):
            models = self._model.hydrate(results, connection)

            # If we actually found models we will also eager load any relationships that
            # have been specified as needing to be eager loaded, which will solve the
            # n+1 query issue for the developers to avoid running a lot of queries.
            if len(models) > 0:
                models = self.eager_load_relations(models)

            collection = self._model.new_collection(models)

            yield collection

    def lists(self, column, key=None):
        """
        Get a list with the values of a given column

        :param column: The column to get the values for
        :type column: str

        :param key: The key
        :type key: str

        :return: The list of values
        :rtype: list or dict
        """
        results = self.to_base().lists(column, key)

        if not self._model.has_get_mutator(column):
            return results

        if isinstance(results, dict):
            for key, value in results.items():
                fill = {column: value}

                results[key] = self._model.new_from_builder(fill).column
        else:
            for i, value in enumerate(results):
                fill = {column: value}

                results[i] = self._model.new_from_builder(fill).column

    def paginate(self, per_page=None, current_page=None, columns=None):
        """
        Paginate the given query.

        :param per_page: The number of records per page
        :type per_page: int

        :param current_page: The current page of results
        :type current_page: int

        :param columns: The columns to return
        :type columns: list

        :return: The paginator
        """
        if columns is None:
            columns = ["*"]

        total = self.to_base().get_count_for_pagination()

        page = current_page or Paginator.resolve_current_page()
        per_page = per_page or self._model.get_per_page()
        self._query.for_page(page, per_page)

        return LengthAwarePaginator(self.get(columns).all(), total, per_page, page)

    def simple_paginate(self, per_page=None, current_page=None, columns=None):
        """
        Paginate the given query.

        :param per_page: The number of records per page
        :type per_page: int

        :param current_page: The current page of results
        :type current_page: int

        :param columns: The columns to return
        :type columns: list

        :return: The paginator
        """
        if columns is None:
            columns = ["*"]

        page = current_page or Paginator.resolve_current_page()
        per_page = per_page or self._model.get_per_page()

        self.skip((page - 1) * per_page).take(per_page + 1)

        return Paginator(self.get(columns).all(), per_page, page)

    def update(self, _values=None, **values):
        """
        Update a record in the database

        :param values: The values of the update
        :type values: dict

        :return: The number of records affected
        :rtype: int
        """
        if _values is not None:
            values.update(_values)

        return self._query.update(self._add_updated_at_column(values))

    def increment(self, column, amount=1, extras=None):
        """
        Increment a column's value by a given amount

        :param column: The column to increment
        :type column: str

        :param amount: The amount by which to increment
        :type amount: int

        :param extras: Extra columns
        :type extras: dict

        :return: The number of rows affected
        :rtype: int
        """
        if extras is None:
            extras = {}

        extras = self._add_updated_at_column(extras)

        return self.to_base().increment(column, amount, extras)

    def decrement(self, column, amount=1, extras=None):
        """
        Decrement a column's value by a given amount

        :param column: The column to increment
        :type column: str

        :param amount: The amount by which to increment
        :type amount: int

        :param extras: Extra columns
        :type extras: dict

        :return: The number of rows affected
        :rtype: int
        """
        if extras is None:
            extras = {}

        extras = self._add_updated_at_column(extras)

        return self.to_base().decrement(column, amount, extras)

    def _add_updated_at_column(self, values):
        """
        Add the "updated_at" column to a dictionary of values.

        :param values: The values to update
        :type values: dict

        :return: The new dictionary of values
        :rtype: dict
        """
        if not self._model.uses_timestamps():
            return values

        column = self._model.get_updated_at_column()

        if "updated_at" not in values:
            values.update({column: self._model.fresh_timestamp_string()})

        return values

    def delete(self):
        """
        Delete a record from the database.
        """
        if self._on_delete is not None:
            return self._on_delete(self)

        return self._query.delete()

    def force_delete(self):
        """
        Run the default delete function on the builder.
        """
        return self._query.delete()

    def on_delete(self, callback):
        """
        Register a replacement for the default delete function.

        :param callback: A replacement for the default delete function
        :type callback: callable
        """
        self._on_delete = callback

    def get_models(self, columns=None):
        """
        Get the hydrated models without eager loading.

        :param columns: The columns to get
        :type columns: list

        :return: A list of models
        :rtype: orator.orm.collection.Collection
        """
        results = self.apply_scopes().get_query().get(columns).all()

        connection = self._model.get_connection_name()

        models = self._model.hydrate(results, connection)

        return models

    def eager_load_relations(self, models):
        """
        Eager load the relationship of the models.

        :param models:
        :type models: list

        :return: The models
        :rtype: list
        """
        for name, constraints in self._eager_load.items():
            if name.find(".") == -1:
                models = self._load_relation(models, name, constraints)

        return models

    def _load_relation(self, models, name, constraints):
        """
        Eagerly load the relationship on a set of models.

        :rtype: list
        """
        relation = self.get_relation(name)

        relation.add_eager_constraints(models)

        if callable(constraints):
            constraints(relation.get_query())
        else:
            relation.merge_query(constraints)

        models = relation.init_relation(models, name)

        results = relation.get_eager()

        return relation.match(models, results, name)

    def get_relation(self, relation):
        """
        Get the relation instance for the given relation name.

        :rtype: orator.orm.relations.Relation
        """
        from .relations import Relation

        with Relation.no_constraints(True):
            rel = getattr(self.get_model(), relation)()

        nested = self._nested_relations(relation)

        if len(nested) > 0:
            rel.get_query().with_(nested)

        return rel

    def _nested_relations(self, relation):
        """
        Get the deeply nested relations for a given top-level relation.

        :rtype: dict
        """
        nested = {}

        for name, constraints in self._eager_load.items():
            if self._is_nested(name, relation):
                nested[name[len(relation + ".") :]] = constraints

        return nested

    def _is_nested(self, name, relation):
        """
        Determine if the relationship is nested.

        :type name: str
        :type relation: str

        :rtype: bool
        """
        dots = name.find(".")

        return dots and name.startswith(relation + ".")

    def where(self, column, operator=Null(), value=None, boolean="and"):
        """
        Add a where clause to the query

        :param column: The column of the where clause, can also be a QueryBuilder instance for sub where
        :type column: str|Builder

        :param operator: The operator of the where clause
        :type operator: str

        :param value: The value of the where clause
        :type value: mixed

        :param boolean: The boolean of the where clause
        :type boolean: str

        :return: The current Builder instance
        :rtype: Builder
        """
        if isinstance(column, Builder):
            self._query.add_nested_where_query(column.get_query(), boolean)
        else:
            self._query.where(column, operator, value, boolean)

        return self

    def or_where(self, column, operator=None, value=None):
        """
        Add an "or where" clause to the query.

        :param column: The column of the where clause, can also be a QueryBuilder instance for sub where
        :type column: str or Builder

        :param operator: The operator of the where clause
        :type operator: str

        :param value: The value of the where clause
        :type value: mixed

        :return: The current Builder instance
        :rtype: Builder
        """
        return self.where(column, operator, value, "or")

    def where_exists(self, query, boolean="and", negate=False):
        """
        Add an exists clause to the query.

        :param query: The exists query
        :type query: Builder or QueryBuilder

        :type boolean: str

        :type negate: bool

        :rtype: Builder
        """
        if isinstance(query, Builder):
            query = query.get_query()

        self.get_query().where_exists(query, boolean, negate)

        return self

    def or_where_exists(self, query, negate=False):
        """
        Add an or exists clause to the query.

        :param query: The exists query
        :type query: Builder or QueryBuilder

        :type negate: bool

        :rtype: Builder
        """
        return self.where_exists(query, "or", negate)

    def where_not_exists(self, query, boolean="and"):
        """
        Add a where not exists clause to the query.

        :param query: The exists query
        :type query: Builder or QueryBuilder

        :type boolean: str

        :rtype: Builder
        """
        return self.where_exists(query, boolean, True)

    def or_where_not_exists(self, query):
        """
        Add a or where not exists clause to the query.

        :param query: The exists query
        :type query: Builder or QueryBuilder

        :rtype: Builder
        """
        return self.or_where_exists(query, True)

    def has(self, relation, operator=">=", count=1, boolean="and", extra=None):
        """
        Add a relationship count condition to the query.

        :param relation: The relation to count
        :type relation: str

        :param operator: The operator
        :type operator: str

        :param count: The count
        :type count: int

        :param boolean: The boolean value
        :type boolean: str

        :param extra: The extra query
        :type extra: Builder or callable

        :type: Builder
        """
        if relation.find(".") >= 0:
            return self._has_nested(relation, operator, count, boolean, extra)

        relation = self._get_has_relation_query(relation)

        query = relation.get_relation_count_query(
            relation.get_related().new_query(), self
        )

        # TODO: extra query
        if extra:
            if callable(extra):
                extra(query)

        return self._add_has_where(
            query.apply_scopes(), relation, operator, count, boolean
        )

    def _has_nested(self, relations, operator=">=", count=1, boolean="and", extra=None):
        """
        Add nested relationship count conditions to the query.

        :param relations: nested relations
        :type relations: str

        :param operator: The operator
        :type operator: str

        :param count: The count
        :type count: int

        :param boolean: The boolean value
        :type boolean: str

        :param extra: The extra query
        :type extra: Builder or callable

        :rtype: Builder
        """
        relations = relations.split(".")

        def closure(q):
            if len(relations) > 1:
                q.where_has(relations.pop(0), closure)
            else:
                q.has(relations.pop(0), operator, count, boolean, extra)

        return self.where_has(relations.pop(0), closure)

    def doesnt_have(self, relation, boolean="and", extra=None):
        """
        Add a relationship count to the query.

        :param relation: The relation to count
        :type relation: str

        :param boolean: The boolean value
        :type boolean: str

        :param extra: The extra query
        :type extra: Builder or callable

        :rtype: Builder
        """
        return self.has(relation, "<", 1, boolean, extra)

    def where_has(self, relation, extra, operator=">=", count=1):
        """
        Add a relationship count condition to the query with where clauses.

        :param relation: The relation to count
        :type relation: str

        :param extra: The extra query
        :type extra: Builder or callable

        :param operator: The operator
        :type operator: str

        :param count: The count
        :type count: int

        :rtype: Builder
        """
        return self.has(relation, operator, count, "and", extra)

    def where_doesnt_have(self, relation, extra=None):
        """
        Add a relationship count condition to the query with where clauses.

        :param relation: The relation to count
        :type relation: str

        :param extra: The extra query
        :type extra: Builder or callable

        :rtype: Builder
        """
        return self.doesnt_have(relation, "and", extra)

    def or_has(self, relation, operator=">=", count=1):
        """
        Add a relationship count condition to the query with an "or".

        :param relation: The relation to count
        :type relation: str

        :param operator: The operator
        :type operator: str

        :param count: The count
        :type count: int

        :rtype: Builder
        """
        return self.has(relation, operator, count, "or")

    def or_where_has(self, relation, extra, operator=">=", count=1):
        """
        Add a relationship count condition to the query with where clauses and an "or".

        :param relation: The relation to count
        :type relation: str

        :param extra: The extra query
        :type extra: Builder or callable

        :param operator: The operator
        :type operator: str

        :param count: The count
        :type count: int

        :rtype: Builder
        """
        return self.has(relation, operator, count, "or", extra)

    def _add_has_where(self, has_query, relation, operator, count, boolean):
        """
        Add the "has" condition where clause to the query.

        :param has_query: The has query
        :type has_query: Builder

        :param relation: The relation to count
        :type relation: orator.orm.relations.Relation

        :param operator: The operator
        :type operator: str

        :param count: The count
        :type count: int

        :param boolean: The boolean value
        :type boolean: str

        :rtype: Builder
        """
        self._merge_model_defined_relation_wheres_to_has_query(has_query, relation)

        if isinstance(count, basestring) and count.isdigit():
            count = QueryExpression(count)

        return self.where(
            QueryExpression("(%s)" % has_query.to_sql()), operator, count, boolean
        )

    def _merge_model_defined_relation_wheres_to_has_query(self, has_query, relation):
        """
        Merge the "wheres" from a relation query to a has query.

        :param has_query: The has query
        :type has_query: Builder

        :param relation: The relation to count
        :type relation: orator.orm.relations.Relation
        """
        relation_query = relation.get_base_query()

        has_query.merge_wheres(relation_query.wheres, relation_query.get_bindings())

        self._query.add_binding(has_query.get_query().get_bindings(), "where")

    def _get_has_relation_query(self, relation):
        """
        Get the "has" relation base query

        :type relation: str

        :rtype: Builder
        """
        from .relations import Relation

        with Relation.no_constraints(True):
            return getattr(self.get_model(), relation)()

    def with_(self, *relations):
        """
        Set the relationships that should be eager loaded.

        :return: The current Builder instance
        :rtype: Builder
        """
        if not relations:
            return self

        eagers = self._parse_with_relations(list(relations))

        self._eager_load.update(eagers)

        return self

    def _parse_with_relations(self, relations):
        """
        Parse a list of relations into individuals.

        :param relations: The relation to parse
        :type relations: list

        :rtype: dict
        """
        results = {}

        for relation in relations:
            if isinstance(relation, dict):
                for name, constraints in relation.items():
                    results = self._parse_nested_with(name, results)

                    results[name] = constraints

                continue
            else:
                name = relation
                constraints = self.__class__(self.get_query().new_query())

            results = self._parse_nested_with(name, results)

            results[name] = constraints

        return results

    def _parse_nested_with(self, name, results):
        """
        Parse the nested relationship in a relation.

        :param name: The name of the relationship
        :type name: str

        :type results: dict

        :rtype: dict
        """
        progress = []

        for segment in name.split("."):
            progress.append(segment)

            last = ".".join(progress)
            if last not in results:
                results[last] = self.__class__(self.get_query().new_query())

        return results

    def _call_scope(self, scope, *args, **kwargs):
        """
        Call the given model scope.

        :param scope: The scope to call
        :type scope: str
        """
        query = self.get_query()

        # We will keep track of how many wheres are on the query before running the
        # scope so that we can properly group the added scope constraints in the
        # query as their own isolated nested where statement and avoid issues.
        original_where_count = len(query.wheres)

        result = getattr(self._model, scope)(self, *args, **kwargs)

        if self._should_nest_wheres_for_scope(query, original_where_count):
            self._nest_wheres_for_scope(
                query, [0, original_where_count, len(query.wheres)]
            )

        return result or self

    def apply_scopes(self):
        """
        Get the underlying query builder instance with applied global scopes.

        :type: Builder
        """
        if not self._scopes:
            return self

        builder = copy.copy(self)

        query = builder.get_query()

        # We will keep track of how many wheres are on the query before running the
        # scope so that we can properly group the added scope constraints in the
        # query as their own isolated nested where statement and avoid issues.
        original_where_count = len(query.wheres)

        where_counts = [0, original_where_count]

        for scope in self._scopes.values():
            self._apply_scope(scope, builder)

            # Again, we will keep track of the count each time we add where clauses so that
            # we will properly isolate each set of scope constraints inside of their own
            # nested where clause to avoid any conflicts or issues with logical order.
            where_counts.append(len(query.wheres))

        if self._should_nest_wheres_for_scope(query, original_where_count):
            self._nest_wheres_for_scope(query, Collection(where_counts).unique().all())

        return builder

    def _apply_scope(self, scope, builder):
        """
        Apply a single scope on the given builder instance.

        :param scope: The scope to apply
        :type scope: callable or Scope

        :param builder: The builder to apply the scope to
        :type builder: Builder
        """
        if callable(scope):
            scope(builder)
        elif isinstance(scope, Scope):
            scope.apply(builder, self.get_model())

    def _should_nest_wheres_for_scope(self, query, original_where_count):
        """
        Determine if the scope added after the given offset should be nested.

        :type query: QueryBuilder
        :type original_where_count: int

        :rtype: bool
        """
        return original_where_count and len(query.wheres) > original_where_count

    def _nest_wheres_for_scope(self, query, where_counts):
        """
        Nest where conditions of the builder and each global scope.

        :type query: QueryBuilder
        :type where_counts: list
        """
        # Here, we totally remove all of the where clauses since we are going to
        # rebuild them as nested queries by slicing the groups of wheres into
        # their own sections. This is to prevent any confusing logic order.
        wheres = query.wheres

        query.wheres = []

        # We will take the first offset (typically 0) of where clauses and start
        # slicing out every scope's where clauses into their own nested where
        # groups for improved isolation of every scope's added constraints.
        previous_count = where_counts.pop(0)

        for where_count in where_counts:
            query.wheres.append(
                self._slice_where_conditions(
                    wheres, previous_count, where_count - previous_count
                )
            )

            previous_count = where_count

    def _slice_where_conditions(self, wheres, offset, length):
        """
        Create a where list with sliced where conditions.

        :type wheres: list
        :type offset: int
        :type length: int

        :rtype: list
        """
        where_group = self.get_query().for_nested_where()
        where_group.wheres = wheres[offset : (offset + length)]

        return {"type": "nested", "query": where_group, "boolean": "and"}

    def get_query(self):
        """
        Get the underlying query instance.

        :rtype: QueryBuilder
        """
        return self._query

    def to_base(self):
        """
        Get a base query builder instance.

        :rtype: QueryBuilder
        """
        return self.apply_scopes().get_query()

    def set_query(self, query):
        """
        Set the underlying query instance.

        :param query: A QueryBuilder instance
        :type query: QueryBuilder
        """
        self._query = query

    def get_eager_loads(self):
        """
        Get the relationships being eager loaded.

        :rtype: dict
        """
        return self._eager_load

    def set_eager_loads(self, eager_load):
        """
        Sets the relationships to eager load.

        :type eager_load: dict

        :rtype: Builder
        """
        self._eager_load = eager_load

        return self

    def get_model(self):
        """
        Get the model instance of the model being queried

        :rtype: orator.Model
        """
        return self._model

    def set_model(self, model):
        """
        Set a model instance for the model being queried.

        :param model: The model instance
        :type model: orator.orm.Model

        :return: The current Builder instance
        :rtype: Builder
        """
        self._model = model

        self._query.from_(model.get_table())

        return self

    def macro(self, name, callback):
        """
        Extend the builder with the given callback.

        :param name: The extension name
        :type name: str

        :param callback: The callback
        :type callback: callable
        """
        self._macros[name] = callback

    def get_macro(self, name):
        """
        Get the given macro by name

        :param name: The macro name
        :type name: str
        :return:
        """
        return self._macros.get(name)

    def __dynamic(self, method):
        from .utils import scope

        scope_method = "scope_%s" % method
        is_scope = False
        is_macro = False

        # New scope definition check
        if hasattr(self._model, method) and isinstance(
            getattr(self._model, method), scope
        ):
            is_scope = True
            attribute = getattr(self._model, method)
            scope_method = method
        # Old scope definition check
        elif hasattr(self._model, scope_method):
            is_scope = True
            attribute = getattr(self._model, scope_method)
        elif method in self._macros:
            is_macro = True
            attribute = self._macros[method]
        else:
            if method in self._passthru:
                attribute = getattr(self.apply_scopes().get_query(), method)
            else:
                attribute = getattr(self._query, method)

        def call(*args, **kwargs):
            if is_scope:
                return self._call_scope(scope_method, *args, **kwargs)
            if is_macro:
                return attribute(self, *args, **kwargs)

            result = attribute(*args, **kwargs)

            if method in self._passthru:
                return result
            else:
                return self

        if not callable(attribute):
            return attribute

        return call

    def __getattr__(self, item, *args):
        return self.__dynamic(item)

    def __copy__(self):
        new = self.__class__(copy.copy(self._query))
        new.set_model(self._model)

        return new
