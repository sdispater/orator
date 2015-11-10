### 0.7

(November 10th, 2015)

##### Improvements

- [#15](https://github.com/sdispater/orator/issues/9) Execute migrations inside a transaction.
- [#13](https://github.com/sdispater/orator/issues/9) Support database seeding and model factories.
- [#9](https://github.com/sdispater/orator/issues/9) Support for SQLite foreign keys.
- Relationships decorators.
- Morph relationships now using a name (default being the table name) rather than a class name.

##### Fixes

- [#14](https://github.com/sdispater/orator/issues/14) Changing columns with SchemaBuilder does not work with some types.
- [#16](https://github.com/sdispater/orator/issues/16) The last page of LengthAwarePaginator is not calculated properly in Python 2.7.
- Avoid an error when psycopg2 is not installed.
- Fix dynamic properties for eagerloaded relationships.


### 0.6.4

(July 7th, 2015)

##### Fixes

- [#11](https://github.com/sdispater/orator/issues/11) Paginator.resolve_current_page() raises and error on Python 2.7.


### 0.6.3

(June 30th, 2015)

##### Improvements

- [#10](https://github.com/sdispater/orator/issues/10) Remove hard dependencies in commands.

##### Fixes

- [#8](https://github.com/sdispater/orator/issues/8) Reconnection on lost connection does not properly work.


### 0.6.2

(June 9nd, 2015)

##### Fixes

- Fixes a bug when results rather than the relation was returned
- #7 Starting a new query from a BelongsToMany relation does not maintain pivot columns.
- #6 Model.set_table() method does not properly handle pivot classes.
- #5 Model.fresh() method raises an error for models retrieved from relations.


### 0.6.1

(June 2nd, 2015)

- Fixes a lot of problems that broke relations behavior in 0.6.
- Adds raw() method to orm builder passthru.

### 0.6

(May 31th, 2015)

- Adds pagination support
- Adds model events support
- Implements Model.load() method
- Adds to_json() method to collections
- Makes to_json() methods consistent.
- Fixes how relations are retrieved from strings
- Fixes classes lookup in morph_to() method
- Fixes mutators not being called when initiating models
- Improves models attributes lookup
- Removes DynamicProperty class. Relations are dynamic themselves.

### 0.5

(May 24th, 2015)

- Adds database migrations
- Adds mutators and accessors
- Fix BelongsToMany.save_many() default joinings value

### 0.4

(April 28th, 2015)

- Adds Schema Builder
- Adds scopes support
- Adds support for related name in relationships declaration

### 0.3.1

(April 19th, 2015)

- Fix MySQLdb compatibiity issues
- Fix wrong default key value for Builder.lists() method

### 0.3

(April 3th, 2015)

- Query logging
- Polymorphic relations
- Adds support for Model.has() method
- Adds support for callbacks in eager load conditions
- Adds support for multi-threaded applications by default


### 0.2

(March 31th, 2015)

- Adds actual ORM with relationships and eager loading
- Adds chunk support for QueryBuilder
- Properly close connections when using reconnect() and disconnect() methods


### 0.1

(March 18th, 2015)

- Initial release
