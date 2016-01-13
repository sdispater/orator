# -*- coding: utf-8 -*-

from cleo import Application
from ..version import VERSION

application = Application('Orator', VERSION, complete=True)

# Migrations
from .migrations import (
    InstallCommand, MigrateCommand,
    MigrateMakeCommand, RollbackCommand,
    StatusCommand, ResetCommand, RefreshCommand
)

application.add(InstallCommand())
application.add(MigrateCommand())
application.add(MigrateMakeCommand())
application.add(RollbackCommand())
application.add(StatusCommand())
application.add(ResetCommand())
application.add(RefreshCommand())

# Seeds
from .seeds import SeedersMakeCommand, SeedCommand

application.add(SeedersMakeCommand())
application.add(SeedCommand())

# Models
from .models import ModelMakeCommand

application.add(ModelMakeCommand())
