from peewee import *

db = SqliteDatabase("EPL.db") #in real app this would come from config, not hard coded

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
    goals_scored = IntegerField()
    goals_conceded = IntegerField()

    def points(self):
        """Returns the number of points a team has based on
           games won, drawn and lost"""
        return (self.won*3) + self.drawn

    def games_played(self):
        """returns the total number of matches played
            by the team"""
        return self.won + self.drawn + self.lost

    def update_goal_stats(self,scored,conceded):
        print(scored,conceded)
        self.goals_scored += scored
        self.goals_conceded += conceded

    #class Meta:
        #order_by = ('lost',)

class Result(BaseModel):
    result_id = PrimaryKeyField()
    home_team = CharField()
    away_team = CharField()
    home_htg = IntegerField()
    away_htg = IntegerField()
    home_ftg = IntegerField()
    away_ftg = IntegerField()

def init_db():
    db.connect()
    db.create_tables([Team, Result], safe = True)
