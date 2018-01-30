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

    def goal_difference(self):
        """returns the goals difference for the team"""
        return self.goals_scored - self.goals_conceded

    def win_rate(self):
        """returns the percentage of games won by a team"""
        return round((100/self.games_played())*self.won)

    def draw_rate(self):
        """returns the percentage of games drawn by a team"""
        return round((100/self.games_played())*self.drawn)

    def loss_rate(self):
        """returns the percentage of games lost by a team"""
        return round((100/self.games_played())*self.lost)

    # class Meta:
    #     order_by = ('won',)

class Result(BaseModel):
    result_id = PrimaryKeyField()
    home_team = CharField()
    away_team = CharField()
    home_htg = IntegerField(null=True)
    away_htg = IntegerField(null=True)
    home_ftg = IntegerField(null=True)
    away_ftg = IntegerField(null=True)
    result_has_been_updated = BooleanField(default=False)

    def result_type(self):
        """returns the result type which is either home win,
            away win_rate, draw or no result"""
        if self.home_ftg > self.away_ftg:
            return 'home win'
        elif self.home_ftg < self.away_ftg:
            return 'away win'
        else:
            return 'draw'

def init_db():
    db.connect()
    db.create_tables([Team, Result], safe = True)
