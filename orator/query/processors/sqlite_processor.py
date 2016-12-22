# -*- coding: utf-8 -*-

from .processor import QueryProcessor


class SQLiteQueryProcessor(QueryProcessor):

    def process_column_listing(self, results):
        """
        Process the results of a column listing query

        :param results: The query results
        :type results: dict

        :return: The processed results
        :return: list
        """
        return list(map(lambda x: x['name'], results))
