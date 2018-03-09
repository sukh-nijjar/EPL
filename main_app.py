import csv, os, shutil, re
from collections import defaultdict
from flask import Flask, render_template, request, url_for, redirect, flash, json, jsonify
from playhouse.flask_utils import PaginatedQuery, object_list
from models import *
from operator import methodcaller, attrgetter
from playhouse.shortcuts import model_to_dict
from results_manager import ResultsValidator

#create application instance
app = Flask(__name__)

@app.before_request
def before_request():
    init_db()

@app.teardown_request
def teardown_request(exception):
    db.close()

@app.route('/')
def home():
    ResultsValidator.display_all_results_in_DB()
    feedback = None
    teams = Team.select()
    if len(teams) > 0:
        teams_in_goals_scored_order = sorted(teams, key=attrgetter('goals_scored'))
        teams_in_GD_order = sorted(teams, key=methodcaller('goal_difference'), reverse=True)
        teams_in_points_order = sorted(teams_in_GD_order, key=methodcaller('points'), reverse=True)
        return render_template('home.html', teams=teams_in_points_order)
    else:
        feedback = "There are no teams in the system. Please add some."
        return render_template('feedback.html', feedback = feedback)

@app.route('/new_team/')
def new_team():
    return render_template('createTeam.html')

@app.route('/create/', methods=['POST'])
def create_team():
    team_name_to_validate = request.form['team'].lower().strip()
    if team_name_valid(team_name_to_validate):
        try:
            Team.create(
            name = request.form['team'].lower().strip(),
            won = 0,
            drawn = 0,
            lost = 0,
            goals_scored = 0,
            goals_conceded = 0
            )
            return redirect(url_for('home'))
        except IntegrityError:
            error = 'Team already exists'
            return render_template('createTeam.html',error=error)
    else:
        error = team_name_to_validate + ' contains invalid characters'
        return render_template('createTeam.html',error=error)

@app.route('/load_data/')
def display_upload_form():
    return render_template('upload.html')

@app.route('/upload_teams/', methods=['POST'])
def perform_teams_upload():
    error = None
    invalid_rows = []
    with db.atomic() as transaction:
        try:
            with open('2017Teams.csv') as team_csv:
                csv_reader = csv.reader(team_csv)
                next(csv_reader)
                for row in csv_reader:
                    if team_name_valid(row[0]):
                        Team.create(
                        name = row[0].lower().strip(),
                        won = 0,
                        drawn = 0,
                        lost = 0,
                        goals_scored = 0,
                        goals_conceded = 0
                        )
                    else:
                        raise ValueError(row[0] + " contains invalid characters")
                return redirect(url_for('home'))

        except IOError:
            error = 'That file has not been found'
            return render_template('upload.html',error=error)
        except IntegrityError:
            error = 'IntegrityError detected'
            db.rollback()
            return render_template('upload.html',error=error)
        except ValueError as v_err:
            # print("VALUE ERORR{}".format(v_err.args))
            error = ('{} '.format(v_err.args[0]))
            db.rollback()
            return render_template('upload.html',error=error)

@app.route('/upload_results/', methods=['POST'])
def perform_results_upload():
    """
    Reads in result data from csv file. Validates each result and creates a dB
    record for valid results or writes invalid result to text file as errors.
    """
    error_MSG = None
    feedback = None
    error_found = False
    errors_list = []
    if Team.select().count() < 1:
        feedback = "Teams must be loaded before loading results"
        return render_template('feedback.html', feedback=feedback)

    try:
        with open('2017ResultsShortVersion.csv') as results_csv:
            csv_reader = csv.reader(results_csv)
            next(csv_reader)
            #introducing the db.atomic() command speeded up the process from 64 secs to 2 secs!!
            with db.atomic():
                for row in csv_reader:
                    teams = dict(Home=row[0].lower().strip(), Away=row[1].lower().strip(),Week=row[6])
                    try:
                        goals = dict(FT_Home=int(row[2]),HT_Home=int(row[4]),FT_Away=int(row[3]),HT_Away=int(row[5]))
                    except ValueError:
                        goals = dict(FT_Home=None,HT_Home=None,FT_Away=None,HT_Away=None)

                    result = result_is_valid(teams,goals)
                    if result == True:
                        Result.create(
                            home_team = teams['Home'],
                            away_team = teams['Away'],
                            home_ftg = goals['FT_Home'],
                            away_ftg = goals['FT_Away'],
                            home_htg = goals['HT_Home'],
                            away_htg = goals['HT_Away'],
                            week = teams['Week'])
                        if None not in goals.values():
                            # the result has a score therefore stats for each team need updating
                            update_team_stats(teams['Home'],teams['Away'],goals['FT_Home'],goals['FT_Away'])
                    else:
                        error_found = True
                        Result.create(
                            home_team = teams['Home'],
                            away_team = teams['Away'],
                            home_ftg = goals['FT_Home'],
                            away_ftg = goals['FT_Away'],
                            home_htg = goals['HT_Home'],
                            away_htg = goals['HT_Away'],
                            week = teams['Week'],
                            is_error = True)
                        each_error = []
                        for err in result['Errors']:
                            each_error.append(err)
                        # get result record just inserted
                        result = Result.select().order_by(Result.result_id.desc()).get()
                        #at the moment 'e' is the whole list
                        # for e in errors_list:
                        for err in each_error:
                            error = Error.create(result_id=result, description=err)
                        #get all errors for a given result
                        # for error in result.error_set:
                        #     print (error.description)

            if error_found:
                result_errors = Result.select().where(Result.is_error == True)
                return render_template('uploadErrors.html',invalid_results=result_errors)
            else:
                return redirect(url_for('view_results'))
    except IOError:
        error_MSG = 'That file has not been found'
        return render_template('upload.html',error=error)

@app.route('/enter_result/')
def enter_result():
    team_dd = Team.select().order_by(Team.name)
    if len(team_dd) > 1:
        return render_template('enterResult.html',team_dd = team_dd)
    else:
        return render_template("feedback.html", feedback = "There must be a minimum of 2 teams before a result can be added")

@app.route('/create_result/', methods=['POST'])
def create_result():
    teams = dict(Home=request.form.get('home_team'), Away=request.form.get('away_team'))
    goals = dict(FT_Home=int(request.form.get('hftg')),HT_Home=int(request.form.get('hhtg')),
                 FT_Away=int(request.form.get('aftg')),HT_Away=int(request.form.get('ahtg')))

    results_validator = ResultsValidator()

    UI_msg,new_result = results_validator.result_is_new(teams)
    if not new_result:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd)

    # check valid team(s)selected and not the default text
    UI_msg, teams_exist = results_validator.validate_teams_exist(teams)
    if not teams_exist:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd)

    # check half-time goals are not greater than full-time goals
    UI_msg, goal_totals_valid = results_validator.validate_goal_values(goals)
    if not goal_totals_valid:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd)

    # check a team is not both the home and away team - can't play themselves(!)
    UI_msg, two_different_teams = results_validator.validate_home_and_away_teams_different(teams)
    if not two_different_teams:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd)

    if new_result and teams_exist and goal_totals_valid and two_different_teams:
        Result.create(
        home_team = request.form.get('home_team'),
        away_team = request.form.get('away_team'),
        home_htg = request.form['hhtg'],
        away_htg = request.form['ahtg'],
        home_ftg = request.form['hftg'],
        away_ftg = request.form['aftg']
        )
        update_team_stats(request.form['home_team'], request.form['away_team'], int(request.form['hftg']), int(request.form['aftg']))
        return redirect(url_for('home'))

@app.route('/view_results/')
def view_results():
    feedback = None
    results = Result.select().where(Result.is_error == False)
    if len(results) > 0:
        return object_list('results.html',results,paginate_by=10)
    else:
        feedback = "No results available"
        return render_template("feedback.html", feedback = feedback)

@app.route('/delete_result/', methods=['DELETE'])
def delete_result():
    home_team = request.form['home_team'].lower()
    away_team = request.form['away_team'].lower()
    #get the teams from database whose stats will need amending due to result deletion
    home = Team.get(Team.name == home_team)
    away = Team.get(Team.name == away_team)

    result = Result.get((Result.home_team == home_team.lower()) & (Result.away_team == away_team.lower()))
    home_goals_adjustment = result.home_ftg
    away_goals_adjustment = result.away_ftg

    if result.result_type() == 'draw':
        home.drawn = Team.drawn - 1
        home.save()
        away.drawn = Team.drawn - 1
        away.save()
    elif result.result_type() == 'home win':
        home.won = Team.won - 1
        home.save()
        away.lost = Team.lost - 1
        away.save()
    else: #must be away win
        away.won = Team.won - 1
        away.save()
        home.lost = Team.lost - 1
        home.save()

    #adjust goals scored/conceded for deleted result
    update_home_for_against = Team.update(goals_scored = Team.goals_scored - home_goals_adjustment,
    goals_conceded = Team.goals_conceded - away_goals_adjustment).where(Team.team_id == home.team_id)
    update_home_for_against.execute()
    #repeat for away team
    update_away_for_against = Team.update(goals_scored = Team.goals_scored - away_goals_adjustment,
    goals_conceded = Team.goals_conceded - home_goals_adjustment).where(Team.team_id == away.team_id)
    update_away_for_against.execute()

    result.delete_instance()
    return jsonify({'done' : 'Result deleted'})

@app.route('/update_score/', methods=['PUT'])
def update_score():
    results_validator = ResultsValidator()
    teams = dict(Home=request.form['home_team'],Away=request.form['away_team'])
    goals = dict(FT_Home=int(request.form.get('hftg')),HT_Home=int(request.form.get('hhtg')),
                 FT_Away=int(request.form.get('aftg')),HT_Away=int(request.form.get('ahtg')))
    #i need to refactor out the below var = request form []...stick with the dicts now!
    home_team = request.form['home_team']
    away_team = request.form['away_team']
    home_htg = request.form['hhtg']
    away_htg = request.form['ahtg']
    home_ftg = request.form['hftg']
    away_ftg = request.form['aftg']

    #the next line holds the result before any requested update is applied to it:
    result = Result.get((Result.home_team == home_team.lower()) & (Result.away_team == away_team.lower()))
    UI_msg, goal_totals_valid = results_validator.validate_goal_values(goals)
    if goal_totals_valid:
        if result.home_ftg == None and result.home_htg == None and result.away_ftg == None and result.away_htg == None:
            print("This is the initial result for this fixture")
            update_query = Result.update(
            home_htg = home_htg,
            away_htg = away_htg,
            home_ftg = home_ftg,
            away_ftg = away_ftg
            ).where(Result.result_id == result.result_id)
            update_query.execute()
            update_team_stats(request.form['home_team'].lower(), request.form['away_team'].lower(), int(request.form['hftg']), int(request.form['aftg']))
            return jsonify({'done' : 'Initial result for this fixture created'})
        else:
            print("existing_result (the result BEFORE getting updated via the 'Edit')")
            existing_result = dict(ID = result.result_id, home_FT = result.home_ftg, home_HT = result.home_htg,
            away_HT = result.away_htg, away_FT = result.away_ftg, outcome=result.result_type())

            update_query = Result.update(
            home_htg = home_htg,
            away_htg = away_htg,
            home_ftg = home_ftg,
            away_ftg = away_ftg,
            result_has_been_updated = True
            ).where(Result.result_id == existing_result['ID'])
            update_query.execute()
            amend_team_stats(existing_result)
            return jsonify({'done' : 'Existing result updated'})
    else:
        return jsonify({'error' : UI_msg})

@app.route('/verify_resolved_results/', methods=['PUT'])
def verify():
    print("ROUTE '/verify_resolved_results/' called")
    teams = dict(Home=request.form['home_team'].lower().strip(),Away=request.form['away_team'].lower().strip())
    goals = dict(FT_Home=int(request.form.get('hftg')),HT_Home=int(request.form.get('hhtg')),
                 FT_Away=int(request.form.get('aftg')),HT_Away=int(request.form.get('ahtg')))

    result_to_verify = Result.get(Result.result_id == int(request.form['resid']))

    update_query = Result.update(
    home_team = teams['Home'],
    away_team = teams['Away'],
    home_ftg = goals['FT_Home'],
    away_ftg = goals['FT_Away'],
    home_htg = goals['HT_Home'],
    away_htg = goals['HT_Away']
    ).where(Result.result_id == result_to_verify.result_id)
    update_query.execute()

    result = result_is_valid(teams,goals,ignore_result_is_new=True)
    if result == True:
        update_query = Result.update(is_error = False)
        update_query.execute()
        update_team_stats(teams['Home'],teams['Away'],goals['FT_Home'],goals['FT_Away'])
    else:
        print("Need to delete errors that are no longer relevant")
        dq = Error.delete()
        #delete the error description that matches the resolved error ... hmmm OR
        #have a error column boolean that can be deleted when resolved = true ... hmmm

    return jsonify({'done' : 'Re-validation complete'})
    # return redirect(url_for('display_upload_errors'))

@app.route('/delete_all_results/')
def delete_all_results():
    """deletes all results and resets teams stats to no games played"""
    delete_query = Error.delete()
    delete_query.execute()
    delete_query = Result.delete()
    delete_query.execute()
    reset_teams_query = Team.update(won = 0,drawn = 0,lost = 0,
    goals_scored = 0,goals_conceded = 0)
    reset_teams_query.execute()
    # if os.path.exists('result_upload_errors.txt'):
    #     os.remove('result_upload_errors.txt')
    return redirect(url_for('home'))

@app.route('/delete_all_teams/', methods=['POST'])
def delete_all_teams():
    """deleting teams also causes all results to be deleted
    """
    delete_query = Team.delete()
    delete_query.execute()
    delete_query = Result.delete()
    delete_query.execute()
    if os.path.exists('result_upload_errors.csv'):
        os.remove('result_upload_errors.csv')
    return redirect(url_for('home'))

@app.route('/team_drill_down/<team>', methods=['GET'])
def drill_down(team):
    team=Team.get(Team.name == team)
    print("{} team id is {}, wins = {}".format(team.name, team.team_id, team.won))
    results=Result.select().where((Result.away_team == team.name) | (Result.home_team == team.name))
    # object_list method creates a PaginatedQuery object calls get_object_list
    return object_list('teamDetails.html',results,paginate_by=9,team=team)

@app.route('/get_chart_data', methods=['GET'])
def ReturnChartData():
    team_arg = request.args.get('team')
    print("{}".format(request.args.get('team')))
    # print("Called 'ReturnChartData', team = {}".format(team))
    print("Called 'ReturnChartData'")
    team=Team.get(Team.name == team_arg.lower())
    print("{} team id is {}".format(team.name, team.team_id))
    return jsonify({'won' : team.won,'drawn' : team.drawn, 'lost'  : team.lost})

@app.route('/upload_errors/', methods=['GET'])
def display_upload_errors():
    result_errors = Result.select().where(Result.is_error == True)
    if len(result_errors) > 0:
        return render_template('uploadErrors.html',invalid_results=result_errors)
    else:
        return render_template('uploadErrors.html',feedback = "No errors to report")

def create_dd_of_ints(required_range):
    dd = []
    for i in range(required_range):
        dd.append(i)
    return dd

#IF ROW IS VALID REFACTORED START--------------------------------------------
def result_is_valid(teams,goals,**kwargs):
    res = defaultdict(list,{**teams, **goals})
    results_validator = ResultsValidator()
    UI_msg, goal_types_valid = results_validator.validate_goal_types(goals)
    if not goal_types_valid:
        res['Errors'].append(UI_msg)
    print("Outcome = {}".format(goal_types_valid))
    # print("{} : message = {}. Outcome = {}".format(res, UI_msg, goal_types_valid))
    UI_msg, goal_values_valid = results_validator.validate_goal_values(goals)
    if not goal_values_valid:
        res['Errors'].append(UI_msg)
    print("Outcome = {}".format(goal_values_valid))

    UI_msg, team_names_provided = results_validator.validate_team_names_present(teams)
    if not team_names_provided:
        res['Errors'].append(UI_msg)
    print("Outcome = {}".format(team_names_provided))

    UI_msg, teams_exist = results_validator.validate_teams_exist(teams)
    if not teams_exist:
        res['Errors'].append(UI_msg)
    print("Outcome = {}".format(teams_exist))

    UI_msg, different_teams = results_validator.validate_home_and_away_teams_different(teams)
    if not different_teams:
        res['Errors'].append(UI_msg)
    print("Outcome = {}".format(different_teams))

    #this validation needs to skipped when result is being re-validated after upload
    if 'ignore_result_is_new' in kwargs:
        UI_msg = None
        new_result = True
        print("Ignored so Outcome = {}".format(new_result))
    else:
        UI_msg, new_result = results_validator.result_is_new(teams)

    if not new_result:
        res['Errors'].append(UI_msg)
    print("Outcome = {}".format(new_result))

    if goal_types_valid and goal_values_valid and team_names_provided and teams_exist and different_teams and new_result:
        print("Valid result - {}".format(res))
        return True
    else:
        print("ERROR in {}".format(res))
        return res
#IF ROW IS VALID REFACTORED END--------------------------------------------------

def team_name_valid(team_name):
    match = re.search(r'^[a-z A-Z 0-9 &]+\Z', team_name)
    if match:
        return True
    else:
        return False

#TO-D0 - PASS IN RESULT OBJECT AND result_type() METHOD
def update_team_stats(home_team, away_team, goals_scored_by_home_team, goals_scored_by_away_team):
    """After a result has been created this method updates the matches
    won, drawn, lost, goals scored and conceded stats for each team in the match."""
    if goals_scored_by_home_team > goals_scored_by_away_team:
        # home win
        update_query = Team.update(
        won = Team.won + 1,
        goals_scored = Team.goals_scored + goals_scored_by_home_team,
        goals_conceded = Team.goals_conceded + goals_scored_by_away_team
        ).where(Team.name == home_team)
        update_query.execute()
        update_query = Team.update(
        lost = Team.lost + 1,
        goals_scored = Team.goals_scored + goals_scored_by_away_team,
        goals_conceded = Team.goals_conceded + goals_scored_by_home_team
        ).where(Team.name == away_team)
        update_query.execute()
    elif goals_scored_by_home_team < goals_scored_by_away_team:
        # away win
        update_query = Team.update(won = Team.won + 1,
        goals_scored = Team.goals_scored + goals_scored_by_away_team,
        goals_conceded = Team.goals_conceded + goals_scored_by_home_team
        ).where(Team.name == away_team)
        update_query.execute()
        update_query = Team.update(lost = Team.lost + 1,
        goals_scored = Team.goals_scored + goals_scored_by_home_team,
        goals_conceded = Team.goals_conceded + goals_scored_by_away_team
        ).where(Team.name == home_team)
        update_query.execute()
    else:
        # draw
        update_query = Team.update(drawn = Team.drawn + 1,
        goals_scored = Team.goals_scored + goals_scored_by_home_team,
        goals_conceded = Team.goals_conceded + goals_scored_by_away_team
        ).where(Team.name << [home_team, away_team])
        update_query.execute()

def amend_team_stats(previous_result):
    """After a result has been updated this method amends the matches
    won, drawn, lost, goals scored and conceded stats for each team in the match."""
    print ("previous result = {} ".format(previous_result))
    current_result = Result.get(Result.result_id == previous_result['ID'])
    home_team = Team.get(Team.name == current_result.home_team)
    away_team = Team.get(Team.name == current_result.away_team)
    print("DB result type = {}".format(current_result.result_type()))

    if current_result.result_has_been_updated:
        scored_change = current_result.home_ftg - previous_result['home_FT']
        conceded_change = current_result.away_ftg - previous_result['away_FT']
        update_query = Team.update(goals_scored = Team.goals_scored + scored_change,
        goals_conceded = Team.goals_conceded + conceded_change
        ).where(Team.name == home_team.name)
        update_query.execute()
        #repeat for away team
        scored_change = current_result.away_ftg - previous_result['away_FT']
        conceded_change = current_result.home_ftg - previous_result['home_FT']
        update_query = Team.update(goals_scored = Team.goals_scored + scored_change,
        goals_conceded = Team.goals_conceded + conceded_change
        ).where(Team.name == away_team.name)
        update_query.execute()
        update_query = Result.update(result_has_been_updated=False).where(Result.result_id == current_result.result_id)
        update_query.execute()

    if previous_result['outcome'] == 'draw':
        if current_result.result_type() == 'home win':
            update_query = Team.update(won = Team.won + 1,
            drawn = Team.drawn - 1).where(Team.name == home_team.name)
            update_query.execute()
            update_query = Team.update(lost = Team.lost + 1,
            drawn = Team.drawn - 1).where(Team.name == away_team.name)
            update_query.execute()
        if current_result.result_type() == 'away win':
            update_query = Team.update(won = Team.won + 1,
            drawn = Team.drawn - 1).where(Team.name == away_team.name)
            update_query.execute()
            update_query = Team.update(lost = Team.lost + 1,
            drawn = Team.drawn - 1).where(Team.name == home_team.name)
            update_query.execute()

    if previous_result['outcome'] == 'home win':
        if current_result.result_type() == 'draw':
            update_query = Team.update(won = Team.won - 1,
            drawn = Team.drawn + 1).where(Team.name == home_team.name)
            update_query.execute()
            update_query = Team.update(lost = Team.lost - 1,
            drawn = Team.drawn + 1).where(Team.name == away_team.name)
            update_query.execute()
        if current_result.result_type() == 'away win':
            update_query = Team.update(won = Team.won - 1,
            lost = Team.lost + 1).where(Team.name == home_team.name)
            update_query.execute()
            update_query = Team.update(lost = Team.lost - 1,
            won = Team.won + 1).where(Team.name == away_team.name)
            update_query.execute()

    if previous_result['outcome'] == 'away win':
        if current_result.result_type() == 'draw':
            update_query = Team.update(won = Team.won - 1,
            drawn = Team.drawn + 1).where(Team.name == away_team.name)
            update_query.execute()
            update_query = Team.update(lost = Team.lost - 1,
            drawn = Team.drawn + 1).where(Team.name == home_team.name)
            update_query.execute()
        if current_result.result_type() == 'home win':
            update_query = Team.update(won = Team.won + 1,
            lost = Team.lost - 1).where(Team.name == home_team.name)
            update_query.execute()
            update_query = Team.update(lost = Team.lost + 1,
            won = Team.won - 1).where(Team.name == away_team.name)
            update_query.execute()

#debug helpers
def display_all_error_in_DB():
    errors = Error.select()
    for e in errors:
      print("---------------------------------------------------------------")
      print("Errors_ID : {}, Result_ID : {}, Desc : {}".format(e.error_id,e.result_id,e.description))
      print("---------------------------------------------------------------")

def display_all_team_in_DB():
    teams = Team.select()
    for t in teams:
      print("---------------------------------------------------------------")
      print("Team_ID : {}, Team : {}".format(t.team_id,t.name))
      print("---------------------------------------------------------------")

def display_results_and_errors_in_DB(r_id):
    print("**param in = {}".format(r_id))
    result = Error.select().join(Result).where(Result.result_id == r_id)
    for error in result:
        print("result_id {} and errors : {}".format(error.result_id,error.description))


#end debug helpers

if __name__ == '__main__':
    app.secret_key ='sum fink' #THIS SHOULD BE IN CONFIG - SECRET_KEY = 'string'
    app.send_file_max_age_default = 0
    app.run(debug=True)
