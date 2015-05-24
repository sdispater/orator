# -*- coding: utf-8 -*-

from cleo import Application
from ..version import VERSION
from .migrations import (
    InstallCommand, MigrateCommand,
    MigrateMakeCommand, RollbackCommand,
    StatusCommand, ResetCommand
)

application = Application('Orator', VERSION)

application.add(InstallCommand())
application.add(MigrateCommand())
application.add(MigrateMakeCommand())
application.add(RollbackCommand())
application.add(StatusCommand())
application.add(ResetCommand())
