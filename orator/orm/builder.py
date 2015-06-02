# -*- coding: utf-8 -*-

from ..exceptions.orm import ModelNotFound
from ..utils import Null, basestring
from ..query.expression import QueryExpression
from ..pagination import Paginator, LengthAwarePaginator


class Builder(object):

    _passthru = [
        'to_sql', 'lists', 'insert', 'insert_get_id', 'pluck', 'count',
        'min', 'max', 'avg', 'sum', 'exists', 'get_bindings', 'raw'
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

        self._on_delete = None

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
            columns = ['*']

        if isinstance(id, list):
            return self.find_many(id, columns)

        self._query.where(self._model.get_qualified_key_name(), '=', id)

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
            columns = ['*']

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
            columns = ['*']

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

        return self._model.new_collection(models)

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
        page = 1
        results = self.for_page(page, count).get()

        while results:
            yield results

            page += 1

            results = self.for_page(page, count).get()

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
        results = self._query.lists(column, key)

        if self._model.has_get_mutator(column):
            if isinstance(results, dict):
                for key, value in results.items():
                    fill = {column: value}

                    results[key] = self._model.new_from_builder(fill).column
            else:
                for i, value in enumerate(results):
                    fill = {column: value}

                    results[i] = self._model.new_from_builder(fill).column

        return results

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
            columns = ['*']

        total = self._query.get_count_for_pagination()

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
            columns = ['*']

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
        extras = self._add_updated_at_column(extras)

        return self._query.increment(column, amount, extras)

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
        extras = self._add_updated_at_column(extras)

        return self._query.decrement(column, amount, extras)

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

        values.update({column: self._model.fresh_timestamp()})

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
        :rtype: list
        """
        results = self._query.get(columns)

        connection = self._model.get_connection_name()

        return self._model.hydrate(results, connection).all()

    def eager_load_relations(self, models):
        """
        Eager load the relationship of the models.

        :param models:
        :type models: list

        :return: The models
        :rtype: list
        """
        for name, constraints in self._eager_load.items():
            if name.find('.') == -1:
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
            query = getattr(self.get_model(), relation)()

        nested = self._nested_relations(relation)

        if len(nested) > 0:
            query.get_query().with_(nested)

        return query

    def _nested_relations(self, relation):
        """
        Get the deeply nested relations for a given top-level relation.

        :rtype: dict
        """
        nested = {}

        for name, constraints in self._eager_load.items():
            if self._is_nested(name, relation):
                nested[name[len(relation + '.'):]] = constraints

        return nested

    def _is_nested(self, name, relation):
        """
        Determine if the relationship is nested.

        :type name: str
        :type relation: str

        :rtype: bool
        """
        dots = name.find('.')

        return dots and name.startswith(relation + '.')

    def where(self, column, operator=Null(), value=None, boolean='and'):
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
        return self.where(column, operator, value, 'or')

    def has(self, relation, operator='>=', count=1, boolean='and', extra=None):
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
        if relation.find('.') >= 0:
            return self._has_nested(relation, operator, count, boolean, extra)

        relation = self._get_has_relation_query(relation)

        query = relation.get_relation_count_query(relation.get_related().new_query(), self)

        # TODO: extra query
        if extra:
            if callable(extra):
                extra(query)

        return self._add_has_where(query, relation, operator, count, boolean)

    def _has_nested(self, relations, operator='>=', count=1, boolean='and', extra=None):
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
        relations = relations.split('.')

        def closure(q):
            if len(relations) > 1:
                q.where_has(relations.pop(0), closure)
            else:
                q.has(relations.pop(0), operator, count, boolean, extra)

        return self.where_has(relations.pop(0), closure)

    def doesnt_have(self, relation, boolean='and', extra=None):
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
        return self.has(relation, '<', 1, boolean, extra)

    def where_has(self, relation, extra, operator='>=', count=1):
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
        return self.has(relation, operator, count, 'and', extra)

    def where_doesnt_have(self, relation, extra=None):
        """
        Add a relationship count condition to the query with where clauses.

        :param relation: The relation to count
        :type relation: str

        :param extra: The extra query
        :type extra: Builder or callable

        :rtype: Builder
        """
        return self.doesnt_have(relation, 'and', extra)

    def or_has(self, relation, operator='>=', count=1):
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
        return self.has(relation, operator, count, 'or')

    def or_where_has(self, relation, extra, operator='>=', count=1):
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
        return self.has(relation, operator, count, 'or', extra)

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
        self._merge_wheres_to_has(has_query, relation)

        if isinstance(count, basestring) and count.isdigit():
            count = QueryExpression(count)

        return self.where(QueryExpression('(%s)' % has_query.to_sql()), operator, count, boolean)

    def _merge_wheres_to_has(self, has_query, relation):
        """
        Merge the "wheres" from the relation query to a has query.

        :param has_query: The has query
        :type has_query: Builder

        :param relation: The relation to count
        :type relation: orator.orm.relations.Relation
        """
        relation_query = relation.get_base_query()

        has_query.merge_wheres(relation_query.wheres, relation_query.get_bindings())

        self._query.merge_bindings(has_query.get_query())

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

        eagers = self._parse_relations(list(relations))

        self._eager_load.update(eagers)

        return self

    def _parse_relations(self, relations):
        """
        Parse a list of relations into individuals.

        :param relations: The relation to parse
        :type relations: list

        :rtype: dict
        """
        results = {}

        for relation in relations:
            if isinstance(relation, dict):
                name = list(relation.keys())[0]
                constraints = relation[name]
            else:
                name = relation
                constraints = self.__class__(self.get_query().new_query())

            results = self._parse_nested(name, results)

            results[name] = constraints

        return results

    def _parse_nested(self, name, results):
        """
        Parse the nested relationship in a relation.

        :param name: The name of the relationship
        :type name: str

        :type results: dict

        :rtype: dict
        """
        progress = []

        for segment in name.split('.'):
            progress.append(segment)

            last = '.'.join(progress)
            if last not in results:
                results[last] = self.__class__(self.get_query().new_query())

        return results

    def _call_scope(self, scope, *args, **kwargs):
        """
        Call the given model scope.

        :param scope: The scope to call
        :type scope: str
        """
        result = getattr(self._model, scope)(self, *args, **kwargs)

        return result or self

    def get_query(self):
        """
        Get the underlying query instance.

        :rtype: QueryBuilder
        """
        return self._query

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
        scope = 'scope_%s' % method
        is_scope = False
        is_macro = False
        if hasattr(self._model, scope):
            is_scope = True
            attribute = getattr(self._model, scope)
        elif method in self._macros:
            is_macro = True
            attribute = self._macros[method]
        else:
            attribute = getattr(self._query, method)

        def call(*args, **kwargs):
            if is_scope:
                return self._call_scope(scope, *args, **kwargs)
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
        try:
            object.__getattribute__(self, item)
        except AttributeError:
            # TODO: macros
            return self.__dynamic(item)
