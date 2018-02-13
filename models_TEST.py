from peewee import *

db = SqliteDatabase("TEST_DATABASE.db") #in real app this would come from config, not hard coded

# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will automatically
# use the correct storage.
class BaseModel(Model):
    class Meta:
        database = db

class Team(BaseModel):
    team_id = PrimaryKeyField()
    name =  CharField(unique=True) #name must be unique in the table
    won = IntegerField()
    drawn = IntegerField()
    lost = IntegerField()

class Result(BaseModel):
    result_id = PrimaryKeyField()
    home_team = CharField()
    away_team = CharField()
    home_htg = IntegerField(null=True)
    away_htg = IntegerField(null=True)
    home_ftg = IntegerField(null=True)
    away_ftg = IntegerField(null=True)

def init_db():
    db.connect()
    db.create_tables([Team,Result], safe = True)
