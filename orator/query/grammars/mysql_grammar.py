# -*- coding: utf-8 -*-

from .grammar import QueryGrammar
from ...utils import basestring


class MySQLQueryGrammar(QueryGrammar):

    _select_components = [
        'aggregate_',
        'columns',
        'from__',
        'joins',
        'wheres',
        'groups',
        'havings',
        'orders',
        'limit_',
        'offset_',
        'lock_'
    ]

    marker = '%s'

    def compile_select(self, query):
        """
        Compile a select query into SQL

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The compiled sql
        :rtype: str
        """
        sql = super(MySQLQueryGrammar, self).compile_select(query)

        if query.unions:
            sql = '(%s) %s' % (sql, self._compile_unions(query))

        return sql

    def _compile_union(self, union):
        """
        Compile a single union statement

        :param union: The union statement
        :type union: dict

        :return: The compiled union statement
        :rtype: str
        """
        if union['all']:
            joiner = ' UNION ALL '
        else:
            joiner = ' UNION '

        return '%s(%s)' % (joiner, union['query'].to_sql())

    def _compile_lock(self, query, value):
        """
        Compile the lock into SQL

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param value: The lock value
        :type value: bool or str

        :return: The compiled lock
        :rtype: str
        """
        if isinstance(value, basestring):
            return value

        if value is True:
            return 'FOR UPDATE'
        elif value is False:
            return 'LOCK IN SHARE MODE'

    def compile_update(self, query, values):
        """
        Compile an update statement into SQL

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param values: The update values
        :type values: dict

        :return: The compiled update
        :rtype: str
        """
        sql = super(MySQLQueryGrammar, self).compile_update(query, values)

        if query.orders:
            sql += ' %s' % self._compile_orders(query, query.orders)

        if query.limit_:
            sql += ' %s' % self._compile_limit(query, query.limit_)

        return sql.rstrip()

    def compile_delete(self, query):
        """
        Compile a delete statement into SQL

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The compiled update
        :rtype: str
        """
        table = self.wrap_table(query.from__)

        if isinstance(query.wheres, list):
            wheres = self._compile_wheres(query)
        else:
            wheres = ''

        if query.joins:
            joins = ' %s' % self._compile_joins(query, query.joins)

            sql = 'DELETE %s FROM %s%s %s' % (table, table, joins, wheres)
        else:
            sql = 'DELETE FROM %s %s' % (table, wheres)

        sql = sql.strip()

        if query.orders:
            sql += ' %s' % self._compile_orders(query, query.orders)

        if query.limit_:
            sql += ' %s' % self._compile_limit(query, query.limit_)

        return sql

    def _wrap_value(self, value):
        """
        Wrap a single string in keyword identifers

        :param value: The value to wrap
        :type value: str

        :return: The wrapped value
        :rtype: str
        """
        if value == '*':
            return value

        return '`%s`' % value.replace('`', '``')
