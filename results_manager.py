from models_TEST import *

class ResultsValidator:
    def validate_goal_types(self, goals):
        #needs to handle empty strings don't forget!!!
        if goals not in int:
            raise TypeError("Goals must be integer values")

    def validate_goal_values(self, goals):
        """validates goals are not negative values and
            FT goals are more than or equal to HT goals"""
        if any(g < 0 for g in goals.values()):
            return False
        elif goals['FT_Home'] >= goals['HT_Home'] and goals['FT_Away'] >= goals['HT_Away']:
            return True
        else:
             return False

    def validate_team_names_present(self,teams):
        # the IF checks if team names have a value
        if teams['Home'] and teams['Away']:
            return True
        else:
            #otherwise team names are equal to none or are empty strings
            return False

    def validate_teams_exist(self,result):
        home_team = Team.select().where(Team.name == result["Home"])
        away_team = Team.select().where(Team.name == result["Away"])
        if home_team.exists() and away_team.exists():
            return True
        else:
            msg = "Please provide 2 teams"
            return msg,False

    def validate_result_is_new(self,result):
        result = Result.select().where((Result.home_team == result["Home"]) & (Result.away_team == result["Away"])
        & (Result.home_htg != None or Result.away_htg != None or Result.home_ftg != None or Result.away_ftg != None))
        if result.exists():
            return False
        else:
            return True

    def validate_home_and_away_teams_different(self,result):
        if result['Home'].lower() == result['Away'].lower():
            msg = result['Home'].title() + " cannot play themselves"
            return msg,False
        else:
            return True
