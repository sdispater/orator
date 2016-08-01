# -*- coding: utf-8 -*-

from collections import OrderedDict
from ..index import Index
from ..table import Table
from ..identifier import Identifier
from ..exceptions import DBALException
from ...utils import basestring


class Platform(object):

    _keywords = None

    CREATE_INDEXES = 1

    CREATE_FOREIGNKEYS = 2

    INTERNAL_TYPE_MAPPING = {}

    def __init__(self, version=None):
        self._version = None

    def get_default_value_declaration_sql(self, field):
        default = ''

        if not field.get('notnull'):
            default = ' DEFAULT NULL'

        if 'default' in field and field['default'] is not None:
            default = ' DEFAULT \'%s\'' % field['default']

            if 'type' in field:
                type = field['type']

                if type in ['integer', 'bigint', 'smallint']:
                    default = ' DEFAULT %s' % field['default']
                elif type in ['datetime', 'datetimetz'] \
                        and field['default'] in [self.get_current_timestamp_sql(), 'NOW', 'now']:
                    default = ' DEFAULT %s' % self.get_current_timestamp_sql()
                elif type in ['time'] \
                        and field['default'] in [self.get_current_time_sql(), 'NOW', 'now']:
                    default = ' DEFAULT %s' % self.get_current_time_sql()
                elif type in ['date'] \
                        and field['default'] in [self.get_current_date_sql(), 'NOW', 'now']:
                    default = ' DEFAULT %s' % self.get_current_date_sql()
                elif type in ['boolean']:
                    default = ' DEFAULT \'%s\'' % self.convert_booleans(field['default'])

        return default

    def convert_booleans(self, item):
        if isinstance(item, list):
            for i, value in enumerate(item):
                if isinstance(value, bool):
                    item[i] = int(value)
        elif isinstance(item, bool):
            item = int(item)

        return item

    def get_check_declaration_sql(self, definition):
        """
        Obtains DBMS specific SQL code portion needed to set a CHECK constraint
        declaration to be used in statements like CREATE TABLE.

        :param definition: The check definition
        :type definition: dict

        :return: DBMS specific SQL code portion needed to set a CHECK constraint.
        :rtype: str
        """
        constraints = []
        for field, def_ in definition.items():
            if isinstance(def_, basestring):
                constraints.append('CHECK (%s)' % def_)
            else:
                if 'min' in def_:
                    constraints.append('CHECK (%s >= %s)' % (field, def_['min']))

                if 'max' in def_:
                    constraints.append('CHECK (%s <= %s)' % (field, def_['max']))

        return ', '.join(constraints)

    def get_unique_constraint_declaration_sql(self, name, index):
        """
        Obtains DBMS specific SQL code portion needed to set a unique
        constraint declaration to be used in statements like CREATE TABLE.

        :param name: The name of the unique constraint.
        :type name: str

        :param index: The index definition
        :type index: Index

        :return: DBMS specific SQL code portion needed to set a constraint.
        :rtype: str
        """
        columns = index.get_quoted_columns(self)
        name = Identifier(name)

        if not columns:
            raise DBALException('Incomplete definition. "columns" required.')

        return 'CONSTRAINT %s UNIQUE (%s)%s'\
               % (name.get_quoted_name(self),
                  self.get_index_field_declaration_list_sql(columns),
                  self.get_partial_index_sql(index))

    def get_index_declaration_sql(self, name, index):
        """
        Obtains DBMS specific SQL code portion needed to set an index
        declaration to be used in statements like CREATE TABLE.

        :param name: The name of the index.
        :type name: str

        :param index: The index definition
        :type index: Index

        :return: DBMS specific SQL code portion needed to set an index.
        :rtype: str
        """
        columns = index.get_quoted_columns(self)
        name = Identifier(name)

        if not columns:
            raise DBALException('Incomplete definition. "columns" required.')

        return '%sINDEX %s (%s)%s'\
               % (self.get_create_index_sql_flags(index),
                  name.get_quoted_name(self),
                  self.get_index_field_declaration_list_sql(columns),
                  self.get_partial_index_sql(index))

    def get_foreign_key_declaration_sql(self, foreign_key):
        """
        Obtain DBMS specific SQL code portion needed to set the FOREIGN KEY constraint
        of a field declaration to be used in statements like CREATE TABLE.

        :param foreign_key: The foreign key
        :type foreign_key: ForeignKeyConstraint

        :rtype: str
        """
        sql = self.get_foreign_key_base_declaration_sql(foreign_key)
        sql += self.get_advanced_foreign_key_options_sql(foreign_key)

        return sql

    def get_advanced_foreign_key_options_sql(self, foreign_key):
        """
        Returns the FOREIGN KEY query section dealing with non-standard options
        as MATCH, INITIALLY DEFERRED, ON UPDATE, ...

        :param foreign_key: The foreign key
        :type foreign_key: ForeignKeyConstraint

        :rtype: str
        """
        query = ''
        if self.supports_foreign_key_on_update() and foreign_key.has_option('on_update'):
            query += ' ON UPDATE %s' % self.get_foreign_key_referential_action_sql(foreign_key.get_option('on_update'))

        if foreign_key.has_option('on_delete'):
            query += ' ON DELETE %s' % self.get_foreign_key_referential_action_sql(foreign_key.get_option('on_delete'))

        return query

    def get_foreign_key_referential_action_sql(self, action):
        """
        Returns the given referential action in uppercase if valid, otherwise throws an exception.

        :param action: The action
        :type action: str

        :rtype: str
        """
        action = action.upper()
        if action not in ['CASCADE', 'SET NULL', 'NO ACTION', 'RESTRICT', 'SET DEFAULT']:
            raise DBALException('Invalid foreign key action: %s' % action)

        return action

    def get_foreign_key_base_declaration_sql(self, foreign_key):
        """
        Obtains DBMS specific SQL code portion needed to set the FOREIGN KEY constraint
        of a field declaration to be used in statements like CREATE TABLE.

        :param foreign_key: The foreign key
        :type foreign_key: ForeignKeyConstraint

        :rtype: str
        """
        sql = ''
        if foreign_key.get_name():
            sql += 'CONSTRAINT %s ' % foreign_key.get_quoted_name(self)

        sql += 'FOREIGN KEY ('

        if not foreign_key.get_local_columns():
            raise DBALException('Incomplete definition. "local" required.')

        if not foreign_key.get_foreign_columns():
            raise DBALException('Incomplete definition. "foreign" required.')

        if not foreign_key.get_foreign_table_name():
            raise DBALException('Incomplete definition. "foreign_table" required.')

        sql += '%s) REFERENCES %s (%s)'\
               % (', '.join(foreign_key.get_quoted_local_columns(self)),
                  foreign_key.get_quoted_foreign_table_name(self),
                  ', '.join(foreign_key.get_quoted_foreign_columns(self)))

        return sql

    def get_current_date_sql(self):
        return 'CURRENT_DATE'

    def get_current_time_sql(self):
        return 'CURRENT_TIME'

    def get_current_timestamp_sql(self):
        return 'CURRENT_TIMESTAMP'

    def get_sql_type_declaration(self, column):
        internal_type = column['type']

        return getattr(self, 'get_%s_type_declaration_sql' % internal_type)(column)

    def get_column_declaration_list_sql(self, fields):
        """
        Gets declaration of a number of fields in bulk.
        """
        query_fields = []

        for name, field in fields.items():
            query_fields.append(self.get_column_declaration_sql(name, field))

        return ', '.join(query_fields)

    def get_column_declaration_sql(self, name, field):
        if 'column_definition' in field:
            column_def = self.get_custom_type_declaration_sql(field)
        else:
            default = self.get_default_value_declaration_sql(field)

            charset = field.get('charset', '')
            if charset:
                charset = ' ' + self.get_column_charset_declaration_sql(charset)

            collation = field.get('collation', '')
            if charset:
                charset = ' ' + self.get_column_collation_declaration_sql(charset)

            notnull = field.get('notnull', '')
            if notnull:
                notnull = ' NOT NULL'
            else:
                notnull = ''

            unique = field.get('unique', '')
            if unique:
                unique = ' ' + self.get_unique_field_declaration_sql()
            else:
                unique = ''

            check = field.get('check', '')

            type_decl = self.get_sql_type_declaration(field)
            column_def = type_decl + charset + default + notnull + unique + check + collation

        return name + ' ' + column_def

    def get_custom_type_declaration_sql(self, column_def):
        return column_def['column_definition']

    def get_column_charset_declaration_sql(self, charset):
        return ''

    def get_column_collation_declaration_sql(self, collation):
        if self.supports_column_collation():
            return 'COLLATE %s' % collation

        return ''

    def supports_column_collation(self):
        return False

    def get_unique_field_declaration_sql(self):
        return 'UNIQUE'

    def get_string_type_declaration_sql(self, column):
        if 'length' not in column:
            column['length'] = self.get_varchar_default_length()

        fixed = column.get('fixed', False)

        if column['length'] > self.get_varchar_max_length():
            return self.get_clob_type_declaration_sql(column)

        return self.get_varchar_type_declaration_sql_snippet(column['length'], fixed)

    def get_binary_type_declaration_sql(self, column):
        if 'length' not in column:
            column['length'] = self.get_binary_default_length()

        fixed = column.get('fixed', False)

        if column['length'] > self.get_binary_max_length():
            return self.get_blob_type_declaration_sql(column)

        return self.get_binary_type_declaration_sql_snippet(column['length'], fixed)

    def get_varchar_type_declaration_sql_snippet(self, length, fixed):
        raise NotImplementedError('VARCHARS not supported by Platform')

    def get_binary_type_declaration_sql_snippet(self, length, fixed):
        raise NotImplementedError('BINARY/VARBINARY not supported by Platform')

    def get_decimal_type_declaration_sql(self, column):
        if 'precision' not in column or not column['precision']:
            column['precision'] = 10

        if 'scale' not in column or not column['scale']:
            column['precision'] = 0

        return 'NUMERIC(%s, %s)' % (column['precision'], column['scale'])

    def get_json_type_declaration_sql(self, column):
        return self.get_clob_type_declaration_sql(column)

    def get_clob_type_declaration_sql(self, column):
        raise NotImplementedError()

    def get_text_type_declaration_sql(self, column):
        return self.get_clob_type_declaration_sql(column)

    def get_blob_type_declaration_sql(self, column):
        raise NotImplementedError()

    def get_varchar_default_length(self):
        return 255

    def get_varchar_max_length(self):
        return 4000

    def get_binary_default_length(self):
        return 255

    def get_binary_max_length(self):
        return 4000

    def get_column_options(self):
        return []

    def get_type_mapping(self, db_type):
        return self.INTERNAL_TYPE_MAPPING[db_type]

    def get_reserved_keywords_list(self):
        if self._keywords:
            return self._keywords

        klass = self._get_reserved_keywords_class()
        keywords = klass()

        self._keywords = keywords

        return keywords

    def _get_reserved_keywords_class(self):
        raise NotImplementedError

    def get_index_field_declaration_list_sql(self, fields):
        """
        Obtains DBMS specific SQL code portion needed to set an index
        declaration to be used in statements like CREATE TABLE.

        :param fields: The columns
        :type fields: list

        :rtype: sql
        """
        ret = []

        for field in fields:
            ret.append(field)

        return ', '.join(ret)

    def get_create_index_sql(self, index, table):
        """
        Returns the SQL to create an index on a table on this platform.

        :param index: The index
        :type index: Index

        :param table: The table
        :type table: Table or str

        :rtype: str
        """
        if isinstance(table, Table):
            table = table.get_quoted_name(self)

        name = index.get_quoted_name(self)
        columns = index.get_quoted_columns(self)

        if not columns:
            raise DBALException('Incomplete definition. "columns" required.')

        if index.is_primary():
            return self.get_create_primary_key_sql(index, table)

        query = 'CREATE %sINDEX %s ON %s' % (self.get_create_index_sql_flags(index), name, table)
        query += ' (%s)%s' % (self.get_index_field_declaration_list_sql(columns),
                              self.get_partial_index_sql(index))

        return query

    def get_partial_index_sql(self, index):
        """
        Adds condition for partial index.

        :param index: The index
        :type index: Index

        :rtype: str
        """
        if self.supports_partial_indexes() and index.has_option('where'):
            return ' WHERE %s' % index.get_option('where')

        return ''

    def get_create_index_sql_flags(self, index):
        """
        Adds additional flags for index generation.

        :param index: The index
        :type index: Index

        :rtype: str
        """
        if index.is_unique():
            return 'UNIQUE '

        return ''

    def get_create_primary_key_sql(self, index, table):
        """
        Returns the SQL to create an unnamed primary key constraint.

        :param index: The index
        :type index: Index

        :param table: The table
        :type table: Table or str

        :rtype: str
        """
        return 'ALTER TABLE %s ADD PRIMARY KEY (%s)'\
               % (table,
                  self.get_index_field_declaration_list_sql(index.get_quoted_columns(self)))

    def get_create_foreign_key_sql(self, foreign_key, table):
        """
        Returns the SQL to create a new foreign key.

        :rtype: sql
        """
        if isinstance(table, Table):
            table = table.get_quoted_name(self)

        query = 'ALTER TABLE %s ADD %s' % (table, self.get_foreign_key_declaration_sql(foreign_key))

        return query

    def get_drop_table_sql(self, table):
        """
        Returns the SQL snippet to drop an existing table.

        :param table: The table
        :type table: Table or str

        :rtype: str
        """
        if isinstance(table, Table):
            table = table.get_quoted_name(self)

        return 'DROP TABLE %s' % table

    def get_drop_index_sql(self, index, table=None):
        """
        Returns the SQL to drop an index from a table.

        :param index: The index
        :type index: Index or str

        :param table: The table
        :type table: Table or str or None

        :rtype: str
        """
        if isinstance(index, Index):
            index = index.get_quoted_name(self)

        return 'DROP INDEX %s' % index

    def get_create_table_sql(self, table, create_flags=CREATE_INDEXES):
        """
        Returns the SQL statement(s) to create a table
        with the specified name, columns and constraints
        on this platform.

        :param table: The table
        :type table: Table

        :type create_flags: int

        :rtype: str
        """
        table_name = table.get_quoted_name(self)
        options = dict((k, v) for k, v in table.get_options().items())

        options['unique_constraints'] = OrderedDict()
        options['indexes'] = OrderedDict()
        options['primary'] = []

        if create_flags & self.CREATE_INDEXES > 0:
            for index in table.get_indexes().values():
                if index.is_primary():
                    options['primary'] = index.get_quoted_columns(self)
                    options['primary_index'] = index
                else:
                    options['indexes'][index.get_quoted_name(self)] = index

        columns = OrderedDict()

        for column in table.get_columns().values():
            column_data = column.to_dict()
            column_data['name'] = column.get_quoted_name(self)
            if column.has_platform_option('version'):
                column_data['version'] = column.get_platform_option('version')
            else:
                column_data['version'] = False

            # column_data['comment'] = self.get_column_comment(column)

            if column_data['type'] == 'string' and  column_data['length'] is None:
                column_data['length'] = 255

            if column.get_name() in options['primary']:
                column_data['primary'] = True

            columns[column_data['name']] = column_data

        if create_flags & self.CREATE_FOREIGNKEYS > 0:
            options['foreign_keys'] = []
            for fk in table.get_foreign_keys().values():
                options['foreign_keys'].append(fk)

        sql = self._get_create_table_sql(table_name, columns, options)

        # Comments?

        return sql

    def _get_create_table_sql(self, table_name, columns, options=None):
        """
        Returns the SQL used to create a table.

        :param table_name: The name of the table to create
        :type table_name: str

        :param columns: The table columns
        :type columns: dict

        :param options: The options
        :type options: dict

        :rtype: str
        """
        options = options or {}

        column_list_sql = self.get_column_declaration_list_sql(columns)

        if options.get('unique_constraints'):
            for name, definition in options['unique_constraints'].items():
                column_list_sql += ', %s' % self.get_unique_constraint_declaration_sql(name, definition)

        if options.get('primary'):
            column_list_sql += ', PRIMARY KEY(%s)' % ', '.join(options['primary'])

        if options.get('indexes'):
            for index, definition in options['indexes']:
                column_list_sql += ', %s' % self.get_index_declaration_sql(index, definition)

        query = 'CREATE TABLE %s (%s' % (table_name, column_list_sql)

        check = self.get_check_declaration_sql(columns)
        if check:
            query += ', %s' % check

        query += ')'

        sql = [query]

        if options.get('foreign_keys'):
            for definition in options['foreign_keys']:
                sql.append(self.get_create_foreign_key_sql(definition, table_name))

        return sql


    def quote_identifier(self, string):
        """
        Quotes a string so that it can be safely used as a table or column name,
        even if it is a reserved word of the platform. This also detects identifier
        chains separated by dot and quotes them independently.

        :param string: The identifier name to be quoted.
        :type string: str

        :return: The quoted identifier string.
        :rtype: str
        """
        if '.' in string:
            parts = list(map(self.quote_single_identifier, string.split('.')))

            return '.'.join(parts)

        return self.quote_single_identifier(string)

    def quote_single_identifier(self, string):
        """
        Quotes a single identifier (no dot chain separation).

        :param string: The identifier name to be quoted.
        :type string: str

        :return: The quoted identifier string.
        :rtype: str
        """
        c = self.get_identifier_quote_character()

        return '%s%s%s' % (c, string.replace(c, c+c), c)

    def get_identifier_quote_character(self):
        return '"'

    def supports_indexes(self):
        return True

    def supports_partial_indexes(self):
        return False

    def supports_alter_table(self):
        return True

    def supports_transactions(self):
        return True

    def supports_primary_constraints(self):
        return True

    def supports_foreign_key_constraints(self):
        return True

    def supports_foreign_key_on_update(self):
        return self.supports_foreign_key_constraints()

    def has_native_json_type(self):
        return False
