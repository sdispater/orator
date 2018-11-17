# -*- coding: utf-8 -*-

from .processor import QueryProcessor


class PostgresQueryProcessor(QueryProcessor):
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
        result = query.get_connection().select_from_write_connection(sql, values)

        id = result[0][0]

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
        return list(map(lambda x: x["column_name"], results))
