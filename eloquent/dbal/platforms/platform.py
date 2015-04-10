# -*- coding: utf-8 -*-


class Platform(object):

    INTERNAL_TYPE_MAPPING = {}

    def get_default_value_declaration_sql(self, field):
        default = ''

        if not field.get('notnull'):
            default = ' DEFAULT NULL'

        if 'default' in field:
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

    def get_column_options(self):
        return []

    def get_type_mapping(self, db_type):
        return self.INTERNAL_TYPE_MAPPING[db_type]
