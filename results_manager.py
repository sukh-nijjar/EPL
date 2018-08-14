# from models_TEST import * #GOTCHA!!!!!!!!
from models import *

class ResultsValidator:
    def validate_goal_types(self, goals):
        """validates goals are integer values"""
        if all(g == None for g in goals.values()):
            return None,True
        for key,val in goals.items():
            # print("{} = {}".format(key, val))
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
        # the IF checks if team names have a value
        if teams['Home'] and teams['Away']:
            return None,True
        else:
            #otherwise team names are equal to none or are empty strings
            msg = "Team name cannot be empty"
            return msg,False

    def validate_teams_exist(self,result):
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
                                    (Result.away_team == result["Away"].lower()) &
                                    (Result.is_error == False))
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

    @staticmethod
    def display_all_results_in_DB():
        results = Result.select()
        if results.count() > 0:
            for r in results:
              print("---------------------------------------------------------------")
              print("Result_ID : {}, Errors exist? : {}, Updated? : {}, Week : {}, home = {}, away={}, {},{},{},{}".format(r.result_id,r.is_error,r.result_has_been_updated, r.week,r.home_team,r.away_team,r.home_ftg,r.home_htg,r.away_ftg,r.away_htg))
              print("---------------------------------------------------------------")
        else:
            print("-----------No results in database------------")
