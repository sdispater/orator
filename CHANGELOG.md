# Change Log

## [0.9.9] - 2019-07-15

### Fixed

- Fixed missing relationships when eager loading multiple nested relationships.
- Fixed a possible `AttributeError` when starting a transaction.
- Fixed an infinite recursion when using `where_exists()` on a soft-deletable model.
- Fixed some cases where a reconnection would not occur for PostgreSQL.


## [0.9.8] - 2018-10-10

### Fixed

- Fixed the `morphed_by_many()` decorator.
- Fixed decoding errors for MySQL.
- Fixed connection errors check.
- Fixed the `touches()` method.
- Fixed `has_many` not showing `DISTINCT`.
- Fixed `save_many()` for Python 3.
- Fixed an error when listing columns for recent MySQL versions.


## [0.9.7] - 2017-05-17

### Fixed

- Fixed `orator` command no longer working


## [0.9.6] - 2017-05-16

### Added

- Added support for `DATE` types in models.
- Added support for fractional seconds for the `TIMESTAMP` type in MySQL 5.6.4+.
- Added support for fractional seconds for the `TIMESTAMP` and `TIME` types in PostreSQL.

### Changed

- Improved implementation of the `chunk` method.

### Fixed

- Fixed timezone offset errors when inserting datetime aware objects into PostgreSQL.
- Fixed a bug occurring when using `__touches__` with an optional relationship.
- Fixed collections serialization when using the query builder


## [0.9.5] - 2017-02-11

### Changed

- `make:migration` now shows the name of the created migration file. (Thanks to [denislins](https://github.com/denislins))

### Fixed

- Fixed transactions not working for PostgreSQL and SQLite.


## [0.9.4] - 2017-01-12

### Fixed

- Fixes `BelongsTo.associate()` for non saved models.
- Fixes reconnection for PostgreSQL.
- Fixes dependencies (changed `fake-factory` to `Faker`) (thanks to [acristoffers](https://github.com/acristoffers))


## [0.9.3] - 2016-11-10

### Fixed

- Fixes `compile_table_exists()` method in PostgreSQL schema grammar that could break migrations.


## [0.9.2] - 2016-10-17

### Changed

- Adds ability to specify multiple conditions in a single `where()` (thanks to [mathankumart](https://github.com/mathankumart)).

### Fixed

- Fixes an error when table prefix is set to `None`.
- Fixes column listing.


## [0.9.1] - 2016-09-29

### Changed

- Improves migrate command output when pretending.

### Fixed

- Fixes errors when using PyMySQL.
- Fixes `use_qmark` information not being passed to schema grammars.


## [0.9.0] - 2016-09-15

### Changed

###### ORM

- Removed `arrow` support for [pendulum](https://pendulum.eustace.io).

###### Connection

- Improved connectors.

###### Schema

- Makes the `use_current=True` the default for `timestamps()`.

###### Query

- Allow usage of qmark syntax for all backends.
- Made `QueryBuilder` return Collections.
- Merging queries also merges columns.
- Made query builder results accessible by attributes.

###### DBAL

- Improved connectors and dbal to detect platform versions.

###### Collections

- Removed `Collection` code and uses [backpack](https://github.com/sdispater/backpack) package instead.

### Fixed

###### ORM

- Fixed the update of pivots.
- Fixed behavior for dates accessor.
- Fixed connection not being properly set when specifying the connection with `on()`

###### Commands

- Made the `-P/--pretend` command option work.

###### Schema

- Fixed schema grammars.
- Fixed an error when modify a table with an enum column in MySQL.

###### DBAL

- Fixed behavior for enum columns.


## [0.8.2] - 2016-06-02

### Changed

###### Connection

- Updating connectors to raise an exception when backend packages are missing.

### Fixed

###### ORM

- Fixing a possible `Memory Error: stack overflow` error when accessing relations.
- Fixing builder copying process to avoir issues with `PyMySQL`(thanks to [ihumanable](https://github.com/ihumanable)).

###### Commands

- Fixing the `-n/--no-interaction` option not automatically confirming questions.
- Removing the check character in migration commands output to avoid errors on Windows.

###### Connection

- Updating connectors to raise an exception when backend packages are missing.
- Adding standard name resolution to the `purge` method (thanks to [ihumanable](https://github.com/ihumanable)).

###### DBAL

- Fixing setting foreign key constraint name for MySQL.
- Handling missing `constraint_name` for sqlite (thanks to [ihumanable](https://github.com/ihumanable)).


## [0.8.1] - 2016-03-30

### Fixed

###### ORM

- Removing call to `Model._boot_columns()` to avoid errors for column types not supported by the dbal.

###### Schema Builder

- Fixing `Blueprint.char()` method (thanks to [ihumanable](https://github.com/ihumanable)).
- Fixing `Fluent` behavior.

###### Commands

- Fixing `orator` command not working on Windows.
- Fixing `migrate:status` command not switching databases.

###### Connection

- Fixing a bug when calling `Connnection.disconnect()` after a reconnection when not using read/write connections.
- Fixing `MySQLConnection.get_server_version()` method to be compatible with `PyMySQL` (thanks to [gdraynz](https://github.com/gdraynz)).


## [0.8] - 2016-02-08

### Added

###### ORM

- [#30](https://github.com/sdispater/orator/issues/30) Support for default values
- [#29](https://github.com/sdispater/orator/issues/29) Supporting only one timestamp column on models
- [#26](https://github.com/sdispater/orator/issues/26) Adding support for extra conditions on relationships
- Adding `@scope` decorator to define query scopes.

###### Schema builder

- Adding support for a `use_current()` on timestamps

###### Query Builder

- [#28](https://github.com/sdispater/orator/issues/28) Making where_in() method accept Collection instances

###### Commands

- Adding a `make:model` command

###### Collections

- Adds `flatten()` method to `Collection` class

### Changed

###### ORM

- Improving global scopes

##### Schema builder

- Improving dbal to support SQLite fully.
- Improving fluents

###### Connection

- Using unicode by default for mysql and postgres.
- Improves how queries are run in `Connection` class

### Fixed

###### ORM

- Fixes `Model.get_foreign_key()` method
- Fixes soft deletes
- Avoid going through \_\_setattr\_\_ method when setting timestamps

###### Schema Builder

- [#33](https://github.com/sdispater/orator/issues/33) [SQLite] Renaming or dropping columns loses NULL constraint
- [#32](https://github.com/sdispater/orator/issues/32) [SQLite] Renaming or dropping columns fails when columns' name is a keyword
- [#31](https://github.com/sdispater/orator/issues/31) [SQLite] Changing columns loses default column values.

###### Query Builder

- Fixes query grammar default columns value

###### Connection

- Fixing `Connection._try_again_if_caused_by_lost_connection()` not being called
- Preventing default connection being set to None
- Fixing json type behavior for Postgres

###### Migrations
- Fixing migration stubs


## [0.7.1] - 2015-11-30

### Added

- [#20](https://github.com/sdispater/orator/issues/20) Collections have been improved (New methods added)

### Changed

- Commands have been improved
- The `to_dict` methods on the `Model`, `Collection` classes and paginators are now deprecated. Use `serialize` instead.

### Fixed

* [#22](https://github.com/sdispater/orator/issues/22) Model.fill() and other methods now accept a dictionary in addition to keyword arguments.
* MySQL charset config value was not used when connecting. This is now fixed. (Thanks to [@heavenshell](https://github.com/heavenshell))
* [#24](https://github.com/sdispater/orator/issues/24) Dynamic properties called the wrong methods when accessing the related items.


## [0.7] - 2015-11-10

### Added

- [#13](https://github.com/sdispater/orator/issues/9) Support database seeding and model factories.
- [#9](https://github.com/sdispater/orator/issues/9) Support for SQLite foreign keys.
- Relationships decorators.

### Changed

- [#15](https://github.com/sdispater/orator/issues/9) Execute migrations inside a transaction.
- Morph relationships now using a name (default being the table name) rather than a class name.

### Fixed

- [#14](https://github.com/sdispater/orator/issues/14) Changing columns with SchemaBuilder does not work with some types.
- [#16](https://github.com/sdispater/orator/issues/16) The last page of LengthAwarePaginator is not calculated properly in Python 2.7.
- Avoid an error when psycopg2 is not installed.
- Fix dynamic properties for eagerloaded relationships.


## [0.6.4] - 2015-07-07

### Fixed

- [#11](https://github.com/sdispater/orator/issues/11) Paginator.resolve_current_page() raises and error on Python 2.7.


## [0.6.3] - 2015-06-30

### Changed

- [#10](https://github.com/sdispater/orator/issues/10) Remove hard dependencies in commands.

### Fixed

- [#8](https://github.com/sdispater/orator/issues/8) Reconnection on lost connection does not properly work.


## [0.6.2] - 2015-06-09

##### Fixed

- Fixes a bug when results rather than the relation was returned
- Starting a new query from a BelongsToMany relation does not maintain pivot columns.
- Model.set_table() method does not properly handle pivot classes.
- Model.fresh() method raises an error for models retrieved from relations.


## [0.6.1] - 2015-06-02

### Changed

- Adds raw() method to orm builder passthru.

### Fixed

- Fixes a lot of problems that broke relations behavior in 0.6.


## [0.6] - 2015-05-31

### Added

- Adds pagination support
- Adds model events support
- Implements Model.load() method
- Adds to_json() method to collections

### Changed

- Makes to_json() methods consistent.
- Improves models attributes lookup
- Removes DynamicProperty class. Relations are dynamic themselves.

### Fixed

- Fixes how relations are retrieved from strings
- Fixes classes lookup in morph_to() method
- Fixes mutators not being called when initiating models


## [0.5] - 2015-05-24

### Added

- Adds database migrations
- Adds mutators and accessors

### Fixed

- Fix BelongsToMany.save_many() default joinings value


## [0.4] - 2015-04-28

### Added

- Adds Schema Builder
- Adds scopes support
- Adds support for related name in relationships declaration


## [0.3.1] - 2015-04-19

### Fixed

- Fix MySQLdb compatibiity issues
- Fix wrong default key value for Builder.lists() method


## [0.3] - 2015-04-03

### Added

- Query logging
- Polymorphic relations
- Adds support for Model.has() method
- Adds support for callbacks in eager load conditions
- Adds support for multi-threaded applications by default


## [0.2] - 2015-03-31

### Added

- Adds actual ORM with relationships and eager loading
- Adds chunk support for QueryBuilder

### Fixed

- Properly close connections when using reconnect() and disconnect() methods


## [0.1] - 2015-03-18

Initial release


[Unreleased]: https://github.com/sdispater/orator/compare/0.9.9...0.9
[0.9.9]: https://github.com/sdispater/orator/releases/0.9.9
[0.9.8]: https://github.com/sdispater/orator/releases/0.9.8
[0.9.7]: https://github.com/sdispater/orator/releases/0.9.7
[0.9.6]: https://github.com/sdispater/orator/releases/0.9.6
[0.9.5]: https://github.com/sdispater/orator/releases/0.9.5
[0.9.4]: https://github.com/sdispater/orator/releases/0.9.4
[0.9.3]: https://github.com/sdispater/orator/releases/0.9.3
[0.9.2]: https://github.com/sdispater/orator/releases/0.9.2
[0.9.1]: https://github.com/sdispater/orator/releases/0.9.1
[0.9.0]: https://github.com/sdispater/orator/releases/0.9.0
[0.8.2]: https://github.com/sdispater/orator/releases/tag/0.8.2
[0.8.1]: https://github.com/sdispater/orator/releases/tag/0.8.1
[0.8]: https://github.com/sdispater/orator/releases/tag/0.8
[0.7]: https://github.com/sdispater/orator/releases/tag/0.7
[0.7.1]: https://github.com/sdispater/orator/releases/tag/0.7.1
[0.6.4]: https://github.com/sdispater/orator/releases/tag/0.6.4
[0.6.3]: https://github.com/sdispater/orator/releases/tag/0.6.3
[0.6.2]: https://github.com/sdispater/orator/releases/tag/0.6.2
[0.6.1]: https://github.com/sdispater/orator/releases/tag/0.6.1
[0.6]: https://github.com/sdispater/orator/releases/tag/0.6
[0.5]: https://github.com/sdispater/orator/releases/tag/0.5
[0.4]: https://github.com/sdispater/orator/releases/tag/0.4
[0.3.1]: https://github.com/sdispater/orator/releases/tag/0.3.1
[0.3]: https://github.com/sdispater/orator/releases/tag/0.3
[0.2]: https://github.com/sdispater/orator/releases/tag/0.3
[0.1]: https://github.com/sdispater/orator/releases/tag/0.3
