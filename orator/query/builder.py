# -*- coding: utf-8 -*-

import re
import copy
import datetime

from itertools import chain
from collections import OrderedDict

from .expression import QueryExpression
from .join_clause import JoinClause
from ..pagination import Paginator, LengthAwarePaginator
from ..utils import basestring, Null
from ..exceptions import ArgumentError
from ..support import Collection


class QueryBuilder(object):

    _operators = [
        "=",
        "<",
        ">",
        "<=",
        ">=",
        "<>",
        "!=",
        "like",
        "like binary",
        "not like",
        "between",
        "ilike",
        "&",
        "|",
        "^",
        "<<",
        ">>",
        "rlike",
        "regexp",
        "not regexp",
        "~",
        "~*",
        "!~",
        "!~*",
        "similar to",
        "not similar to",
    ]

    def __init__(self, connection, grammar, processor):
        """
        Constructor

        :param connection: A Connection instance
        :type connection: Connection

        :param grammar: A QueryGrammar instance
        :type grammar: QueryGrammar

        :param processor: A QueryProcessor instance
        :type processor: QueryProcessor
        """
        self._grammar = grammar
        self._processor = processor
        self._connection = connection
        self._bindings = OrderedDict()
        for type in ["select", "join", "where", "having", "order"]:
            self._bindings[type] = []

        self.aggregate_ = None
        self.columns = []
        self.distinct_ = False
        self.from__ = ""
        self.joins = []
        self.wheres = []
        self.groups = []
        self.havings = []
        self.orders = []
        self.limit_ = None
        self.offset_ = None
        self.unions = []
        self.union_limit = None
        self.union_offset = None
        self.union_orders = []
        self.lock_ = None

        self._backups = {}

        self._use_write_connection = False

    def select(self, *columns):
        """
        Set the columns to be selected

        :param columns: The columns to be selected
        :type columns: tuple

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if not columns:
            columns = ["*"]

        self.columns = list(columns)

        return self

    def select_raw(self, expression, bindings=None):
        """
        Add a new raw select expression to the query

        :param expression: The raw expression
        :type expression: str

        :param bindings: The expression bindings
        :type bindings: list

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        self.add_select(QueryExpression(expression))

        if bindings:
            self.add_binding(bindings, "select")

        return self

    def select_sub(self, query, as_):
        """
        Add a subselect expression to the query

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param as_: The subselect alias
        :type as_: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if isinstance(query, QueryBuilder):
            bindings = query.get_bindings()

            query = query.to_sql()
        elif isinstance(query, basestring):
            bindings = []
        else:
            raise ArgumentError("Invalid subselect")

        return self.select_raw(
            "(%s) AS %s" % (query, self._grammar.wrap(as_)), bindings
        )

    def add_select(self, *column):
        """
        Add a new select column to query

        :param column: The column to add
        :type column: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if not column:
            column = []

        self.columns += list(column)

        return self

    def distinct(self):
        """
        Force the query to return only distinct result

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        self.distinct_ = True

        return self

    def from_(self, table):
        """
        Set the query target table

        :param table: The table to target
        :type table: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        self.from__ = table

        return self

    def join(self, table, one=None, operator=None, two=None, type="inner", where=False):
        """
        Add a join clause to the query

        :param table: The table to join with, can also be a JoinClause instance
        :type table: str or JoinClause

        :param one: The first column of the join condition
        :type one: str

        :param operator: The operator of the join condition
        :type operator: str

        :param two: The second column of the join condition
        :type two: str

        :param type: The join type
        :type type: str

        :param where: Whether to use a "where" rather than a "on"
        :type where: bool

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if isinstance(table, JoinClause):
            self.joins.append(table)
        else:
            if one is None:
                raise ArgumentError('Missing "one" argument')

            join = JoinClause(table, type)

            self.joins.append(join.on(one, operator, two, "and", where))

        return self

    def join_where(self, table, one, operator, two, type="inner"):
        """
        Add a "join where" clause to the query

        :param table: The table to join with, can also be a JoinClause instance
        :type table: str or JoinClause

        :param one: The first column of the join condition
        :type one: str

        :param operator: The operator of the join condition
        :type operator: str

        :param two: The second column of the join condition
        :type two: str

        :param type: The join type
        :type type: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.join(table, one, operator, two, type, True)

    def left_join(self, table, one=None, operator=None, two=None):
        """
        Add a left join to the query

        :param table: The table to join with, can also be a JoinClause instance
        :type table: str or JoinClause

        :param one: The first column of the join condition
        :type one: str

        :param operator: The operator of the join condition
        :type operator: str

        :param two: The second column of the join condition
        :type two: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if isinstance(table, JoinClause):
            table.type = "left"

        return self.join(table, one, operator, two, "left")

    def left_join_where(self, table, one, operator, two):
        """
        Add a "left join where" clause to the query

        :param table: The table to join with, can also be a JoinClause instance
        :type table: str or JoinClause

        :param one: The first column of the join condition
        :type one: str

        :param operator: The operator of the join condition
        :type operator: str

        :param two: The second column of the join condition
        :type two: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.join_where(table, one, operator, two, "left")

    def right_join(self, table, one=None, operator=None, two=None):
        """
        Add a right join to the query

        :param table: The table to join with, can also be a JoinClause instance
        :type table: str or JoinClause

        :param one: The first column of the join condition
        :type one: str

        :param operator: The operator of the join condition
        :type operator: str

        :param two: The second column of the join condition
        :type two: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if isinstance(table, JoinClause):
            table.type = "right"

        return self.join(table, one, operator, two, "right")

    def right_join_where(self, table, one, operator, two):
        """
        Add a "right join where" clause to the query

        :param table: The table to join with, can also be a JoinClause instance
        :type table: str or JoinClause

        :param one: The first column of the join condition
        :type one: str

        :param operator: The operator of the join condition
        :type operator: str

        :param two: The second column of the join condition
        :type two: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.join_where(table, one, operator, two, "right")

    def where(self, column, operator=Null(), value=None, boolean="and"):
        """
        Add a where clause to the query

        :param column: The column of the where clause, can also be a QueryBuilder instance for sub where
        :type column: str or QueryBuilder

        :param operator: The operator of the where clause
        :type operator: str

        :param value: The value of the where clause
        :type value: mixed

        :param boolean: The boolean of the where clause
        :type boolean: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        # If the column is an array, we will assume it is an array of key-value pairs
        # and can add them each as a where clause. We will maintain the boolean we
        # received when the method was called and pass it into the nested where.
        if isinstance(column, dict):
            nested = self.new_query()
            for key, value in column.items():
                nested.where(key, "=", value)

            return self.where_nested(nested, boolean)

        if isinstance(column, QueryBuilder):
            return self.where_nested(column, boolean)

        if isinstance(column, list):
            nested = self.new_query()
            for condition in column:
                if isinstance(condition, list) and len(condition) == 3:
                    nested.where(condition[0], condition[1], condition[2])
                else:
                    raise ArgumentError("Invalid conditions in where() clause")
            return self.where_nested(nested, boolean)

        if value is None:
            if not isinstance(operator, Null):
                value = operator
                operator = "="
            else:
                raise ArgumentError("Value must be provided")

        if operator not in self._operators:
            value = operator
            operator = "="

        if isinstance(value, QueryBuilder):
            return self._where_sub(column, operator, value, boolean)

        if value is None:
            return self.where_null(column, boolean, operator != "=")

        type = "basic"

        self.wheres.append(
            {
                "type": type,
                "column": column,
                "operator": operator,
                "value": value,
                "boolean": boolean,
            }
        )

        if not isinstance(value, QueryExpression):
            self.add_binding(value, "where")

        return self

    def or_where(self, column, operator=None, value=None):
        return self.where(column, operator, value, "or")

    def _invalid_operator_and_value(self, operator, value):
        is_operator = operator in self._operators

        return is_operator and operator != "=" and value is None

    def where_raw(self, sql, bindings=None, boolean="and"):
        type = "raw"

        self.wheres.append({"type": type, "sql": sql, "boolean": boolean})

        self.add_binding(bindings, "where")

        return self

    def or_where_raw(self, sql, bindings=None):
        return self.where_raw(sql, bindings, "or")

    def where_between(self, column, values, boolean="and", negate=False):
        type = "between"

        self.wheres.append(
            {"column": column, "type": type, "boolean": boolean, "not": negate}
        )

        self.add_binding(values, "where")

        return self

    def or_where_between(self, column, values):
        return self.where_between(column, values, "or")

    def where_not_between(self, column, values, boolean="and"):
        return self.where_between(column, values, boolean, True)

    def or_where_not_between(self, column, values):
        return self.where_not_between(column, values, "or")

    def where_nested(self, query, boolean="and"):
        query.from_(self.from__)

        return self.add_nested_where_query(query, boolean)

    def for_nested_where(self):
        """
        Create a new query instance for nested where condition.

        :rtype: QueryBuilder
        """
        query = self.new_query()

        return query.from_(self.from__)

    def add_nested_where_query(self, query, boolean="and"):
        if len(query.wheres):
            type = "nested"

            self.wheres.append({"type": type, "query": query, "boolean": boolean})

            self.merge_bindings(query)

        return self

    def _where_sub(self, column, operator, query, boolean):
        type = "sub"

        self.wheres.append(
            {
                "type": type,
                "column": column,
                "operator": operator,
                "query": query,
                "boolean": boolean,
            }
        )

        self.merge_bindings(query)

        return self

    def where_exists(self, query, boolean="and", negate=False):
        """
        Add an exists clause to the query.

        :param query: The exists query
        :type query: QueryBuilder

        :type boolean: str

        :type negate: bool

        :rtype: QueryBuilder
        """
        if negate:
            type = "not_exists"
        else:
            type = "exists"

        self.wheres.append({"type": type, "query": query, "boolean": boolean})

        self.merge_bindings(query)

        return self

    def or_where_exists(self, query, negate=False):
        """
        Add an or exists clause to the query.

        :param query: The exists query
        :type query: QueryBuilder

        :type negate: bool

        :rtype: QueryBuilder
        """
        return self.where_exists(query, "or", negate)

    def where_not_exists(self, query, boolean="and"):
        """
        Add a where not exists clause to the query.

        :param query: The exists query
        :type query: QueryBuilder

        :type boolean: str

        :rtype: QueryBuilder
        """
        return self.where_exists(query, boolean, True)

    def or_where_not_exists(self, query):
        """
        Add a or where not exists clause to the query.

        :param query: The exists query
        :type query: QueryBuilder

        :rtype: QueryBuilder
        """
        return self.or_where_exists(query, True)

    def where_in(self, column, values, boolean="and", negate=False):
        if negate:
            type = "not_in"
        else:
            type = "in"

        if isinstance(values, QueryBuilder):
            return self._where_in_sub(column, values, boolean, negate)

        if isinstance(values, Collection):
            values = values.all()

        self.wheres.append(
            {"type": type, "column": column, "values": values, "boolean": boolean}
        )

        self.add_binding(values, "where")

        return self

    def or_where_in(self, column, values):
        return self.where_in(column, values, "or")

    def where_not_in(self, column, values, boolean="and"):
        return self.where_in(column, values, boolean, True)

    def or_where_not_in(self, column, values):
        return self.where_not_in(column, values, "or")

    def _where_in_sub(self, column, query, boolean, negate=False):
        """
        Add a where in with a sub select to the query

        :param column: The column
        :type column: str

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param boolean: The boolean operator
        :type boolean: str

        :param negate: Whether it is a not where in
        :param negate: bool

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if negate:
            type = "not_in_sub"
        else:
            type = "in_sub"

        self.wheres.append(
            {"type": type, "column": column, "query": query, "boolean": boolean}
        )

        self.merge_bindings(query)

        return self

    def where_null(self, column, boolean="and", negate=False):
        if negate:
            type = "not_null"
        else:
            type = "null"

        self.wheres.append({"type": type, "column": column, "boolean": boolean})

        return self

    def or_where_null(self, column):
        return self.where_null(column, "or")

    def where_not_null(self, column, boolean="and"):
        return self.where_null(column, boolean, True)

    def or_where_not_null(self, column):
        return self.where_not_null(column, "or")

    def where_date(self, column, operator, value, boolean="and"):
        return self._add_date_based_where("date", column, operator, value, boolean)

    def where_day(self, column, operator, value, boolean="and"):
        return self._add_date_based_where("day", column, operator, value, boolean)

    def where_month(self, column, operator, value, boolean="and"):
        return self._add_date_based_where("month", column, operator, value, boolean)

    def where_year(self, column, operator, value, boolean="and"):
        return self._add_date_based_where("year", column, operator, value, boolean)

    def _add_date_based_where(self, type, column, operator, value, boolean="and"):
        self.wheres.append(
            {
                "type": type,
                "column": column,
                "boolean": boolean,
                "operator": operator,
                "value": value,
            }
        )

        self.add_binding(value, "where")

    def dynamic_where(self, method):
        finder = method[6:]

        def dynamic_where(*parameters):
            segments = re.split("_(and|or)_(?=[a-z])", finder, 0, re.I)

            connector = "and"

            index = 0

            for segment in segments:
                if segment.lower() != "and" and segment.lower() != "or":
                    self._add_dynamic(segment, connector, parameters, index)

                    index += 1
                else:
                    connector = segment

            return self

        return dynamic_where

    def _add_dynamic(self, segment, connector, parameters, index):
        self.where(segment, "=", parameters[index], connector)

    def group_by(self, *columns):
        """
        Add a "group by" clause to the query

        :param columns: The columns to group by
        :type columns: tuple

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        for column in columns:
            self.groups.append(column)

        return self

    def having(self, column, operator=None, value=None, boolean="and"):
        """
        Add a "having" clause to the query

        :param column: The column
        :type column: str

        :param operator: The having clause operator
        :type operator: str

        :param value: The having clause value
        :type value: mixed

        :param boolean: Boolean joiner type
        :type boolean: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        type = "basic"

        self.havings.append(
            {
                "type": type,
                "column": column,
                "operator": operator,
                "value": value,
                "boolean": boolean,
            }
        )

        if not isinstance(value, QueryExpression):
            self.add_binding(value, "having")

        return self

    def or_having(self, column, operator=None, value=None):
        """
        Add a "having" clause to the query

        :param column: The column
        :type column: str

        :param operator: The having clause operator
        :type operator: str

        :param value: The having clause value
        :type value: mixed

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.having(column, operator, value, "or")

    def having_raw(self, sql, bindings=None, boolean="and"):
        """
        Add a raw having clause to the query

        :param sql: The raw query
        :type sql: str

        :param bindings: The query bindings
        :type bindings: list

        :param boolean: Boolean joiner type
        :type boolean: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        type = "raw"

        self.havings.append({"type": type, "sql": sql, "boolean": boolean})

        self.add_binding(bindings, "having")

        return self

    def or_having_raw(self, sql, bindings=None):
        """
        Add a raw having clause to the query

        :param sql: The raw query
        :type sql: str

        :param bindings: The query bindings
        :type bindings: list

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.having_raw(sql, bindings, "or")

    def order_by(self, column, direction="asc"):
        """
        Add a "order by" clause to the query

        :param column: The order by column
        :type column: str

        :param direction: The direction of the order
        :type direction: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if self.unions:
            prop = "union_orders"
        else:
            prop = "orders"

        if direction.lower() == "asc":
            direction = "asc"
        else:
            direction = "desc"

        getattr(self, prop).append({"column": column, "direction": direction})

        return self

    def latest(self, column="created_at"):
        """
        Add an "order by" clause for a timestamp to the query
        in descending order

        :param column: The order by column
        :type column: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.order_by(column, "desc")

    def oldest(self, column="created_at"):
        """
        Add an "order by" clause for a timestamp to the query
        in ascending order

        :param column: The order by column
        :type column: str

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.order_by(column, "asc")

    def order_by_raw(self, sql, bindings=None):
        """
        Add a raw "order by" clause to the query

        :param sql: The raw clause
        :type sql: str

        :param bindings: The bdings
        :param bindings: list

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        if bindings is None:
            bindings = []

        type = "raw"

        self.orders.append({"type": type, "sql": sql})

        self.add_binding(bindings, "order")

        return self

    def offset(self, value):
        if self.unions:
            prop = "union_offset"
        else:
            prop = "offset_"

        setattr(self, prop, max(0, value))

        return self

    def skip(self, value):
        return self.offset(value)

    def limit(self, value):
        if self.unions:
            prop = "union_limit"
        else:
            prop = "limit_"

        if value is None or value > 0:
            setattr(self, prop, value)

        return self

    def take(self, value):
        return self.limit(value)

    def for_page(self, page, per_page=15):
        return self.skip((page - 1) * per_page).take(per_page)

    def union(self, query, all=False):
        """
        Add a union statement to the query

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param all: Whether it is a "union all" statement
        :type all: bool

        :return: The query
        :rtype: QueryBuilder
        """
        self.unions.append({"query": query, "all": all})

        return self.merge_bindings(query)

    def union_all(self, query):
        """
        Add a union all statement to the query

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The query
        :rtype: QueryBuilder
        """
        return self.union(query, True)

    def lock(self, value=True):
        """
        Lock the selected rows in the table

        :param value: Whether it is a lock for update or a shared lock
        :type value: bool

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        self.lock_ = value

        return self

    def lock_for_update(self):
        """
        Lock the selected rows in the table for updating.

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.lock(True)

    def shared_lock(self):
        """
        Share lock the selected rows in the table.

        :return: The current QueryBuilder instance
        :rtype: QueryBuilder
        """
        return self.lock(False)

    def to_sql(self):
        """
        Get the SQL representation of the query

        :return: The SQL representation of the query
        :rtype: str
        """
        return self._grammar.compile_select(self)

    def find(self, id, columns=None):
        """
        Execute a query for a single record by id

        :param id: The id of the record to retrieve
        :type id: mixed

        :param columns: The columns of the record to retrive
        :type columns: list

        :return: mixed
        :rtype: mixed
        """
        if not columns:
            columns = ["*"]

        return self.where("id", "=", id).first(1, columns)

    def pluck(self, column):
        """
        Pluck a single column's value from the first results of a query

        :param column: The column to pluck the value from
        :type column: str

        :return: The value of column
        :rtype: mixed
        """
        result = self.first(1, [column])

        if result:
            return result[column]

        return

    def first(self, limit=1, columns=None):
        """
        Execute the query and get the first results

        :param limit: The number of results to get
        :type limit: int

        :param columns: The columns to get
        :type columns: list

        :return: The result
        :rtype: mixed
        """
        if not columns:
            columns = ["*"]

        return self.take(limit).get(columns).first()

    def get(self, columns=None):
        """
        Execute the query as a "select" statement

        :param columns: The columns to get
        :type columns: list

        :return: The result
        :rtype: Collection
        """
        if not columns:
            columns = ["*"]

        original = self.columns

        if not original:
            self.columns = columns

        results = self._processor.process_select(self, self._run_select())

        self.columns = original

        return Collection(results)

    def _run_select(self):
        """
        Run the query as a "select" statement against the connection.

        :return: The result
        :rtype: list
        """
        return self._connection.select(
            self.to_sql(), self.get_bindings(), not self._use_write_connection
        )

    def paginate(self, per_page=15, current_page=None, columns=None):
        """
        Paginate the given query.

        :param per_page: The number of records per page
        :type per_page: int

        :param current_page: The current page of results
        :type current_page: int

        :param columns: The columns to return
        :type columns: list

        :return: The paginator
        :rtype: LengthAwarePaginator
        """
        if columns is None:
            columns = ["*"]

        page = current_page or Paginator.resolve_current_page()

        total = self.get_count_for_pagination()

        results = self.for_page(page, per_page).get(columns)

        return LengthAwarePaginator(results, total, per_page, page)

    def simple_paginate(self, per_page=15, current_page=None, columns=None):
        """
        Paginate the given query.

        :param per_page: The number of records per page
        :type per_page: int

        :param current_page: The current page of results
        :type current_page: int

        :param columns: The columns to return
        :type columns: list

        :return: The paginator
        :rtype: Paginator
        """
        if columns is None:
            columns = ["*"]

        page = current_page or Paginator.resolve_current_page()

        self.skip((page - 1) * per_page).take(per_page + 1)

        return Paginator(self.get(columns), per_page, page)

    def get_count_for_pagination(self):
        self._backup_fields_for_count()

        total = self.count()

        self._restore_fields_for_count()

        return total

    def _backup_fields_for_count(self):
        for field, binding in [("orders", "order"), ("limit", None), ("offset", None)]:
            self._backups[field] = {}
            self._backups[field]["query"] = getattr(self, field)
            if binding is not None:
                self._backups[field]["binding"] = self.get_raw_bindings()[binding]
                self.set_bindings([], binding)

            setattr(self, field, None)

    def _restore_fields_for_count(self):
        for field, binding in [("orders", "order"), ("limit", None), ("offset", None)]:
            setattr(self, field, self._backups[field]["query"])
            if binding is not None and self._backups[field]["binding"] is not None:
                self.add_binding(self._backups[field]["binding"], binding)

        self._backups = {}

    def chunk(self, count):
        """
        Chunk the results of the query

        :param count: The chunk size
        :type count: int

        :return: The current chunk
        :rtype: list
        """
        for chunk in self._connection.select_many(
            count, self.to_sql(), self.get_bindings(), not self._use_write_connection
        ):
            yield chunk

    def lists(self, column, key=None):
        """
        Get a list with the values of a given column

        :param column: The column to get the values for
        :type column: str

        :param key: The key
        :type key: str

        :return: The list of values
        :rtype: Collection or dict
        """
        columns = self._get_list_select(column, key)

        if key is not None:
            results = {}
            for result in self.get(columns):
                results[result[key]] = result[column]
        else:
            results = Collection(list(map(lambda x: x[column], self.get(columns))))

        return results

    def _get_list_select(self, column, key=None):
        """
        Get the columns that should be used in a list

        :param column: The column to get the values for
        :type column: str

        :param key: The key
        :type key: str

        :return: The list of values
        :rtype: list
        """
        if key is None:
            elements = [column]
        else:
            elements = [column, key]

        select = []
        for elem in elements:
            dot = elem.find(".")

            if dot >= 0:
                select.append(column[dot + 1 :])
            else:
                select.append(elem)

        return select

    def implode(self, column, glue=""):
        """
        Concatenate values of a given column as a string.

        :param column: The column to glue the values for
        :type column: str

        :param glue: The glue string
        :type glue: str

        :return: The glued value
        :rtype: str
        """
        return self.lists(column).implode(glue)

    def exists(self):
        """
        Determine if any rows exist for the current query.

        :return: Whether the rows exist or not
        :rtype: bool
        """
        limit = self.limit_

        result = self.limit(1).count() > 0

        self.limit(limit)

        return result

    def count(self, *columns):
        """
        Retrieve the "count" result of the query

        :param columns: The columns to get
        :type columns: tuple

        :return: The count
        :rtype: int
        """
        if not columns and self.distinct_:
            columns = self.columns

        if not columns:
            columns = ["*"]

        return int(self.aggregate("count", *columns))

    def min(self, column):
        """
        Retrieve the "min" result of the query

        :param column: The column to get the minimun for
        :type column: tuple

        :return: The min
        :rtype: int
        """
        return self.aggregate("min", *[column])

    def max(self, column):
        """
        Retrieve the "max" result of the query

        :param column: The column to get the maximum for
        :type column: tuple

        :return: The max
        :rtype: int
        """
        if not column:
            columns = ["*"]

        return self.aggregate("max", *[column])

    def sum(self, column):
        """
        Retrieve the "sum" result of the query

        :param column: The column to get the sum for
        :type column: tuple

        :return: The sum
        :rtype: int
        """
        return self.aggregate("sum", *[column])

    def avg(self, column):
        """
        Retrieve the "avg" result of the query

        :param column: The column to get the average for
        :type column: tuple

        :return: The count
        :rtype: int
        """

        return self.aggregate("avg", *[column])

    def aggregate(self, func, *columns):
        """
        Execute an aggregate function against the database

        :param func: The aggregate function
        :type func: str

        :param columns: The columns to execute the fnction for
        :type columns: tuple

        :return: The aggregate result
        :rtype: mixed
        """
        if not columns:
            columns = ["*"]

        self.aggregate_ = {"function": func, "columns": columns}

        previous_columns = self.columns

        results = self.get(*columns).all()

        self.aggregate_ = None

        self.columns = previous_columns

        if len(results) > 0:
            return dict((k.lower(), v) for k, v in results[0].items())["aggregate"]

    def insert(self, _values=None, **values):
        """
        Insert a new record into the database

        :param _values: The new record values
        :type _values: dict or list

        :param values: The new record values as keyword arguments
        :type values: dict

        :return: The result
        :rtype: bool
        """
        if not values and not _values:
            return True

        if not isinstance(_values, list):
            if _values is not None:
                values.update(_values)

            values = [values]
        else:
            values = _values
            for i, value in enumerate(values):
                values[i] = OrderedDict(sorted(value.items()))

        bindings = []

        for record in values:
            for value in record.values():
                bindings.append(value)

        sql = self._grammar.compile_insert(self, values)

        bindings = self._clean_bindings(bindings)

        return self._connection.insert(sql, bindings)

    def insert_get_id(self, values, sequence=None):
        """
        Insert a new record and get the value of the primary key

        :param values: The new record values
        :type values: dict

        :param sequence: The name of the primary key
        :type sequence: str

        :return: The value of the primary key
        :rtype: int
        """
        values = OrderedDict(sorted(values.items()))

        sql = self._grammar.compile_insert_get_id(self, values, sequence)

        values = self._clean_bindings(values.values())

        return self._processor.process_insert_get_id(self, sql, values, sequence)

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

        values = OrderedDict(sorted(values.items()))

        bindings = list(values.values()) + self.get_bindings()

        sql = self._grammar.compile_update(self, values)

        return self._connection.update(sql, self._clean_bindings(bindings))

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
        wrapped = self._grammar.wrap(column)

        if extras is None:
            extras = {}

        columns = {column: self.raw("%s + %s" % (wrapped, amount))}
        columns.update(extras)

        return self.update(**columns)

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
        wrapped = self._grammar.wrap(column)

        if extras is None:
            extras = {}

        columns = {column: self.raw("%s - %s" % (wrapped, amount))}
        columns.update(extras)

        return self.update(**columns)

    def delete(self, id=None):
        """
        Delete a record from the database

        :param id: The id of the row to delete
        :type id: mixed

        :return: The number of rows deleted
        :rtype: int
        """
        if id is not None:
            self.where("id", "=", id)

        sql = self._grammar.compile_delete(self)

        return self._connection.delete(sql, self.get_bindings())

    def truncate(self):
        """
        Run a truncate statement on the table

        :rtype: None
        """
        for sql, bindings in self._grammar.compile_truncate(self).items():
            self._connection.statement(sql, bindings)

    def new_query(self):
        """
        Get a new instance of the query builder

        :return: A new QueryBuilder instance
        :rtype: QueryBuilder
        """
        return QueryBuilder(self._connection, self._grammar, self._processor)

    def merge_wheres(self, wheres, bindings):
        """
        Merge a list of where clauses and bindings

        :param wheres: A list of where clauses
        :type wheres: list

        :param bindings: A list of bindings
        :type bindings: list

        :rtype: None
        """
        self.wheres = self.wheres + wheres
        self._bindings["where"] = self._bindings["where"] + bindings

    def _clean_bindings(self, bindings):
        """
        Remove all of the expressions from bindings

        :param bindings: The bindings to clean
        :type bindings: list

        :return: The cleaned bindings
        :rtype: list
        """
        return list(filter(lambda b: not isinstance(b, QueryExpression), bindings))

    def raw(self, value):
        """
        Create a raw database expression

        :param value: The value of the raw expression
        :type value: mixed

        :return: A QueryExpression instance
        :rtype: QueryExpression
        """
        return self._connection.raw(value)

    def get_bindings(self):
        bindings = []
        for value in chain(*self._bindings.values()):
            if isinstance(value, datetime.date):
                value = value.strftime(self._grammar.get_date_format())

            bindings.append(value)

        return bindings

    def get_raw_bindings(self):
        return self._bindings

    def set_bindings(self, bindings, type="where"):
        if type not in self._bindings:
            raise ArgumentError("Invalid binding type: %s" % type)

        self._bindings[type] = bindings

        return self

    def add_binding(self, value, type="where"):
        if value is None:
            return self

        if type not in self._bindings:
            raise ArgumentError("Invalid binding type: %s" % type)

        if isinstance(value, (list, tuple)):
            self._bindings[type] += value
        else:
            self._bindings[type].append(value)

        return self

    def merge_bindings(self, query):
        for type in self._bindings:
            self._bindings[type] += query.get_raw_bindings()[type]

        return self

    def merge(self, query):
        """
        Merge current query with another.

        :param query: The query to merge with
        :type query: QueryBuilder
        """
        self.columns += query.columns
        self.joins += query.joins
        self.wheres += query.wheres
        self.groups += query.groups
        self.havings += query.havings
        self.orders += query.orders
        self.distinct_ = query.distinct_

        if self.columns:
            self.columns = Collection(self.columns).unique().all()

        if query.limit_:
            self.limit_ = query.limit_

        if query.offset_:
            self.offset_ = None

        self.unions += query.unions

        if query.union_limit:
            self.union_limit = query.union_limit

        if query.union_offset:
            self.union_offset = query.union_offset

        self.union_orders += query.union_orders

        self.merge_bindings(query)

    def get_connection(self):
        """
        Get the query connection

        :return: The current connection instance
        :rtype: orator.connections.connection.Connection
        """
        return self._connection

    def get_processor(self):
        """
        Get the builder processor

        :return: The builder processor
        :rtype: QueryProcessor
        """
        return self._processor

    def get_grammar(self):
        """
        Get the builder query grammar

        :return: The builder query grammar
        :rtype: QueryGrammar
        """
        return self._grammar

    def use_write_connection(self):
        self._use_write_connection = True

        return self

    def __getattr__(self, item):
        if item.startswith("where_"):
            return self.dynamic_where(item)

        raise AttributeError(item)

    def __copy__(self):
        new = self.__class__(self._connection, self._grammar, self._processor)

        new.__dict__.update(
            dict(
                (k, copy.deepcopy(v))
                for k, v in self.__dict__.items()
                if k != "_connection"
            )
        )

        return new

    def __deepcopy__(self, memo):
        return self.__copy__()
