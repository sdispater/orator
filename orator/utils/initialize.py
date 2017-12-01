import orator
import yaml
from orator import Model, DatabaseManager
from orator.migrations import Migrator, DatabaseMigrationRepository

def initialize(config_file='orator.yml', run_migrations=True, migrations_dir="migrations"):
	with open(config_file) as file:
		config = yaml.load(file)
	
	db = DatabaseManager(config['databases'])
	Model.set_connection_resolver(db)

	if run_migrations:
		repository = DatabaseMigrationRepository(db, 'migrations')
		migrator = Migrator(repository, db)
		if not migrator.repository_exists():
			repository.create_repository()

		migrator.run(migrations_dir)