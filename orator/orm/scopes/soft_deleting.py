# -*- coding: utf-8 -*-

from .scope import Scope


class SoftDeletingScope(Scope):

    _extensions = ['force_delete', 'restore', 'with_trashed', 'only_trashed']

    def apply(self, builder, model):
        """
        Apply the scope to a given query builder.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder

        :param model: The model
        :type model: orator.orm.Model
        """
        builder.where_null(model.get_qualified_deleted_at_column())

        self.extend(builder)

    def remove(self, builder, model):
        """
        Remove the scope from a given query builder.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder

        :param model: The model
        :type model: orator.orm.Model
        """
        column = model.get_qualified_deleted_at_column()

        query = builder.get_query()

        wheres = []
        for where in query.wheres:
            # If the where clause is a soft delete date constraint,
            # we will remove it from the query and reset the keys
            # on the wheres. This allows the developer to include
            # deleted model in a relationship result set that is lazy loaded.
            if not self._is_soft_delete_constraint(where, column):
                wheres.append(where)

        query.wheres = wheres

    def extend(self, builder):
        """
        Extend the query builder with the needed functions.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        for extension in self._extensions:
            getattr(self, '_add_%s' % extension)(builder)

        builder.on_delete(self._on_delete)

    def _on_delete(self, builder):
        """
        The delete replacement function.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        column = self._get_deleted_at_column(builder)

        return builder.update({
            column: builder.get_model().fresh_timestamp()
        })

    def _get_deleted_at_column(self, builder):
        """
        Get the "deleted at" column for the builder.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder

        :rtype: str
        """
        if len(builder.get_query().joins) > 0:
            return builder.get_model().get_qualified_deleted_at_column()
        else:
            return builder.get_model().get_deleted_at_column()

    def _add_force_delete(self, builder):
        """
        Add the force delete extension to the builder.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        builder.macro('force_delete', self._force_delete)

    def _force_delete(self, builder):
        """
        The forece delete extension.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        return builder.get_query().delete()

    def _add_restore(self, builder):
        """
        Add the restore extension to the builder.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        builder.macro('restore', self._restore)

    def _restore(self, builder):
        """
        The restore extension.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        builder.with_trashed()

        return builder.update({
            builder.get_model().get_deleted_at_column(): None
        })

    def _add_with_trashed(self, builder):
        """
        Add the with-trashed extension to the builder.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        builder.macro('with_trashed', self._with_trashed)

    def _with_trashed(self, builder):
        """
        The with-trashed extension.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        self.remove(builder, builder.get_model())

        return builder

    def _add_only_trashed(self, builder):
        """
        Add the only-trashed extension to the builder.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        builder.macro('only_trashed', self._only_trashed)

    def _only_trashed(self, builder):
        """
        The only-trashed extension.

        :param builder: The query builder
        :type builder: orator.orm.builder.Builder
        """
        model = builder.get_model()

        self.remove(builder, model)

        builder.get_query().where_not_null(model.get_qualified_deleted_at_column())

    def _is_soft_delete_constraint(self, where, column):
        """
        Determine if the given where clause is a soft delete constraint.

        :param where: The where clause
        :type where: dict

        :param column: The column
        :type column: str

        :rtype: bool
        """
        return where['type'] == 'null' and where['column'] == column
