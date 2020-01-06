# -*- coding: utf-8 -*-

from ..support.fluent import Fluent


class Blueprint(object):
    def __init__(self, table):
        """
        :param table: The table to operate on
        :type table: str
        """
        self._table = table
        self._columns = []
        self._commands = []
        self.engine = None
        self.charset = None
        self.collation = None

    def build(self, connection, grammar):
        """
        Execute the blueprint against the database.

        :param connection: The connection to use
        :type connection: orator.connections.Connection

        :param grammar: The grammar to user
        :type grammar: orator.query.grammars.QueryGrammar
        """
        for statement in self.to_sql(connection, grammar):
            connection.statement(statement)

    def to_sql(self, connection, grammar):
        """
        Get the raw SQL statements for the blueprint.

        :param connection: The connection to use
        :type connection: orator.connections.Connection

        :param grammar: The grammar to user
        :type grammar: orator.schema.grammars.SchemaGrammar

        :rtype: list
        """
        self._add_implied_commands()

        statements = []

        for command in self._commands:
            method = "compile_%s" % command.name

            if hasattr(grammar, method):
                sql = getattr(grammar, method)(self, command, connection)
                if sql is not None:
                    if isinstance(sql, list):
                        statements += sql
                    else:
                        statements.append(sql)

        return statements

    def _add_implied_commands(self):
        """
        Add the commands that are implied by the blueprint.
        """
        if len(self.get_added_columns()) and not self._creating():
            self._commands.insert(0, self._create_command("add"))

        if len(self.get_changed_columns()) and not self._creating():
            self._commands.insert(0, self._create_command("change"))

        return self._add_fluent_indexes()

    def _add_fluent_indexes(self):
        """
        Add the index commands fluently specified on columns:
        """
        for column in self._columns:
            for index in ["primary", "unique", "index"]:
                column_index = column.get(index)

                if column_index is True:
                    getattr(self, index)(column.name)

                    break
                elif column_index:
                    getattr(self, index)(column.name, column_index)

                    break

    def _creating(self):
        """
        Determine if the blueprint has a create command.

        :rtype: bool
        """
        for command in self._commands:
            if command.name == "create":
                return True

        return False

    def create(self):
        """
        Indicates that the table needs to be created.

        :rtype: Fluent
        """
        return self._add_command("create")

    def drop(self):
        """
        Indicates that the table needs to be dropped.

        :rtype: Fluent
        """
        self._add_command("drop")

        return self

    def drop_if_exists(self):
        """
        Indicates that the table should be dropped if it exists.

        :rtype: Fluent
        """
        return self._add_command("drop_if_exists")

    def drop_column(self, *columns):
        """
        Indicates that the given columns should be dropped.

        :param columns: The columns to drop
        :type columns: tuple

        :rtype: Fluent
        """
        columns = list(columns)

        return self._add_command("drop_column", columns=columns)

    def rename_column(self, from_, to):
        """
        Indicates that the given columns should be renamed.

        :param from_: The original column name
        :type from_: str
        :param to: The new name of the column
        :type to: str

        :rtype: Fluent
        """
        return self._add_command("rename_column", **{"from_": from_, "to": to})

    def drop_primary(self, index=None):
        """
        Indicate that the given primary key should be dropped.

        :param index: The index
        :type index: str

        :rtype: dict
        """
        return self._drop_index_command("drop_primary", "primary", index)

    def drop_unique(self, index):
        """
        Indicate that the given unique key should be dropped.

        :param index: The index
        :type index: str

        :rtype: Fluent
        """
        return self._drop_index_command("drop_unique", "unique", index)

    def drop_index(self, index):
        """
        Indicate that the given index should be dropped.

        :param index: The index
        :type index: str

        :rtype: Fluent
        """
        return self._drop_index_command("drop_index", "index", index)

    def drop_foreign(self, index):
        """
        Indicate that the given foreign key should be dropped.

        :param index: The index
        :type index: str

        :rtype: dict
        """
        return self._drop_index_command("drop_foreign", "foreign", index)

    def drop_timestamps(self):
        """
        Indicate that the timestamp columns should be dropped.

        :rtype: Fluent
        """
        return self.drop_column("created_at", "updated_at")

    def drop_soft_deletes(self):
        """
        Indicate that the soft delete column should be dropped

        :rtype: Fluent
        """
        return self.drop_column("deleted_at")

    def rename(self, to):
        """
        Rename the table to a given name

        :param to: The new table name
        :type to: str

        :rtype: Fluent
        """
        return self._add_command("rename", to=to)

    def primary(self, columns, name=None):
        """
        Specify the primary key(s) for the table

        :param columns: The primary key(s) columns
        :type columns: str or list

        :param name: The name of the primary key
        :type name: str

        :rtype: Fluent
        """
        return self._index_command("primary", columns, name)

    def unique(self, columns, name=None):
        """
        Specify a unique index on the table

        :param columns: The primary key(s) columns
        :type columns: str or list

        :param name: The name of the primary key
        :type name: str

        :rtype: Fluent
        """
        return self._index_command("unique", columns, name)

    def index(self, columns, name=None):
        """
        Specify an index on the table

        :param columns: The primary key(s) columns
        :type columns: str or list

        :param name: The name of the primary key
        :type name: str

        :rtype: Fluent
        """
        return self._index_command("index", columns, name)

    def foreign(self, columns, name=None):
        """
        Specify an foreign key on the table

        :param columns: The foreign key(s) columns
        :type columns: str or list

        :param name: The name of the foreign key
        :type name: str

        :rtype: Fluent
        """
        return self._index_command("foreign", columns, name)

    def increments(self, column):
        """
        Create a new auto-incrementing integer column on the table.

        :param column: The auto-incrementing column
        :type column: str

        :rtype: Fluent
        """
        return self.unsigned_integer(column, True)

    def big_increments(self, column):
        """
        Create a new auto-incrementing big integer column on the table.

        :param column: The auto-incrementing column
        :type column: str

        :rtype: Fluent
        """
        return self.unsigned_big_integer(column, True)

    def char(self, column, length=255):
        """
        Create a new char column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("char", column, length=length)

    def string(self, column, length=255):
        """
        Create a new string column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("string", column, length=length)

    def text(self, column):
        """
        Create a new text column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("text", column)

    def medium_text(self, column):
        """
        Create a new medium text column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("medium_text", column)

    def long_text(self, column):
        """
        Create a new long text column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("long_text", column)

    def integer(self, column, auto_increment=False, unsigned=False):
        """
        Create a new integer column on the table.

        :param column: The column
        :type column: str

        :type auto_increment: bool

        :type unsigned: bool

        :rtype: Fluent
        """
        return self._add_column(
            "integer", column, auto_increment=auto_increment, unsigned=unsigned
        )

    def big_integer(self, column, auto_increment=False, unsigned=False):
        """
        Create a new big integer column on the table.

        :param column: The column
        :type column: str

        :type auto_increment: bool

        :type unsigned: bool

        :rtype: Fluent
        """
        return self._add_column(
            "big_integer", column, auto_increment=auto_increment, unsigned=unsigned
        )

    def medium_integer(self, column, auto_increment=False, unsigned=False):
        """
        Create a new medium integer column on the table.

        :param column: The column
        :type column: str

        :type auto_increment: bool

        :type unsigned: bool

        :rtype: Fluent
        """
        return self._add_column(
            "medium_integer", column, auto_increment=auto_increment, unsigned=unsigned
        )

    def tiny_integer(self, column, auto_increment=False, unsigned=False):
        """
        Create a new tiny integer column on the table.

        :param column: The column
        :type column: str

        :type auto_increment: bool

        :type unsigned: bool

        :rtype: Fluent
        """
        return self._add_column(
            "tiny_integer", column, auto_increment=auto_increment, unsigned=unsigned
        )

    def small_integer(self, column, auto_increment=False, unsigned=False):
        """
        Create a new small integer column on the table.

        :param column: The column
        :type column: str

        :type auto_increment: bool

        :type unsigned: bool

        :rtype: Fluent
        """
        return self._add_column(
            "small_integer", column, auto_increment=auto_increment, unsigned=unsigned
        )

    def unsigned_integer(self, column, auto_increment=False):
        """
        Create a new unsigned integer column on the table.

        :param column: The column
        :type column: str

        :type auto_increment: bool

        :rtype: Fluent
        """
        return self.integer(column, auto_increment, True)

    def unsigned_big_integer(self, column, auto_increment=False):
        """
        Create a new unsigned big integer column on the table.

        :param column: The column
        :type column: str

        :type auto_increment: bool

        :rtype: Fluent
        """
        return self.big_integer(column, auto_increment, True)

    def float(self, column, total=8, places=2):
        """
        Create a new float column on the table.

        :param column: The column
        :type column: str

        :type total: int

        :type places: 2

        :rtype: Fluent
        """
        return self._add_column("float", column, total=total, places=places)

    def double(self, column, total=None, places=None):
        """
        Create a new double column on the table.

        :param column: The column
        :type column: str

        :type total: int

        :type places: 2

        :rtype: Fluent
        """
        return self._add_column("double", column, total=total, places=places)

    def decimal(self, column, total=8, places=2):
        """
        Create a new decimal column on the table.

        :param column: The column
        :type column: str

        :type total: int

        :type places: 2

        :rtype: Fluent
        """
        return self._add_column("decimal", column, total=total, places=places)

    def boolean(self, column):
        """
        Create a new decimal column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("boolean", column)

    def enum(self, column, allowed):
        """
        Create a new enum column on the table.
        
        :param column: The column
        :type column: str
        
        :type allowed: list
        
        :rtype: Fluent
        """
        return self._add_column("enum", column, allowed=allowed)

    def json(self, column):
        """
        Create a new json column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("json", column)

    def date(self, column):
        """
        Create a new date column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("date", column)

    def datetime(self, column):
        """
        Create a new datetime column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("datetime", column)

    def time(self, column):
        """
        Create a new time column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("time", column)

    def timestamp(self, column):
        """
        Create a new timestamp column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("timestamp", column)

    def nullable_timestamps(self):
        """
        Create nullable creation and update timestamps to the table.

        :rtype: Fluent
        """
        self.timestamp("created_at").nullable()
        self.timestamp("updated_at").nullable()

    def timestamps(self, use_current=True):
        """
        Create creation and update timestamps to the table.

        :rtype: Fluent
        """
        if use_current:
            self.timestamp("created_at").use_current()
            self.timestamp("updated_at").use_current()
        else:
            self.timestamp("created_at")
            self.timestamp("updated_at")

    def soft_deletes(self):
        """
        Add a "deleted at" timestamp to the table.

        :rtype: Fluent
        """
        return self.timestamp("deleted_at").nullable()

    def binary(self, column):
        """
        Create a new binary column on the table.

        :param column: The column
        :type column: str

        :rtype: Fluent
        """
        return self._add_column("binary", column)

    def morphs(self, name, index_name=None):
        """
        Add the proper columns for a polymorphic table.

        :type name: str

        :type index_name: str
        """
        self.unsigned_integer("%s_id" % name)
        self.string("%s_type" % name)
        self.index(["%s_id" % name, "%s_type" % name], index_name)

    def _drop_index_command(self, command, type, index):
        """
        Create a new drop index command on the blueprint.

        :param command: The command
        :type command: str

        :param type: The index type
        :type type: str

        :param index: The index name
        :type index: str

        :rtype: Fluent
        """
        columns = []

        if isinstance(index, list):
            columns = index

            index = self._create_index_name(type, columns)

        return self._index_command(command, columns, index)

    def _index_command(self, type, columns, index):
        """
        Add a new index command to the blueprint.

        :param type: The index type
        :type type: str

        :param columns: The index columns
        :type columns: list or str

        :param index: The index name
        :type index: str

        :rtype: Fluent
        """
        if not isinstance(columns, list):
            columns = [columns]

        if not index:
            index = self._create_index_name(type, columns)

        return self._add_command(type, index=index, columns=columns)

    def _create_index_name(self, type, columns):
        if not isinstance(columns, list):
            columns = [columns]

        index = "%s_%s_%s" % (
            self._table,
            "_".join([str(column) for column in columns]),
            type,
        )

        return index.lower().replace("-", "_").replace(".", "_")

    def _add_column(self, type, name, **parameters):
        """
        Add a new column to the blueprint.

        :param type: The column type
        :type type: str

        :param name: The column name
        :type name: str

        :param parameters: The column parameters
        :type parameters: dict

        :rtype: Fluent
        """
        parameters.update({"type": type, "name": name})

        column = Fluent(**parameters)
        self._columns.append(column)

        return column

    def _remove_column(self, name):
        """
        Removes a column from the blueprint.

        :param name: The column name
        :type name: str

        :rtype: Blueprint
        """
        self._columns = filter(lambda c: c.name != name, self._columns)

        return self

    def _add_command(self, name, **parameters):
        """
        Add a new command to the blueprint.

        :param name: The command name
        :type name: str

        :param parameters: The command parameters
        :type parameters: dict

        :rtype: Fluent
        """
        command = self._create_command(name, **parameters)
        self._commands.append(command)

        return command

    def _create_command(self, name, **parameters):
        """
        Create a new command.

        :param name: The command name
        :type name: str

        :param parameters: The command parameters
        :type parameters: dict

        :rtype: Fluent
        """
        parameters.update({"name": name})

        return Fluent(**parameters)

    def get_table(self):
        return self._table

    def get_columns(self):
        return self._columns

    def get_commands(self):
        return self._commands

    def get_added_columns(self):
        return list(filter(lambda column: not column.get("change"), self._columns))

    def get_changed_columns(self):
        return list(filter(lambda column: column.get("change"), self._columns))
