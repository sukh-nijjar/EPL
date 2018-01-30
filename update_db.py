from playhouse.migrate import *

db = SqliteDatabase("EPL.db")
migrator = SqliteMigrator(db)

#IMPORTANT - RUN SCRIPT FROM ACTIVATED VIRTUAL ENVIRONMENT

# 1st migration
# scored_field = IntegerField(default=0)
# against_field = IntegerField(default=0)
#
# migrate(
#     migrator.add_column('Team','goals_scored',scored_field),
#     migrator.add_column('Team','goals_conceded',against_field),
# )

#04/01/2018 - make goal fields accept null values
# migrate(
#     migrator.drop_not_null('Result','home_htg'),
#     migrator.drop_not_null('Result','away_htg'),
#     migrator.drop_not_null('Result','home_ftg'),
#     migrator.drop_not_null('Result','away_ftg'),
# )

#21/01/2018 - add boolean field to Result to indicated result has be updated
# result_updated_field = BooleanField(default=False)
# migrate(
#     migrator.add_column('Result','result_has_been_updated',result_updated_field),
# )
