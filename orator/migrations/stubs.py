# -*- coding: utf-8 -*-

BLANK_STUB = """from orator.migrations import Migration


class DummyClass(Migration):

    def up(self):
        \"\"\"
        Run the migrations.
        \"\"\"
        pass

    def down(self):
        \"\"\"
        Revert the migrations.
        \"\"\"
        pass
"""

CREATE_STUB = """from orator.migrations import Migration


class DummyClass(Migration):

    def up(self):
        \"\"\"
        Run the migrations.
        \"\"\"
        with self.schema.create('dummy_table') as table:
            table.increments('id')
            table.timestamps()

    def down(self):
        \"\"\"
        Revert the migrations.
        \"\"\"
        self.schema.drop('dummy_table')
"""

UPDATE_STUB = """from orator.migrations import Migration


class DummyClass(Migration):

    def up(self):
        \"\"\"
        Run the migrations.
        \"\"\"
        with self.schema.table('dummy_table') as table:
            pass

    def down(self):
        \"\"\"
        Revert the migrations.
        \"\"\"
        with self.schema.table('dummy_table') as table:
            pass
"""
