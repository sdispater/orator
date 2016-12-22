# -*- coding: utf-8 -*-

from .processor import QueryProcessor


class MySQLQueryProcessor(QueryProcessor):

    def process_insert_get_id(self, query, sql, values, sequence=None):
        """
        Process an "insert get ID" query.

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param sql: The sql query to execute
        :type sql: str

        :param values: The value bindings
        :type values: list

        :param sequence: The ids sequence
        :type sequence: str

        :return: The inserted row id
        :rtype: int
        """
        if not query.get_connection().transaction_level():
            with query.get_connection().transaction():
                query.get_connection().insert(sql, values)

                cursor = query.get_connection().get_cursor()
                if hasattr(cursor, 'lastrowid'):
                    id = cursor.lastrowid
                else:
                    id = query.get_connection().statement('SELECT LAST_INSERT_ID()')
        else:
            query.get_connection().insert(sql, values)

            cursor = query.get_connection().get_cursor()
            if hasattr(cursor, 'lastrowid'):
                id = cursor.lastrowid
            else:
                id = query.get_connection().statement('SELECT LAST_INSERT_ID()')

        if isinstance(id, int):
            return id

        if str(id).isdigit():
            return int(id)

        return id

    def process_column_listing(self, results):
        """
        Process the results of a column listing query

        :param results: The query results
        :type results: dict

        :return: The processed results
        :return: list
        """
        return list(map(lambda x: x['column_name'], results))
