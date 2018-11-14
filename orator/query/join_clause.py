# -*- coding: utf-8 -*-

from .expression import QueryExpression


class JoinClause(object):
    def __init__(self, table, type="inner"):
        self.type = type
        self.table = table

        self.clauses = []
        self.bindings = []

    def on(self, first, operator, second, boolean="and", where=False):
        self.clauses.append(
            {
                "first": first,
                "operator": operator,
                "second": second,
                "boolean": boolean,
                "where": where,
            }
        )

        if where:
            self.bindings.append(second)

        return self

    def or_on(self, first, operator, second):
        return self.on(first, operator, second, "or")

    def where(self, first, operator, second, boolean="and"):
        return self.on(first, operator, second, boolean, True)

    def or_where(self, first, operator, second):
        return self.where(first, operator, second, "or")

    def where_null(self, column, boolean="and"):
        return self.on(column, "IS", QueryExpression("NULL"), boolean, False)

    def or_where_null(self, column):
        return self.where_null(column, "or")

    def where_not_null(self, column, boolean="and"):
        return self.on(column, "IS", QueryExpression("NOT NULL"), boolean, False)

    def or_where_not_null(self, column):
        return self.where_not_null(column, "or")
