# -*- coding: utf-8 -*-


class DBALException(Exception):

    pass


class InvalidPlatformSpecified(DBALException):
    def __init__(self, index_name, table_name):
        message = 'Invalid "platform" option specified, need to give an instance of dbal.platforms.Platform'

        super(InvalidPlatformSpecified, self).__init__(message)


class SchemaException(DBALException):

    pass


class IndexDoesNotExist(SchemaException):
    def __init__(self, index_name, table_name):
        message = 'Index "%s" does not exist on table "%s".' % (index_name, table_name)

        super(IndexDoesNotExist, self).__init__(message)


class IndexAlreadyExists(SchemaException):
    def __init__(self, index_name, table_name):
        message = 'An index with name "%s" already exists on table "%s".' % (
            index_name,
            table_name,
        )

        super(IndexAlreadyExists, self).__init__(message)


class IndexNameInvalid(SchemaException):
    def __init__(self, index_name):
        message = 'Invalid index name "%s" given, has to be [a-zA-Z0-9_]' % index_name

        super(IndexNameInvalid, self).__init__(message)


class ColumnDoesNotExist(SchemaException):
    def __init__(self, column, table_name):
        message = 'Column "%s" does not exist on table "%s".' % (column, table_name)

        super(ColumnDoesNotExist, self).__init__(message)


class ColumnAlreadyExists(SchemaException):
    def __init__(self, column, table_name):
        message = 'An column with name "%s" already exists on table "%s".' % (
            column,
            table_name,
        )

        super(ColumnAlreadyExists, self).__init__(message)


class ForeignKeyDoesNotExist(SchemaException):
    def __init__(self, constraint, table_name):
        message = 'Foreign key "%s" does not exist on table "%s".' % (
            constraint,
            table_name,
        )

        super(ForeignKeyDoesNotExist, self).__init__(message)
