# -*- coding: utf-8 -*-


class QueryProcessor(object):
    def process_select(self, query, results):
        """
        Process the results of a "select" query

        :param query: A QueryBuilder instance
        :type query: QueryBuilder

        :param results: The query results
        :type results: dict

        :return: The processed results
        :rtype: dict
        """
        return results

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
        query.get_connection().insert(sql, values)

        id = query.get_connection().get_cursor().lastrowid

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
        :return: dict
        """
        return results
