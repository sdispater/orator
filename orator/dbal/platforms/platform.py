# -*- coding: utf-8 -*-


class Platform(object):

    _keywords = None

    INTERNAL_TYPE_MAPPING = {}

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

    def get_current_date_sql(self):
        return 'CURRENT_DATE'

    def get_current_time_sql(self):
        return 'CURRENT_TIME'

    def get_current_timestamp_sql(self):
        return 'CURRENT_TIMESTAMP'

    def get_sql_type_declaration(self, column):
        internal_type = column['type']

        return getattr(self, 'get_%s_type_sql_declaration' % internal_type)(column)

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

    def get_string_type_sql_declaration(self, column):
        if 'length' not in column:
            column['length'] = self.get_varchar_default_length()

        fixed = column.get('fixed', False)

        if column['length'] > self.get_varchar_max_length():
            return self.get_text_type_sql_declaration(column)

        return self.get_varchar_type_declaration_sql_snippet(column['length'], fixed)

    def get_binary_type_sql_declaration(self, column):
        if 'length' not in column:
            column['length'] = self.get_binary_default_length()

        fixed = column.get('fixed', False)

        if column['length'] > self.get_binary_max_length():
            return self.get_blob_type_sql_declaration(column)

        return self.get_binary_type_declaration_sql_snippet(column['length'], fixed)

    def get_varchar_type_declaration_sql_snippet(self, length, fixed):
        raise NotImplementedError('VARCHARS not supported by Platform')

    def get_binary_type_declaration_sql_snippet(self, length, fixed):
        raise NotImplementedError('BINARY/VARBINARY not supported by Platform')

    def get_decimal_type_sql_declaration(self, column):
        if 'precision' not in column or not column['precision']:
            column['precision'] = 10

        if 'scale' not in column or not column['scale']:
            column['precision'] = 0

        return 'NUMERIC(%s, %s)' % (column['precision'], column['scale'])

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
