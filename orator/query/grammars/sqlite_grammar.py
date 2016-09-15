# -*- coding: utf-8 -*-

from .grammar import QueryGrammar


class SQLiteQueryGrammar(QueryGrammar):

    _operators = [
        '=', '<', '>', '<=', '>=', '<>', '!=',
        'like', 'not like', 'between', 'ilike',
        '&', '|', '<<', '>>',
    ]

    def compile_insert(self, query, values):
        """
        Compile insert statement into SQL

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param values: The insert values
        :type values: dict or list

        :return: The compiled insert
        :rtype: str
        """
        table = self.wrap_table(query.from__)

        if not isinstance(values, list):
            values = [values]

        # If there is only one row to insert, we just use the normal grammar
        if len(values) == 1:
            return super(SQLiteQueryGrammar, self).compile_insert(query, values)

        names = self.columnize(values[0].keys())

        columns = []

        # SQLite requires us to build the multi-row insert as a listing of select with
        # unions joining them together. So we'll build out this list of columns and
        # then join them all together with select unions to complete the queries.
        for column in values[0].keys():
            columns.append('%s AS %s' % (self.get_marker(), self.wrap(column)))

        columns = [', '.join(columns)] * len(values)

        return 'INSERT INTO %s (%s) SELECT %s'\
               % (table, names, ' UNION ALL SELECT '.join(columns))

    def compile_truncate(self, query):
        """
        Compile a truncate statement into SQL

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :return: The compiled truncate statement
        :rtype: str
        """
        sql = {
            'DELETE FROM sqlite_sequence WHERE name = %s' % self.get_marker(): [query.from__]
        }

        sql['DELETE FROM %s' % self.wrap_table(query.from__)] = []

        return sql

    def _where_day(self, query, where):
        """
        Compile a "where day" clause

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param where: The condition
        :type where: dict

        :return: The compiled clause
        :rtype: str
        """
        return self._date_based_where('%d', query, where)

    def _where_month(self, query, where):
        """
        Compile a "where month" clause

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param where: The condition
        :type where: dict

        :return: The compiled clause
        :rtype: str
        """
        return self._date_based_where('%m', query, where)

    def _where_year(self, query, where):
        """
        Compile a "where year" clause

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param where: The condition
        :type where: dict

        :return: The compiled clause
        :rtype: str
        """
        return self._date_based_where('%Y', query, where)

    def _date_based_where(self, type, query, where):
        """
        Compiled a date where based clause

        :param type: The date type
        :type type: str

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param where: The condition
        :type where: dict

        :return: The compiled clause
        :rtype: str
        """
        value = str(where['value']).zfill(2)
        value = self.parameter(value)

        return 'strftime(\'%s\', %s) %s %s'\
               % (type, self.wrap(where['column']),
                  where['operator'], value)
