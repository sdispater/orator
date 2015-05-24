# -*- coding: utf-8 -*-

from .table_diff import TableDiff
from .column_diff import ColumnDiff


class Comparator(object):
    """
    Compares two Schemas and return an instance of SchemaDiff.
    """

    def diff_table(self, table1, table2):
        """
        Returns the difference between the tables table1 and table2.

        :type table1: Table
        :type table2: Table

        :rtype: TableDiff
        """
        changes = 0
        table_differences = TableDiff(table1.get_name())
        table_differences.from_table = table1

        table1_columns = table1.get_columns()
        table2_columns = table2.get_columns()

        # See if all the fields in table1 exist in table2
        for column_name, column in table2_columns.items():
            if not table1.has_column(column_name):
                table_differences.added_columns[column_name] = column
                changes += 1

        # See if there are any removed fields in table2
        for column_name, column in table1_columns.items():
            if not table2.has_column(column_name):
                table_differences.removed_columns[column_name] = column
                changes += 1
                continue

            # See if column has changed properties in table2
            changed_properties = self.diff_column(column, table2.get_column(column_name))

            if changed_properties:
                column_diff = ColumnDiff(column.get_name(),
                                         table2.get_column(column_name),
                                         changed_properties)
                column_diff.from_column = column
                table_differences.changed_columns[column.get_name()] = column_diff
                changes += 1

        self.detect_column_renamings(table_differences)

        # table1_indexes = table1.get_indexes()
        # table2_indexes = table2.get_indexes()
        #
        # # See if all the fields in table1 exist in table2
        # for index_name, index in table2_indexes.items():
        #     if (index.is_primary() and table1.has_primary_key()) or table1.has_index(index_name):
        #         continue
        #
        #     table_differences.added_indexes[index_name] = index
        #     changes += 1
        #
        # # See if there are any removed fields in table2
        # for index_name, index in table1_indexes.items():
        #     if (index.is_primary() and not table2.has_primary_key())\
        #             or (not index.is_primary() and not table2.has_index(index_name)):
        #         table_differences.removed_indexes[index_name] = index
        #         changes += 1
        #         continue
        #
        #     if index.is_primary():
        #         table2_index = table2.get_primary_key()
        #     else:
        #         table2_index = table2.get_index(index_name)
        #
        #     if self.diff_index(index, table2_index):
        #         table_differences.changed_indexes[index_name] = index
        #         changes += 1
        #
        # self.detect_index_renamings(table_differences)
        #
        # from_fkeys = table1.get_foreign_keys()
        # to_fkeys = table2.get_foreign_keys()
        #
        # for key1, constraint1 in from_fkeys.items():
        #     for key2, constraint2 in to_fkeys.items():
        #         if self.diff_foreign_key(constraint1, constraint2) is False:
        #             del from_fkeys[key1]
        #             del to_fkeys[key2]
        #         else:
        #             if constraint1.get_name().lower() == constraint2.get_name().lower():
        #                 table_differences.changed_foreign_keys.append(constraint2)
        #                 changes += 1
        #                 del from_fkeys[key1]
        #                 del to_fkeys[key2]
        #
        # for constraint1 in from_fkeys.values():
        #     table_differences.removed_foreign_keys.append(constraint1)
        #     changes += 1
        #
        # for constraint2 in to_fkeys.values():
        #     table_differences.added_foreign_keys.append(constraint2)
        #     changes += 1

        if changes:
            return table_differences

        return False

    def detect_column_renamings(self, table_differences):
        """
        Try to find columns that only changed their names.

        :type table_differences: TableDiff
        """
        rename_candidates = {}

        for added_column_name, added_column in table_differences.added_columns.items():
            for removed_column in table_differences.removed_columns.values():
                if len(self.diff_column(added_column, removed_column)) == 0:
                    if added_column.get_name() not in rename_candidates:
                        rename_candidates[added_column.get_name()] = []

                    rename_candidates[added_column.get_name()] = (removed_column, added_column, added_column_name)

        for candidate_columns in rename_candidates.values():
            if len(candidate_columns) == 1:
                removed_column, added_column, _ = candidate_columns[0]
                removed_column_name = removed_column.get_name().lower()
                added_column_name = added_column.get_name().lower()

                if removed_column_name not in table_differences.renamed_columns:
                    table_differences.renamed_columns[removed_column_name] = added_column
                    del table_differences.added_columns[added_column_name]
                    del table_differences.removed_columns[removed_column_name]

    def diff_column(self, column1, column2):
        """
        Returns the difference between column1 and column2

        :type column1: orator.dbal.column.Column
        :type column2: orator.dbal.column.Column

        :rtype: list
        """
        properties1 = column1.to_dict()
        properties2 = column2.to_dict()

        changed_properties = []

        for prop in ['type', 'notnull', 'unsigned', 'autoincrement']:
            if properties1[prop] != properties2[prop]:
                changed_properties.append(prop)

        if properties1['default'] != properties2['default']\
                or (properties1['default'] is None and properties2['default'] is not None)\
                or (properties2['default'] is None and properties1['default'] is not None):
            changed_properties.append('default')

        if properties1['type'] == 'string' and properties1['type'] != 'guid'\
                or properties1['type'] in ['binary', 'blob']:
            length1 = properties1['length'] or 255
            length2 = properties2['length'] or 255

            if length1 != length2:
                changed_properties.append('length')

            if properties1['fixed'] != properties2['fixed']:
                changed_properties.append('fixed')
        elif properties1['type'] in ['decimal', 'float', 'double precision']:
            precision1 = properties1['precision'] or 10
            precision2 = properties2['precision'] or 10

            if precision1 != precision2:
                changed_properties.append('precision')

            if properties1['scale'] != properties2['scale']:
                changed_properties.append('scale')

        return list(set(changed_properties))


