# -*- coding: utf-8 -*-


class ConnectionInterface(object):
    def table(self, table):
        """
        Begin a fluent query against a database table

        :param table: The database table
        :type table: str

        :return: A QueryBuilder instance
        :rtype: QueryBuilder
        """
        raise NotImplementedError()

    def query(self):
        """
        Begin a fluent query

        :return: A QueryBuilder instance
        :rtype: QueryBuilder
        """
        raise NotImplementedError()

    def raw(self, value):
        """
        Get a new raw query expression

        :param value: The value
        :type value: mixed

        :return: A QueryExpression instance
        :rtype: QueryExpression
        """
        raise NotImplementedError()

    def select_one(self, query, bindings=None):
        """
        Run a select statement and return a single result

        :param query: The select statement
        :type query: str
        :param bindings: The query bindings
        :type bindings: dict

        :return: mixed
        """
        raise NotImplementedError()

    def select(self, query, bindings=None):
        """
        Run a select statement against the database

        :param query: The select statement
        :type query: str
        :param bindings: The query bindings
        :type bindings: dict

        :return: mixed
        """
        raise NotImplementedError()

    def insert(self, query, bindings=None):
        """
        Run an insert statement against the database

        :param query: The insert statement
        :type query: str
        :param bindings: The query bindings
        :type bindings: dict

        :return: mixed
        """
        raise NotImplementedError()

    def update(self, query, bindings=None):
        """
        Run an update statement against the database

        :param query: The update statement
        :type query: str
        :param bindings: The query bindings
        :type bindings: dict

        :return: mixed
        """
        raise NotImplementedError()

    def delete(self, query, bindings=None):
        """
        Run a delete statement against the database

        :param query: The select statement
        :type query: str
        :param bindings: The query bindings
        :type bindings: dict

        :return: mixed
        """
        raise NotImplementedError()

    def statement(self, query, bindings=None):
        """
        Run an SQL statement and return the boolean result

        :param query: The select statement
        :type query: str
        :param bindings: The query bindings
        :type bindings: dict

        :return: Boolean result
        :rtype: bool
        """
        raise NotImplementedError()

    def affecting_statement(self, query, bindings=None):
        """
        Run an SQL statement and return the number of affected rows

        :param query: The select statement
        :type query: str
        :param bindings: The query bindings
        :type bindings: dict

        :return: Number of affected rows
        :rtype: int
        """
        raise NotImplementedError()

    def unprepared(self, query):
        """
        Run a raw, unprepared query against the dbapi connection

        :param query: The raw query
        :type query: str

        :return: Boolean result
        :rtype: bool
        """
        raise NotImplementedError()

    def prepare_bindings(self, bindings):
        """
        Prepare the query bindings for execution

        :param bindings: The query bindings
        :type bindings: dict

        :return: The prepared bindings
        :rtype: dict
        """
        raise NotImplementedError()

    def transaction(self):
        raise NotImplementedError()

    def begin_transaction(self):
        raise NotImplementedError()

    def commit(self):
        raise NotImplementedError()

    def rollback(self):
        raise NotImplementedError()

    def transaction_level(self):
        raise NotImplementedError()

    def pretend(self):
        raise NotImplementedError()
