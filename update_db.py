from playhouse.migrate import *

db = SqliteDatabase("EPL.db")
migrator = SqliteMigrator(db)

scored_field = IntegerField(default=0)
against_field = IntegerField(default=0)

migrate(
    migrator.add_column('Team','goals_scored',scored_field),
    migrator.add_column('Team','goals_conceded',against_field),
)
