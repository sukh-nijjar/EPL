# from models_TEST import * #GOTCHA!!!!!!!!
from models import *

class ResultsValidator:
    def validate_goal_types(self, goals):
        """validates goals are integer values"""
        if all(g == None for g in goals.values()):
            return None,True
        for key,val in goals.items():
            if isinstance(val, int):
                return None,True
            else:
                msg = "Goals must be integer values"
                return msg,False


    def validate_goal_values(self, goals):
        """validates goals are not negative values and
            FT goals are more than or equal to HT goals"""
        #TO DO : Negative goal values MASKS ELSE CLAUSE ERROR
        if all(g == None for g in goals.values()):
            return None,True
        if any(g < 0 for g in goals.values()):
            msg = "Negative values not allowed"
            return msg,False
        elif goals['FT_Home'] >= goals['HT_Home'] and goals['FT_Away'] >= goals['HT_Away']:
            return None,True
        else:
            msg = "Full time goals cannot be less than Half time goals"
            return msg,False

    def validate_team_names_present(self,teams):
        """validates team names have been supplied. Note this is used for results upload validation
           and not currently being used when result submited from UI 'Enter result' form"""
        if teams['Home'] and teams['Away']:
            return None,True
        else:
            #otherwise team names are equal to none or are empty strings
            msg = "Team name cannot be empty"
            return msg,False

    def validate_teams_exist(self,result):
        """validates the teams specified in the result are actual teams
           (e.g. exist in the database)"""
        home_team = Team.select().where(Team.name == result["Home"].lower())
        away_team = Team.select().where(Team.name == result["Away"].lower())
        if home_team.exists() and away_team.exists():
            return None,True
        else:
            msg = "Please provide 2 valid teams"
            return msg,False

    def result_is_new(self,result):
        """determines if a record already exists for the
           combination of the home and away teams (could be either a result or fixture)"""
        res = Result.select().where((Result.home_team == result["Home"].lower()) &
                                    (Result.away_team == result["Away"].lower())) #&
                                    #(Result.is_error == False))
        if res.exists():
            msg = "Duplicate result : A result for " + result["Home"].title() + " vs " + result["Away"].title() + " already exists"
            return msg,False
        else:
            #it's a new result
            return None,True

    def validate_home_and_away_teams_different(self,result):
        """validates the home and away teams are different, for example
           a match cannot be Arsenal vs Arsenal"""
        if result['Home'].lower() == result['Away'].lower():
            msg = result['Home'].title() + " cannot play themselves"
            return msg,False
        else:
            return None,True
