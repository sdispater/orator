# -*- coding: utf-8 -*-

import re
from ...support.grammar import Grammar
from ..builder import QueryBuilder
from ...utils import basestring


class QueryGrammar(Grammar):

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
        'unions',
        'lock_'
    ]

    def compile_select(self, query):
        if not query.columns:
            query.columns = ['*']

        return self._concatenate(self._compile_components(query)).strip()

    def _compile_components(self, query):
        sql = {}

        for component in self._select_components:
            # To compile the query, we'll spin through each component of the query and
            # see if that component exists. If it does we'll just call the compiler
            # function for the component which is responsible for making the SQL.
            component_value = getattr(query, component)
            if component_value is not None:
                method = '_compile_%s' % component.replace('_', '')

                sql[component] = getattr(self, method)(query, component_value)

        return sql

    def _compile_aggregate(self, query, aggregate):
        column = self.columnize(aggregate['columns'])

        if query.distinct_ and column != '*':
            column = 'DISTINCT %s' % column

        return 'SELECT %s(%s) AS aggregate' % (aggregate['function'].upper(),
                                               column)

    def _compile_columns(self, query, columns):
        # If the query is actually performing an aggregating select, we will let that
        # compiler handle the building of the select clauses, as it will need some
        # more syntax that is best handled by that function to keep things neat.
        if query.aggregate_ is not None:
            return

        if query.distinct_:
            select = 'SELECT DISTINCT '
        else:
            select = 'SELECT '

        return '%s%s' % (select, self.columnize(columns))

    def _compile_from(self, query, table):
        return 'FROM %s' % self.wrap_table(table)

    def _compile_joins(self, query, joins):
        sql = []

        query.set_bindings([], 'join')

        for join in joins:
            table = self.wrap_table(join.table)

            # First we need to build all of the "on" clauses for the join. There may be many
            # of these clauses so we will need to iterate through each one and build them
            # separately, then we'll join them up into a single string when we're done.
            clauses = []

            for clause in join.clauses:
                clauses.append(self._compile_join_constraints(clause))

            for binding in join.bindings:
                query.add_binding(binding, 'join')

            # Once we have constructed the clauses, we'll need to take the boolean connector
            # off of the first clause as it obviously will not be required on that clause
            # because it leads the rest of the clauses, thus not requiring any boolean.
            clauses[0] = self._remove_leading_boolean(clauses[0])

            clauses = ' '.join(clauses)

            type = join.type

            # Once we have everything ready to go, we will just concatenate all the parts to
            # build the final join statement SQL for the query and we can then return the
            # final clause back to the callers as a single, stringified join statement.

            sql.append('%s JOIN %s ON %s' % (type.upper(), table, clauses))

        return ' '.join(sql)

    def _compile_join_constraints(self, clause):
        first = self.wrap(clause['first'])

        if clause['where']:
            second = self.get_marker()
        else:
            second = self.wrap(clause['second'])

        return '%s %s %s %s' % (clause['boolean'].upper(), first,
                                clause['operator'], second)

    def _compile_wheres(self, query, _=None):
        sql = []

        if query.wheres is None:
            return ''

        # Each type of where clauses has its own compiler function which is responsible
        # for actually creating the where clauses SQL. This helps keep the code nice
        # and maintainable since each clause has a very small method that it uses.
        for where in query.wheres:
            method = '_where_%s' % where['type']

            sql.append('%s %s' % (where['boolean'].upper(),
                                  getattr(self, method)(query, where)))

        # If we actually have some where clauses, we will strip off the first boolean
        # operator, which is added by the query builders for convenience so we can
        # avoid checking for the first clauses in each of the compilers methods.
        if len(sql) > 0:
            sql = ' '.join(sql)

            return 'WHERE %s' % re.sub('AND |OR ', '', sql, 1, re.I)

        return ''

    def _where_nested(self, query, where):
        nested = where['query']

        return '(%s)' % (self._compile_wheres(nested)[6:])

    def _where_sub(self, query, where):
        select = self.compile_select(where['query'])

        return '%s %s (%s)' % (self.wrap(where['column']),
                               where['operator'], select)

    def _where_basic(self, query, where):
        value = self.parameter(where['value'])

        return '%s %s %s' % (self.wrap(where['column']),
                             where['operator'], value)

    def _where_between(self, query, where):
        if where['not']:
            between = 'NOT BETWEEN'
        else:
            between = 'BETWEEN'

        return '%s %s %s AND %s' % (self.wrap(where['column']), between,
                                    self.get_marker(), self.get_marker())

    def _where_exists(self, query, where):
        return 'EXISTS (%s)' % self.compile_select(where['query'])

    def _where_not_exists(self, query, where):
        return 'NOT EXISTS (%s)' % self.compile_select(where['query'])

    def _where_in(self, query, where):
        if not where['values']:
            return '0 = 1'

        values = self.parameterize(where['values'])

        return '%s IN (%s)' % (self.wrap(where['column']), values)

    def _where_not_in(self, query, where):
        if not where['values']:
            return '1 = 1'

        values = self.parameterize(where['values'])

        return '%s NOT IN (%s)' % (self.wrap(where['column']), values)

    def _where_in_sub(self, query, where):
        select = self.compile_select(where['query'])

        return '%s IN (%s)' % (self.wrap(where['column']), select)

    def _where_not_in_sub(self, query, where):
        select = self.compile_select(where['query'])

        return '%s NOT IN (%s)' % (self.wrap(where['column']), select)

    def _where_null(self, query, where):
        return '%s IS NULL' % self.wrap(where['column'])

    def _where_not_null(self, query, where):
        return '%s IS NOT NULL' % self.wrap(where['column'])

    def _where_date(self, query, where):
        return self._date_based_where('date', query, where)

    def _where_day(self, query, where):
        return self._date_based_where('day', query, where)

    def _where_month(self, query, where):
        return self._date_based_where('month', query, where)

    def _where_year(self, query, where):
        return self._date_based_where('year', query, where)

    def _date_based_where(self, type, query, where):
        value = self.parameter(where['value'])

        return '%s(%s) %s %s' % (type.upper(), self.wrap(where['column']),
                                 where['operator'], value)

    def _where_raw(self, query, where):
        return re.sub('( and | or )',
                      lambda m: m.group(1).upper(),
                      where['sql'],
                      re.I)

    def _compile_groups(self, query, groups):
        if not groups:
            return ''

        return 'GROUP BY %s' % self.columnize(groups)

    def _compile_havings(self, query, havings):
        if not havings:
            return ''

        sql = ' '.join(map(self._compile_having, havings))

        return 'HAVING %s' % re.sub('and |or ', '', sql, 1, re.I)

    def _compile_having(self, having):
        # If the having clause is "raw", we can just return the clause straight away
        # without doing any more processing on it. Otherwise, we will compile the
        # clause into SQL based on the components that make it up from builder.
        if having['type'] == 'raw':
            return '%s %s' % (having['boolean'].upper(), having['sql'])

        return self._compile_basic_having(having)

    def _compile_basic_having(self, having):
        column = self.wrap(having['column'])

        parameter = self.parameter(having['value'])

        return '%s %s %s %s' % (having['boolean'].upper(), column,
                                having['operator'], parameter)

    def _compile_orders(self, query, orders):
        if not orders:
            return ''

        compiled = []
        for order in orders:
            if order.get('sql'):
                compiled.append(re.sub('( desc| asc)( |$)',
                                       lambda m: '%s%s' % (m.group(1).upper(), m.group(2)),
                                       order['sql'],
                                       re.I))
            else:
                compiled.append('%s %s' % (self.wrap(order['column']),
                                           order['direction'].upper()))

        return 'ORDER BY %s' % ', '.join(compiled)

    def _compile_limit(self, query, limit):
        return 'LIMIT %s' % int(limit)

    def _compile_offset(self, query, offset):
        return 'OFFSET %s' % int(offset)

    def _compile_unions(self, query, _=None):
        sql = ''

        for union in query.unions:
            sql += self._compile_union(union)

        if query.union_orders:
            sql += ' %s' % self._compile_orders(query, query.union_orders)

        if query.union_limit:
            sql += ' %s' % self._compile_limit(query, query.union_limit)

        if query.union_offset:
            sql += ' %s' % self._compile_offset(query, query.union_offset)

        return sql.lstrip()

    def _compile_union(self, union):
        if union['all']:
            joiner = ' UNION ALL '
        else:
            joiner = ' UNION '

        return '%s%s' % (joiner, union['query'].to_sql())

    def compile_insert(self, query, values):
        """
        Compile an insert SQL statement

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param values: The values to insert
        :type values: dict or list

        :return: The compiled statement
        :rtype: str
        """
        # Essentially we will force every insert to be treated as a batch insert which
        # simply makes creating the SQL easier for us since we can utilize the same
        # basic routine regardless of an amount of records given to us to insert.
        table = self.wrap_table(query.from__)

        if not isinstance(values, list):
            values = [values]

        columns = self.columnize(values[0].keys())

        # We need to build a list of parameter place-holders of values that are bound
        # to the query. Each insert should have the exact same amount of parameter
        # bindings so we can just go off the first list of values in this array.
        parameters = self.parameterize(values[0].values())

        value = ['(%s)' % parameters] * len(values)

        parameters = ', '.join(value)

        return 'INSERT INTO %s (%s) VALUES %s' % (table, columns, parameters)

    def compile_insert_get_id(self, query, values, sequence):
        return self.compile_insert(query, values)

    def compile_update(self, query, values):
        table = self.wrap_table(query.from__)

        # Each one of the columns in the update statements needs to be wrapped in the
        # keyword identifiers, also a place-holder needs to be created for each of
        # the values in the list of bindings so we can make the sets statements.
        columns = []

        for key, value in values.items():
            columns.append('%s = %s' % (self.wrap(key), self.parameter(value)))

        columns = ', '.join(columns)

        # If the query has any "join" clauses, we will setup the joins on the builder
        # and compile them so we can attach them to this update, as update queries
        # can get join statements to attach to other tables when they're needed.
        if query.joins:
            joins = ' %s' % self._compile_joins(query, query.joins)
        else:
            joins = ''

        # Of course, update queries may also be constrained by where clauses so we'll
        # need to compile the where clauses and attach it to the query so only the
        # intended records are updated by the SQL statements we generate to run.
        where = self._compile_wheres(query)

        return ('UPDATE %s%s SET %s %s' % (table, joins, columns, where)).strip()

    def compile_delete(self, query):
        table = self.wrap_table(query.from__)

        if isinstance(query.wheres, list):
            where = self._compile_wheres(query)
        else:
            where = ''

        return ('DELETE FROM %s %s' % (table, where)).strip()

    def compile_truncate(self, query):
        return {
            'TRUNCATE %s' % self.wrap_table(query.from__): []
        }

    def _compile_lock(self, query, value):
        if isinstance(value, basestring):
            return value
        else:
            return ''

    def _concatenate(self, segments):
        parts = []

        for component in self._select_components:
            value = segments.get(component)
            if value:
                parts.append(value)

        return ' '.join(parts)

    def _remove_leading_boolean(self, value):
        return re.sub('and | or ', '', value, 1, re.I)


