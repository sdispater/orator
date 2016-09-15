# -*- coding: utf-8 -*-

import hashlib
import time
import inflection
from ...exceptions.orm import ModelNotFound
from ...query.expression import QueryExpression
from ..collection import Collection
import orator.orm.model
from .relation import Relation
from .result import Result


class BelongsToMany(Relation):

    _table = None
    _other_key = None
    _foreign_key = None
    _relation_name = None

    _pivot_columns = []
    _pivot_wheres = []

    def __init__(self, query, parent, table, foreign_key, other_key, relation_name=None):
        """
        :param query: A Builder instance
        :type query: Builder

        :param parent: The parent model
        :type parent: Model

        :param table: The pivot table
        :type table: str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param other_key: The other key
        :type other_key: str

        :param relation_name: The relation name
        :type relation_name: str
        """
        self._table = table
        self._other_key = other_key
        self._foreign_key = foreign_key
        self._relation_name = relation_name

        self._pivot_columns = []
        self._pivot_wheres = []

        super(BelongsToMany, self).__init__(query, parent)

    def get_results(self):
        """
        Get the results of the relationship.
        """
        return self.get()

    def where_pivot(self, column, operator=None, value=None, boolean='and'):
        """
        Set a where clause for a pivot table column.

        :param column: The column of the where clause, can also be a QueryBuilder instance for sub where
        :type column: str|Builder

        :param operator: The operator of the where clause
        :type operator: str

        :param value: The value of the where clause
        :type value: mixed

        :param boolean: The boolean of the where clause
        :type boolean: str

        :return: self
        :rtype: self
        """
        self._pivot_wheres.append([column, operator, value, boolean])

        return self._query.where('%s.%s' % (self._table, column), operator, value, boolean)

    def or_where_pivot(self, column, operator=None, value=None):
        """
        Set an or where clause for a pivot table column.

        :param column: The column of the where clause, can also be a QueryBuilder instance for sub where
        :type column: str|Builder

        :param operator: The operator of the where clause
        :type operator: str

        :param value: The value of the where clause
        :type value: mixed

        :return: self
        :rtype: BelongsToMany
        """
        return self.where_pivot(column, operator, value, 'or')

    def first(self, columns=None):
        """
        Execute the query and get the first result.

        :type columns: list
        """
        self._query.take(1)

        results = self.get(columns)

        if len(results) > 0:
            return results.first()

        return

    def first_or_fail(self, columns=None):
        """
        Execute the query and get the first result or raise an exception.

        :type columns: list

        :raises: ModelNotFound
        """
        model = self.first(columns)
        if model is not None:
            return model

        raise ModelNotFound(self._parent.__class__)

    def get(self, columns=None):
        """
        Execute the query as a "select" statement.

        :type columns: list

        :rtype: orator.Collection
        """
        if columns is None:
            columns = ['*']

        if self._query.get_query().columns:
            columns = []

        select = self._get_select_columns(columns)

        models = self._query.add_select(*select).get_models()

        self._hydrate_pivot_relation(models)

        if len(models) > 0:
            models = self._query.eager_load_relations(models)

        return self._related.new_collection(models)

    def _hydrate_pivot_relation(self, models):
        """
        Hydrate the pivot table relationship on the models.

        :type models: list
        """
        for model in models:
            pivot = self.new_existing_pivot(self._clean_pivot_attributes(model))

            model.set_relation('pivot', pivot)

    def _clean_pivot_attributes(self, model):
        """
        Get the pivot attributes from a model.

        :type model: orator.Model
        """
        values = {}
        delete_keys = []

        for key, value in model.get_attributes().items():
            if key.find('pivot_') == 0:
                values[key[6:]] = value

                delete_keys.append(key)

        for key in delete_keys:
            delattr(model, key)

        return values

    def add_constraints(self):
        """
        Set the base constraints on the relation query.

        :rtype: None
        """
        self._set_join()

        if BelongsToMany._constraints:
            self._set_where()

    def get_relation_count_query(self, query, parent):
        """
        Add the constraints for a relationship count query.

        :type query: orator.orm.Builder
        :type parent: orator.orm.Builder

        :rtype: orator.orm.Builder
        """
        if parent.get_query().from__ == query.get_query().from__:
            return self.get_relation_count_query_for_self_join(query, parent)

        self._set_join(query)

        return super(BelongsToMany, self).get_relation_count_query(query, parent)

    def get_relation_count_query_for_self_join(self, query, parent):
        """
        Add the constraints for a relationship count query on the same table.

        :type query: orator.orm.Builder
        :type parent: orator.orm.Builder

        :rtype: orator.orm.Builder
        """
        query.select(QueryExpression('COUNT(*)'))

        table_prefix = self._query.get_query().get_connection().get_table_prefix()

        hash_ = self.get_relation_count_hash()
        query.from_('%s AS %s%s' % (self._table, table_prefix, hash_))

        key = self.wrap(self.get_qualified_parent_key_name())

        return query.where('%s.%s' % (hash_, self._foreign_key), '=', QueryExpression(key))

    def get_relation_count_hash(self):
        """
        Get a relationship join table hash.

        :rtype: str
        """
        return 'self_%s' % (hashlib.md5(str(time.time()).encode()).hexdigest())

    def _get_select_columns(self, columns=None):
        """
        Set the select clause for the relation query.

        :param columns: The columns
        :type columns: list

        :rtype: list
        """
        if columns == ['*'] or columns is None:
            columns = ['%s.*' % self._related.get_table()]

        return columns + self._get_aliased_pivot_columns()

    def _get_aliased_pivot_columns(self):
        """
        Get the pivot columns for the relation.

        :rtype: list
        """
        defaults = [self._foreign_key, self._other_key]

        columns = []

        for column in defaults + self._pivot_columns:
            value = '%s.%s AS pivot_%s' % (self._table, column, column)
            if value not in columns:
                columns.append('%s.%s AS pivot_%s' % (self._table, column, column))

        return columns

    def _has_pivot_column(self, column):
        """
        Determine whether the given column is defined as a pivot column.

        :param column: The column to check
        :type column: str

        :rtype: bool
        """
        return column in self._pivot_columns

    def _set_join(self, query=None):
        """
        Set the join clause for the relation query.

        :param query: The query builder
        :type query: orator.orm.Builder

        :return: self
        :rtype: BelongsToMany
        """
        if not query:
            query = self._query

        base_table = self._related.get_table()

        key = '%s.%s' % (base_table, self._related.get_key_name())

        query.join(self._table, key, '=', self.get_other_key())

        return self

    def _set_where(self):
        """
        Set the where clause for the relation query.

        :return: self
        :rtype: BelongsToMany
        """
        foreign = self.get_foreign_key()

        self._query.where(foreign, '=', self._parent.get_key())

        return self

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        self._query.where_in(self.get_foreign_key(), self.get_keys(models))

    def init_relation(self, models, relation):
        """
        Initialize the relation on a set of models.

        :type models: list
        :type relation:  str
        """
        for model in models:
            model.set_relation(relation, Result(self._related.new_collection(), self, model))

        return models

    def match(self, models, results, relation):
        """
        Match the eagerly loaded results to their parents.

        :type models: list
        :type results: Collection
        :type relation:  str
        """
        dictionary = self._build_dictionary(results)

        for model in models:
            key = model.get_key()

            if key in dictionary:
                collection = Result(self._related.new_collection(dictionary[key]), self, model)
            else:
                collection = Result(self._related.new_collection(), self, model)

            model.set_relation(relation, collection)

        return models

    def _build_dictionary(self, results):
        """
        Build model dictionary keyed by the relation's foreign key.

        :param results: The results
        :type results: Collection

        :rtype: dict
        """
        foreign = self._foreign_key

        dictionary = {}

        for result in results:
            key = getattr(result.pivot, foreign)
            if key not in dictionary:
                dictionary[key] = []

            dictionary[key].append(result)

        return dictionary

    def touch(self):
        """
        Touch all of the related models of the relationship.
        """
        key = self.get_related().get_key_name()

        columns = self.get_related_fresh_update()

        ids = self.get_related_ids()

        if len(ids) > 0:
            self.get_related().new_query().where_in(key, ids).update(columns)

    def get_related_ids(self):
        """
        Get all of the IDs for the related models.

        :rtype: list
        """
        related = self.get_related()

        full_key = related.get_qualified_key_name()

        return self.get_query().select(full_key).lists(related.get_key_name())

    def save(self, model, joining=None, touch=True):
        """
        Save a new model and attach it to the parent model.

        :type model: orator.Model
        :type joining: dict
        :type touch: bool

        :rtype: orator.Model
        """
        if joining is None:
            joining = {}

        model.save({'touch': False})

        self.attach(model.get_key(), joining, touch)

        return model

    def save_many(self, models, joinings=None):
        """
        Save a list of new models and attach them to the parent model

        :type models: list
        :type joinings: dict

        :rtype: list
        """
        if joinings is None:
            joinings = {}

        for key, model in enumerate(models):
            self.save(model, joinings.get(key), False)

        self.touch_if_touching()

        return models

    def find_or_new(self, id, columns=None):
        """
        Find a model by its primary key or return new instance of the related model.

        :param id: The primary key
        :type id: mixed

        :param columns:  The columns to retrieve
        :type columns: list

        :rtype: Collection or Model
        """
        instance = self._query.find(id, columns)
        if instance is None:
            instance = self.get_related().new_instance()

        return instance

    def first_or_new(self, _attributes=None, **attributes):
        """
        Get the first related model record matching the attributes or instantiate it.

        :param attributes:  The attributes
        :type attributes: dict

        :rtype: Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        instance = self._query.where(attributes).first()
        if instance is None:
            instance = self._related.new_instance()

        return instance

    def first_or_create(self, _attributes=None, _joining=None, _touch=True, **attributes):
        """
        Get the first related model record matching the attributes or create it.

        :param attributes:  The attributes
        :type attributes: dict

        :rtype: Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        instance = self._query.where(attributes).first()
        if instance is None:
            instance = self.create(attributes, _joining or {}, _touch)

        return instance

    def update_or_create(self, attributes, values=None, joining=None, touch=True):
        """
        Create or update a related record matching the attributes, and fill it with values.

        :param attributes: The attributes
        :type attributes: dict

        :param values: The values
        :type values: dict

        :rtype: Model
        """
        if values is None:
            values = {}

        instance = self._query.where(attributes).first()

        if instance is None:
            return self.create(values, joining, touch)

        instance.fill(**values)

        instance.save({'touch': False})

        return instance

    def create(self, _attributes=None, _joining=None, _touch=True, **attributes):
        """
        Create a new instance of the related model.

        :param attributes: The attributes
        :type attributes: dict

        :rtype: orator.orm.Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        instance = self._related.new_instance(attributes)

        instance.save({'touch': False})

        self.attach(instance.get_key(), _joining, _touch)

        return instance

    def create_many(self, records, joinings=None):
        """
        Create a list of new instances of the related model.
        """
        if joinings is None:
            joinings = []

        instances = []

        for key, record in enumerate(records):
            instances.append(self.create(record), joinings[key], False)

        self.touch_if_touching()

        return instances

    def sync(self, ids, detaching=True):
        """
        Sync the intermediate tables with a list of IDs or collection of models
        """
        changes = {
            'attached': [],
            'detached': [],
            'updated': []
        }

        if isinstance(ids, Collection):
            ids = ids.model_keys()

        current = self._new_pivot_query().lists(self._other_key).all()

        records = self._format_sync_list(ids)

        detach = [x for x in current if x not in records.keys()]

        if detaching and len(detach) > 0:
            self.detach(detach)

            changes['detached'] = detach

        changes.update(self._attach_new(records, current, False))

        if len(changes['attached']) or len(changes['updated']):
            self.touch_if_touching()

        return changes

    def _format_sync_list(self, records):
        """
        Format the sync list so that it is keyed by ID.
        """
        results = {}

        for attributes in records:
            if not isinstance(attributes, dict):
                id, attributes = attributes, {}
            else:
                id = list(attributes.keys())[0]
                attributes = attributes[id]

            results[id] = attributes

        return results

    def _attach_new(self, records, current, touch=True):
        """
        Attach all of the IDs that aren't in the current dict.
        """
        changes = {
            'attached': [],
            'updated': []
        }

        for id, attributes in records.items():
            if id not in current:
                self.attach(id, attributes, touch)

                changes['attached'].append(id)
            elif len(attributes) > 0 and self.update_existing_pivot(id, attributes, touch):
                changes['updated'].append(id)

        return changes

    def update_existing_pivot(self, id, attributes, touch=True):
        """
        Update an existing pivot record on the table.
        """
        if self.updated_at() in self._pivot_columns:
            attributes = self.set_timestamps_on_attach(attributes, True)

        updated = self.new_pivot_statement_for_id(id).update(attributes)

        if touch:
            self.touch_if_touching()

        return updated

    def attach(self, id, attributes=None, touch=True):
        """
        Attach a model to the parent.
        """
        if isinstance(id, orator.orm.Model):
            id = id.get_key()

        query = self.new_pivot_statement()

        if not isinstance(id, list):
            id = [id]

        query.insert(self._create_attach_records(id, attributes))

        if touch:
            self.touch_if_touching()

    def _create_attach_records(self, ids, attributes):
        """
        Create a list of records to insert into the pivot table.
        """
        records = []

        timed = (self._has_pivot_column(self.created_at())
                 or self._has_pivot_column(self.updated_at()))

        for key, value in enumerate(ids):
            records.append(self._attacher(key, value, attributes, timed))

        return records

    def _attacher(self, key, value, attributes, timed):
        """
        Create a full attachment record payload.
        """
        id, extra = self._get_attach_id(key, value, attributes)

        record = self._create_attach_record(id, timed)

        if extra:
            record.update(extra)

        return record

    def _get_attach_id(self, key, value, attributes):
        """
        Get the attach record ID and extra attributes.
        """
        if isinstance(value, dict):
            key = list(value.keys())[0]
            attributes.update(value[key])

            return [key, attributes]

        return value, attributes

    def _create_attach_record(self, id, timed):
        """
        Create a new pivot attachement record.
        """
        record = {}

        record[self._foreign_key] = self._parent.get_key()

        record[self._other_key] = id

        if timed:
            record = self._set_timestamps_on_attach(record)

        return record

    def _set_timestamps_on_attach(self, record, exists=False):
        """
        Set the creation an update timestamps on an attach record.
        """
        fresh = self._parent.fresh_timestamp()

        if not exists and self._has_pivot_column(self.created_at()):
            record[self.created_at()] = fresh

        if self._has_pivot_column(self.updated_at()):
            record[self.updated_at()] = fresh

        return record

    def detach(self, ids=None, touch=True):
        """
        Detach models from the relationship.
        """
        if isinstance(ids, orator.orm.model.Model):
            ids = ids.get_key()

        if ids is None:
            ids = []

        query = self._new_pivot_query()

        if not isinstance(ids, list):
            ids = [ids]

        if len(ids) > 0:
            query.where_in(self._other_key, ids)

        if touch:
            self.touch_if_touching()

        results = query.delete()

        return results

    def touch_if_touching(self):
        """
        Touch if the parent model is being touched.
        """
        if self._touching_parent():
            self.get_parent().touch()

        if self.get_parent().touches(self._relation_name):
            self.touch()

    def _touching_parent(self):
        """
        Determine if we should touch the parent on sync.
        """
        return self.get_related().touches(self._guess_inverse_relation())

    def _guess_inverse_relation(self):
        return inflection.camelize(inflection.pluralize(self.get_parent().__class__.__name__))

    def _new_pivot_query(self):
        """
        Create a new query builder for the pivot table.

        :rtype: orator.orm.Builder
        """
        query = self.new_pivot_statement()

        for where_args in self._pivot_wheres:
            query.where(*where_args)

        return query.where(self._foreign_key, self._parent.get_key())

    def new_pivot_statement(self):
        """
        Get a new plain query builder for the pivot table.
        """
        return self._query.get_query().new_query().from_(self._table)

    def new_pivot_statement_for_id(self, id):
        """
        Get a new pivot statement for a given "other" id.
        """
        return self._new_pivot_query().where(self._other_key, id)

    def new_pivot(self, attributes=None, exists=False):
        """
        Create a new pivot model instance.
        """
        pivot = self._related.new_pivot(self._parent, attributes, self._table, exists)

        return pivot.set_pivot_keys(self._foreign_key, self._other_key)

    def new_existing_pivot(self, attributes):
        """
        Create a new existing pivot model instance.
        """
        return self.new_pivot(attributes, True)

    def with_pivot(self, *columns):
        """
        Set the columns on the pivot table to retrieve.
        """
        columns = list(columns)

        self._pivot_columns += columns

        return self

    def with_timestamps(self, created_at=None, updated_at=None):
        """
        Specify that the pivot table has creation and update columns.
        """
        if not created_at:
            created_at = self.created_at()

        if not updated_at:
            updated_at = self.updated_at()

        return self.with_pivot(created_at, updated_at)

    def get_related_fresh_update(self):
        """
        Get the related model's update at column at
        """
        return {self._related.get_updated_at_column(): self._related.fresh_timestamp()}

    def get_has_compare_key(self):
        """
        Get the key for comparing against the parent key in "has" query.
        """
        return self.get_foreign_key()

    def get_foreign_key(self):
        return '%s.%s' % (self._table, self._foreign_key)

    def get_other_key(self):
        return '%s.%s' % (self._table, self._other_key)

    def get_table(self):
        return self._table

    def get_relation_name(self):
        return self._relation_name

    def _new_instance(self, model):
        relation = BelongsToMany(
            self.new_query(),
            model,
            self._table,
            self._foreign_key,
            self._other_key,
            self._relation_name
        )

        relation.with_pivot(*self._pivot_columns)

        return relation
