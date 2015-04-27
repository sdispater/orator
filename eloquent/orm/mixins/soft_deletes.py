# -*- coding: utf-8 -*-

from ..scopes import SoftDeletingScope


class SoftDeletes(object):

    _force_deleting = False

    @classmethod
    def boot_soft_deletes(cls, klass):
        """
        Boot the soft deleting mixin for a model.
        """
        klass.add_global_scope(SoftDeletingScope())

    def force_delete(self):
        """
        Force a hard delete on a soft deleted model.
        """
        self._force_deleting = True

        self.delete()

        self._force_deleting = False

    def _do_perform_delete_on_model(self):
        """
        Perform the actual delete query on this model instance.
        """
        if self._force_deleting:
            return self.with_trashed().where(self.get_key_name(), self.get_key()).force_delete()

        return self._run_soft_delete()

    def _run_soft_delete(self):
        """
        Perform the actual delete query on this model instance.
        """
        query = self.new_query().where(self.get_key_name(), self.get_key())

        time = self.fresh_timestamp()
        setattr(self, self.get_deleted_at_column(), time)

        query.update({
            self.get_deleted_at_column(): self.from_datetime(time)
        })

    def restore(self):
        """
        Restore a soft-deleted model instance.
        """
        setattr(self, self.get_deleted_at_column(), None)

        self.set_exists(True)

        result = self.save()

        return result

    def trashed(self):
        """
        Determine if the model instance has been soft-deleted

        :rtype: bool
        """
        return getattr(self, self.get_deleted_at_column()) is not None

    @classmethod
    def with_trashed(cls):
        """
        Get a new query builder that includes soft deletes.

        :rtype: eloquent.orm.builder.Builder
        """
        return cls().new_query_without_scope(SoftDeletingScope())

    @classmethod
    def only_trashed(cls):
        """
        Get a new query builder that only includes soft deletes

        :type cls: eloquent.orm.model.Model

        :rtype: eloquent.orm.builder.Builder
        """
        instance = cls()

        column = instance.get_qualified_deleted_at_column()

        return instance.new_query_without_scope(SoftDeletingScope()).where_not_null(column)

    def get_deleted_at_column(self):
        """
        Get the name of the "deleted at" column.

        :rtype: str
        """
        return getattr(self, 'DELETED_AT', 'deleted_at')

    def get_qualified_deleted_at_column(self):
        """
        Get the fully qualified "deleted at" column.

        :rtype: str
        """
        return '%s.%s' % (self.get_table(), self.get_deleted_at_column())
