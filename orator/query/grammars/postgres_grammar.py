# -*- coding: utf-8 -*-

from .grammar import QueryGrammar
from ...utils import basestring


class PostgresQueryGrammar(QueryGrammar):

    _operators = [
        '=', '<', '>', '<=', '>=', '<>', '!=',
        'like', 'not like', 'between', 'ilike',
        '&', '|', '#', '<<', '>>'
    ]

    marker = '%s'

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

        if value:
            return 'FOR UPDATE'

        return 'FOR SHARE'

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
        table = self.wrap_table(query.from__)

        columns = self._compile_update_columns(values)

        from_ = self._compile_update_from(query)

        where = self._compile_update_wheres(query)

        return ('UPDATE %s SET %s%s %s' % (table, columns, from_, where)).strip()

    def _compile_update_columns(self, values):
        """
        Compile the columns for the update statement

        :param values: The columns
        :type values: dict

        :return: The compiled columns
        :rtype: str
        """
        columns = []

        for key, value in values.items():
            columns.append('%s = %s' % (self.wrap(key), self.parameter(value)))

        return ', '.join(columns)

    def _compile_update_from(self, query):
        """
        Compile the "from" clause for an update with a join.

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The compiled sql
        :rtype: str
        """
        if not query.joins:
            return ''

        froms = []

        for join in query.joins:
            froms.append(self.wrap_table(join.table))

        if len(froms):
            return ' FROM %s' % ', '.join(froms)

        return ''

    def _compile_update_wheres(self, query):
        """
        Compile the additional where clauses for updates with joins.

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The compiled sql
        :rtype: str
        """
        base_where = self._compile_wheres(query)

        if not query.joins:
            return base_where

        join_where = self._compile_update_join_wheres(query)

        if not base_where.strip():
            return 'WHERE %s' % self._remove_leading_boolean(join_where)

        return '%s %s' % (base_where, join_where)

    def _compile_update_join_wheres(self, query):
        """
        Compile the "join" clauses for an update.

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The compiled sql
        :rtype: str
        """
        join_wheres = []

        for join in query.joins:
            for clause in join.clauses:
                join_wheres.append(self._compile_join_constraints(clause))

        return ' '.join(join_wheres)

    def compile_insert_get_id(self, query, values, sequence=None):
        """
        Compile an insert and get ID statement into SQL.

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param values: The values to insert
        :type values: dict

        :param sequence: The id sequence
        :type sequence: str

        :return: The compiled statement
        :rtype: str
        """
        if sequence is None:
            sequence = 'id'

        return '%s RETURNING %s'\
               % (self.compile_insert(query, values), self.wrap(sequence))

    def compile_truncate(self, query):
        """
        Compile a truncate table statement into SQL.

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The compiled statement
        :rtype: str
        """
        return {
            'TRUNCATE %s RESTART IDENTITY' % self.wrap_table(query.from__): {}
        }
