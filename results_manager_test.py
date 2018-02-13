import models_TEST
import unittest
from results_manager import ResultsValidator

rv = ResultsValidator()

class TestDatabase(unittest.TestCase):
    def setUp(self):
        models_TEST.init_db()
        if models_TEST.Team.select().count() < 1:
            teams_data_source = [
            {'name': 'Manchester City', 'won': 22, 'drawn': 3, 'lost': 1},
            {'name': 'Manchester United', 'won': 17, 'drawn': 5, 'lost': 4},
            {'name': 'Spurs', 'won': 14, 'drawn': 7, 'lost': 5},
            {'name': 'Bournemouth', 'won': 8, 'drawn': 7, 'lost': 11},
            {'name': 'Brighton', 'won': 6, 'drawn': 9, 'lost': 11},
            {'name': 'Burnley', 'won': 9, 'drawn': 9, 'lost': 8},
            {'name': 'Arsenal', 'won': 13, 'drawn': 6, 'lost': 7}]
            models_TEST.Team.insert_many(teams_data_source).execute()

        if models_TEST.Result.select().count() < 1:
            results_data_source = [
            {'home_team': 'Manchester City', 'away_team': 'Bournemouth', 'home_htg': 1,
                          'away_htg': 1, 'home_ftg': 1, 'away_ftg': 1},
            {'home_team': 'Burnley', 'away_team': 'Bournemouth', 'home_htg': 0,
                          'away_htg': 1, 'home_ftg': 0, 'away_ftg': 2},
            {'home_team': 'Burnley', 'away_team': 'Arsenal', 'home_htg': 2,
                          'away_htg': 1, 'home_ftg': 3, 'away_ftg': 1}]
            models_TEST.Result.insert_many(results_data_source).execute()

    def tearDown(self):
        models_TEST.db.close()

    def test_teams_exist(self):
        """
        Test that a team exists
        """
        message, outcome = rv.validate_teams_exist({'Home':'AFC','Away':'BFC','FT_Home':2,
                                                 'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)

        message, outcome = rv.validate_teams_exist({'Home':'Arsenal','Away':'BFC','FT_Home':2,
                                                 'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)

        message, outcome = rv.validate_teams_exist({'Home':'AFC','Away':'Arsenal','FT_Home':2,
                                                 'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)

        self.assertTrue(rv.validate_teams_exist({'Home':'Brighton','Away':'Manchester City','FT_Home':2,
                                                 'HT_Home':1,'FT_Away':3,'HT_Away':3}))

    def test_validate_result_not_duplicate(self):
        """
        test a result doesn't already exist between the two teams
        for the same home and away combination
        """
        self.assertFalse(rv.validate_result_is_new({'Home':'Manchester City','Away':'Bournemouth','FT_Home':2,
                                                 'HT_Home':1,'FT_Away':3,'HT_Away':3}))
        self.assertTrue(rv.validate_result_is_new({'Home':'Manchester City','Away':'Arsenal','FT_Home':2,
                                                 'HT_Home':1,'FT_Away':3,'HT_Away':3}))

class TestResultsValidator(unittest.TestCase):
    def test_goals_are_integers(self):
        """goals must be specified as integers"""
        self.assertRaises(TypeError, rv.validate_goal_types, [1,2,3,5])

    def test_FTGoals_not_less_than_HTGoals_and_postive_number(self):
        """ensure a team's full time goals are not less than their half time goals"""
        outcome = rv.validate_goal_values({'FT_Home':1,'HT_Home':1,'FT_Away':0,'HT_Away':3})
        self.assertFalse(outcome)
        outcome = rv.validate_goal_values({'FT_Home':-1,'HT_Home':1,'FT_Away':0,'HT_Away':0})
        self.assertFalse(outcome)
        outcome = rv.validate_goal_values({'FT_Home':0,'HT_Home':-1,'FT_Away':-1,'HT_Away':-2})
        self.assertFalse(outcome)
        outcome = rv.validate_goal_values({'FT_Home':2,'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertTrue(outcome)
        outcome = rv.validate_goal_values({'FT_Home':0,'HT_Home':0,'FT_Away':0,'HT_Away':0})
        self.assertTrue(outcome)
        outcome = rv.validate_goal_values({'FT_Home':1,'HT_Home':0,'FT_Away':1,'HT_Away':0})
        self.assertTrue(outcome)

    def test_team_name_are_present(self):
        """ensure the team names are present"""
        outcome = rv.validate_team_names_present({'Home':'AFC','Away':'BFC','FT_Home':2,
                                          'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertTrue(outcome)
        outcome = rv.validate_team_names_present({'Home':'','Away':'BFC','FT_Home':2,
                                          'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)
        outcome = rv.validate_team_names_present({'Home':'AFC','Away':'','FT_Home':2,
                                          'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)
        outcome = rv.validate_team_names_present({'Home':None,'Away':'','FT_Home':2,
                                          'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)
        outcome = rv.validate_team_names_present({'Home':'AFC','Away':None,'FT_Home':2,
                                          'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)
        outcome = rv.validate_team_names_present({'Home':None,'Away':None,'FT_Home':2,
                                          'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)
        outcome = rv.validate_team_names_present({'Home':'','Away':'','FT_Home':2,
                                          'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)

    def test_home_and_away_teams_are_different(self):
        """ensure a team is not playing itself(!)"""
        self.assertTrue(rv.validate_home_and_away_teams_different({'Home':'Manchester City','Away':'Arsenal','FT_Home':2,
                                                                    'HT_Home':1,'FT_Away':3,'HT_Away':3}))
        message, outcome = rv.validate_home_and_away_teams_different({'Home':'ABC','Away':'AbC','FT_Home':2,
                                                                    'HT_Home':1,'FT_Away':3,'HT_Away':3})
        self.assertFalse(outcome)

if __name__ == "__main__":
    unittest.main()
