import csv, math, os, shutil, re
from collections import defaultdict
from domain import TeamPosition
from flask import Flask, Markup, render_template, request, url_for, redirect, flash, json, jsonify, g
from playhouse.flask_utils import PaginatedQuery, object_list
from models import *
from operator import methodcaller, attrgetter
from playhouse.shortcuts import model_to_dict
from results_manager import ResultsValidator
from statistics import mean

#create application instance
app = Flask(__name__)

@app.before_request
def before_request():
    init_db()
    # get the current status of which data exists
    # There are 3 possibilities :
    # no data in system, team data available or both team and results data is available.
    g.state = get_system_state()

@app.teardown_request
def teardown_request(exception):
    db.close()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',feedback="Results not available for week requested"),404

@app.route('/')
def landing_page():
    state = g.get('state',None)
    return render_template('landing_page.html',state=state)

# @app.route('/')
@app.route('/league/')
def home():
    """ display the league table showing teams ordered by points in descending order
    """
    state = g.get('state',None)
    feedback = None
    teams = Team.select()
    if len(teams) > 0:
        teams_in_goals_scored_order = sorted(teams, key=attrgetter('goals_scored'))
        teams_in_GD_order = sorted(teams, key=methodcaller('goal_difference'), reverse=True)
        teams_in_points_order = sorted(teams_in_GD_order, key=methodcaller('points'), reverse=True)
        return render_template('home.html', teams=teams_in_points_order,state=state)
    else:
        feedback = "There are no teams in the system. Please add some."
        return render_template('feedback.html', feedback = feedback,state=state)

@app.route('/new_team/')
def new_team():
    state = g.get('state',None)
    return render_template('createTeam.html',state=state)

@app.route('/create/', methods=['POST'])
def create_team():
    """If validation passes creates a team submitted by input form. If validation fails
       a message is displayed informing what the issue is.
    """
    state = g.get('state',None)
    if Team.select().count() >= 20:
        error = '20 teams in league - unable to add any more'
        return render_template('createTeam.html',error=error,state=state)

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
            error = team_name_to_validate.upper() + ' already exists. Cannot be added twice.'
            return render_template('createTeam.html',error=error,state=state)
    else:
        error = team_name_to_validate + ' contains invalid characters'
        return render_template('createTeam.html',error=error,state=state)

@app.route('/load_data/')
def display_upload_form():
    """display view to load data (csv files)"""
    state = g.get('state',None)
    return render_template('upload.html',state=state)

@app.route('/upload_teams/', methods=['POST'])
def perform_teams_upload():
    """creates teams via upload of csv as long as there are
       less than the allowed maximum 20 teams and any team in the csv doesn't
       already exist in the database. If an error is found no more rows are proceesed and
       the operation is rolled back"""
    existing_teams = []
    state = g.get('state',None)
    error = None
    invalid_rows = []
    teams = Team.select(Team)
    for team in teams:
        existing_teams.append(team.name.title())
    if (teams.count() > 0) & (teams.count() < 19):
        error = Markup('Upload teams is a way to create teams in bulk - a precondition is there should not be any teams already in the system. '
        + '<br>Currently the following teams have been detected:' + '<br>' +  ', '.join(existing_teams)
        + '<br>Please delete these using <i>Delete teams</i> option and then re-try upload teams')
        return render_template('upload.html',error=error,state=state)
    if teams.count() >= 20:
        error = '20 teams in league - unable to add any more'
        return render_template('upload.html',error=error,state=state)

    with db.atomic() as transaction:
        try:
            with open('2017Teams.csv') as team_csv:
            # with open('2017TeamsWithErrors.csv') as team_csv:
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
                        raise ValueError("Error found in row " + str(csv_reader.line_num) + " : " + row[0] + " contains invalid characters")
                return redirect(url_for('home'))

        except IOError:
            error = 'Specified upload file has not been found'
            return render_template('upload.html',error=error,state=state)
        except IntegrityError:
            error = row[0].upper() + ' already exists. Cannot be added twice.'
            db.rollback()
            return render_template('upload.html',error=error,state=state)
        except ValueError as v_err:
            error = ('{} '.format(v_err.args[0]))
            db.rollback()
            return render_template('upload.html',error=error,state=state)

@app.route('/upload_results/', methods=['POST'])
def perform_results_upload():
    """
    Reads in result data from csv file. Validates each result and creates a dB
    record for valid results or creates an invalid result dB record (if a data error is detected).
    If the csv contains missing values or invalid characters for goals and/or week data the row is
    stored as a fixture which means it can be edited from the UI
    """
    state = g.get('state',None)
    feedback = None
    error_found = False
    errors_list = []
    if request.form['file_selected']=="":
        return render_template('feedback.html', feedback='Please select a file to load',state=state)

    if Team.select().count() < 1:
        feedback = "Teams must be loaded before loading results"
        return render_template('upload.html', feedback=feedback,state=state)

    if request.form['file_selected'] == 'validFile':
        file_to_load = '2017Results.csv'
    else:
        file_to_load = '2017ResultsWithErrors.csv'

    try:
        with open(file_to_load) as results_csv:
            csv_reader = csv.reader(results_csv)
            next(csv_reader)
            #introducing the db.atomic() command speeded up the process from 64 secs to an eyeblink!!
            with db.atomic():
                for row in csv_reader:
                    teams = dict(Home=row[0].lower().strip(), Away=row[1].lower().strip())
                    try:
                        goals = dict(FT_Home=int(row[2]),HT_Home=int(row[4]),FT_Away=int(row[3]),HT_Away=int(row[5]),Week=int(row[6]))
                    except (ValueError,IndexError) as err:
                        goals = dict(FT_Home=None,HT_Home=None,FT_Away=None,HT_Away=None,Week=None)

                    result = result_is_valid(teams,goals)
                    if result == True:
                        Result.create(
                            home_team = teams['Home'],
                            away_team = teams['Away'],
                            home_ftg = goals['FT_Home'],
                            away_ftg = goals['FT_Away'],
                            home_htg = goals['HT_Home'],
                            away_htg = goals['HT_Away'],
                            week = goals['Week'])
                        #check if any of the values in the goals dict has a None value (or not)
                        if None not in goals.values():
                            # the result has a score therefore stats for each team need updating
                            update_team_stats(teams['Home'],teams['Away'],goals['FT_Home'],goals['FT_Away'])
                        else:
                            # goal and/or week values are None therefore the match status is updated to a 'fixture' (from the default status of 'result')
                            last_inserted = Result.select().order_by(Result.result_id.desc()).get()
                            update_query = Result.update(match_status = 'fixture').where(Result.result_id == last_inserted)
                            update_query.execute()
                    else:
                        error_found = True
                        Result.create(
                            home_team = teams['Home'],
                            away_team = teams['Away'],
                            home_ftg = goals['FT_Home'],
                            away_ftg = goals['FT_Away'],
                            home_htg = goals['HT_Home'],
                            away_htg = goals['HT_Away'],
                            week = goals['Week'],
                            is_error = True)
                        each_error = []
                        for err in result['Errors']:
                            each_error.append(err)
                        # get result record just inserted
                        result = Result.select().order_by(Result.result_id.desc()).get()
                        for err in each_error:
                            error = Error.create(result_id=result, description=err)

            if error_found:
                result_errors = Result.select().where(Result.is_error == True)
                state = "ERRORS EXIST";
                return render_template('uploadErrors.html',invalid_results=result_errors,state=state)
            else:
                return redirect(url_for('home'))
    except IOError:
        error = 'Specified upload file has not been found'
        return render_template('upload.html',error=error,state=state)

@app.route('/enter_result/')
def enter_result():
    """display view with form to enter results data"""
    state = g.get('state',None)
    team_dd = Team.select().order_by(Team.name)
    if len(team_dd) > 1:
        return render_template('enterResult.html',team_dd = team_dd,state=state)
    else:
        return render_template("enterResult.html", feedback = "There must be a minimum of 2 teams before a result can be added",state=state)

@app.route('/create_result/', methods=['POST'])
def create_result():
    """If validation passes creates result from data submitted by input form,
       if validation fails a message is displayed informing what the issue is.
       When a result is created stats (matches won, drawn, lost, goals scored and conceded)
       for the teams involved are updated which in turn updates the league table"""
    state = g.get('state',None)
    teams = dict(Home=request.form.get('home_team'), Away=request.form.get('away_team'))
    try:
        goals = dict(FT_Home=int(request.form.get('hftg')),HT_Home=int(request.form.get('hhtg')),
                     FT_Away=int(request.form.get('aftg')),HT_Away=int(request.form.get('ahtg')))
    except ValueError:
        team_dd = Team.select().order_by(Team.name)
        error = "Only whole numbers (zero or above) can be entered for goals!"
        return render_template('enterResult.html', error = error, team_dd = team_dd,teams=teams,state=state)

    results_validator = ResultsValidator()

    UI_msg,new_result = results_validator.result_is_new(teams)
    if not new_result:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd,teams=teams,state=state)

    # check valid team(s)selected and not the default text
    UI_msg, teams_exist = results_validator.validate_teams_exist(teams)
    if not teams_exist:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd,teams=teams,state=state)

    # check half-time goals are not greater than full-time goals
    UI_msg, goal_totals_valid = results_validator.validate_goal_values(goals)
    if not goal_totals_valid:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd,teams=teams,state=state)

    # check a team is not both the home and away team - can't play themselves(!)
    UI_msg, two_different_teams = results_validator.validate_home_and_away_teams_different(teams)
    if not two_different_teams:
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = UI_msg, team_dd = team_dd,teams=teams,state=state)

    if new_result and teams_exist and goal_totals_valid and two_different_teams:
        #get last inserted for determining week value
        result_count = Result.select().count()
        if result_count > 0:
            last_inserted = Result.select(Result.result_id).order_by(Result.result_id.desc()).get()

        week = set_week(last_inserted) if result_count > 0 else 1

        Result.create(
        home_team = request.form.get('home_team'),
        away_team = request.form.get('away_team'),
        home_htg = request.form['hhtg'],
        away_htg = request.form['ahtg'],
        home_ftg = request.form['hftg'],
        away_ftg = request.form['aftg'],
        week = week
        )
        update_team_stats(request.form['home_team'], request.form['away_team'], int(request.form['hftg']), int(request.form['aftg']))
        return redirect(url_for('home'))

@app.route('/view_results/')
def view_results():
    """Display valid results if any exist otherwise present message informing no results are available for display"""
    state = g.get('state',None)
    feedback = None
    results = Result.select().where(Result.is_error == False)
    if len(results) > 0:
        return object_list('results.html',results,paginate_by=10,state=state)
    else:
        feedback = "No results available"
        return render_template("feedback.html", feedback = feedback,state=state)

@app.route('/delete_result/', methods=['DELETE'])
def delete_result():
    """Deletes a specific result submitted by input form and update each teams stats
       (matches won, drawn, lost, goals scored and conceded) to reflect data deletion"""
    result_to_delete = Result.get(Result.result_id == int(request.form['resid']))
    #get the teams from database whose stats will need amending due to result deletion
    home = Team.get(Team.name == result_to_delete.home_team)
    away = Team.get(Team.name == result_to_delete.away_team)

    home_goals_adjustment = result_to_delete.home_ftg
    away_goals_adjustment = result_to_delete.away_ftg

    if result_to_delete.result_type() == 'draw':
        home.drawn = Team.drawn - 1
        home.save()
        away.drawn = Team.drawn - 1
        away.save()
    elif result_to_delete.result_type() == 'home win':
        home.won = Team.won - 1
        home.save()
        away.lost = Team.lost - 1
        away.save()
    else: #must be away win to be deleted
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

    result_to_delete.delete_instance(recursive=True)
    return jsonify({'done' : 'Result deleted and league table updated'})

@app.route('/delete_erroneous_result/', methods=['DELETE'])
def delete_erroneous_result():
    """Deletes a result which has been flagged as having 1 or more errors.
	   Both the result and associated error(s) are deleted from the database"""
    erroneous_result_to_delete = Result.get(Result.result_id == int(request.form['resid']))
    erroneous_result_to_delete.delete_instance(recursive=True)
    return jsonify({'done' : 'Erroneous Result deleted', 'path' : '/upload_errors/'})

@app.route('/update_score/', methods=['PUT'])
def update_score():
    """Updates a result record, team stats (matches won, drawn, lost, goals scored and conceded)
       and the league table when a result/fixture is edited"""
    results_validator = ResultsValidator()
    teams = dict(Home=request.form['home_team'].lower(),Away=request.form['away_team'].lower())
    try:
        goals = dict(FT_Home=int(request.form.get('hftg')),HT_Home=int(request.form.get('hhtg')),
                     FT_Away=int(request.form.get('aftg')),HT_Away=int(request.form.get('ahtg')))
    except ValueError:
        return jsonify({'error' : 'Goal value cannot be blank'})

    home_team = teams['Home']
    away_team = teams['Away']
    home_htg = goals['HT_Home']
    away_htg = goals['HT_Away']
    home_ftg = goals['FT_Home']
    away_ftg = goals['FT_Away']
    #the next line gets the result before any requested update is applied to it:
    result = Result.get((Result.home_team == teams['Home'].lower()) & (Result.away_team == teams['Away'].lower()))
    UI_msg, goal_totals_valid = results_validator.validate_goal_values(goals)
    if goal_totals_valid:
        if result.match_status == 'fixture': #this is the initial result for this fixture
            week = set_week(result)
            update_query = Result.update(
            home_htg = home_htg,
            away_htg = away_htg,
            home_ftg = home_ftg,
            away_ftg = away_ftg,
            match_status = 'result',
            week = week
            ).where(Result.result_id == result.result_id)
            update_query.execute()
            update_team_stats(teams['Home'],teams['Away'],goals['FT_Home'],goals['FT_Away'])
            return jsonify({'done' : 'Result created, team stats and league table updated'})
        else: #record is an existing result - get the result BEFORE 'Edit' is applied
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
            return jsonify({'done' : 'Result, team stats and league table updated'})
    else:
        return jsonify({'error' : UI_msg})

@app.route('/verify_resolved_results/', methods=['PUT'])
def verify():
    """Re-validates results data which has been re-submitted after errors have been corrected (or not as the case may be)"""
    UI_msg = None
    result_to_verify = Result.get(Result.result_id == int(request.form['resid']))
    teams = dict(Home=request.form['home_team'].lower().strip(),Away=request.form['away_team'].lower().strip())
    try:
        goals = dict(FT_Home=int(request.form.get('hftg')),HT_Home=int(request.form.get('hhtg')),
                     FT_Away=int(request.form.get('aftg')),HT_Away=int(request.form.get('ahtg')))
    except ValueError: #if any unexpected values submitted for goal data use existing goal values from database record
        goals = dict(FT_Home=result_to_verify.home_ftg, HT_Home=result_to_verify.home_htg, FT_Away=result_to_verify.away_ftg, HT_Away=result_to_verify.away_htg)

    week = set_week(result_to_verify)
    update_query = Result.update(
    home_team = teams['Home'],
    away_team = teams['Away'],
    home_ftg = goals['FT_Home'],
    away_ftg = goals['FT_Away'],
    home_htg = goals['HT_Home'],
    away_htg = goals['HT_Away'],
    week = week
    ).where(Result.result_id == result_to_verify.result_id)
    update_query.execute()
    #check if a valid error free 'duplicate' result exists for these 2 teams - it's possible to enter team names
    #whilst resolving errors that clash with a previously created/uploaded result
    result_count = Result.select().where((Result.home_team == teams["Home"]) & (Result.away_team == teams["Away"])).count()
    result = result_is_valid(teams,goals,ignore_result_is_new=True)
    if result == True and result_count == 1:
        update_query = Result.update(is_error = False).where(Result.result_id == result_to_verify.result_id)
        update_query.execute()
        update_team_stats(teams['Home'],teams['Away'],goals['FT_Home'],goals['FT_Away'])
        #delete errors for result as errors have been verified as cleared and are no longer relevant
        delete_query = Error.delete().where(Result.result_id == result_to_verify.result_id)
        delete_query.execute()
    elif result_count > 1:
        #a result record for the same home and away team combination already exists
        #so the duplicate result check is valid
        result = result_is_valid(teams,goals)

    if result != True:
        #delete errors that have been resolved
        delete_resolved_errors = Error.delete().where((Result.result_id==result_to_verify.result_id) &
                                (str(Error.description) not in result['Errors']))
        delete_resolved_errors.execute()
        #create new errors
        for err in result['Errors']:
            error = Error.create(result_id=result_to_verify.result_id, description=err)

    return jsonify({'done' : 'Re-validation complete'})

@app.route('/delete_all_results/')
def delete_all_results():
    """Deletes all results and resets every team's stats (matches won, drawn, lost, goals scored and conceded) to zero"""
    delete_query = Error.delete()
    delete_query.execute()
    delete_query = Result.delete()
    delete_query.execute()
    reset_teams_query = Team.update(won = 0,drawn = 0,lost = 0,
    goals_scored = 0,goals_conceded = 0)
    reset_teams_query.execute()
    return redirect(url_for('home'))

@app.route('/delete_all_teams/', methods=['POST'])
def delete_all_teams():
    """deleting teams also causes all results and errors to be deleted
    """
    delete_query = Team.delete()
    delete_query.execute()
    delete_query = Error.delete()
    delete_query.execute()
    delete_query = Result.delete()
    delete_query.execute()
    if os.path.exists('result_upload_errors.csv'):
        os.remove('result_upload_errors.csv')
    return redirect(url_for('home'))

@app.route('/team_drill_down/<team>', methods=['GET'])
def drill_down(team):
    state = g.get('state',None)
    team=Team.get(Team.name == team)
    results=Result.select().where(((Result.away_team == team.name) | (Result.home_team == team.name))
                                  & ((Result.is_error == False) & (Result.match_status == 'result')))
    if results:
        # object_list method creates a PaginatedQuery object calls get_object_list
        return object_list('teamDetails.html',results,paginate_by=9,team=team,state=state)
    else:
        return render_template("feedback.html", feedback = "There are no results to view for " + team.name.title(),state=state)

@app.route('/charts/', methods=['GET'])
def GetCharts():
    state = g.get('state',None)
    results = Result.select().where(Result.is_error == False)
    if len(results) == 0:
        feedback = "No results available"
        return render_template("feedback.html",feedback = feedback,state=state)

    #...otherwise grab any teams that have been submitted via checkboxes
    teams_filter = request.args.getlist('team_checked')

    #team_list is passed to the view to produce the checkboxes
    team_list = Team.select().order_by(Team.name)
    chartToLoad = request.args.get('chart_select')
    team_positions_dict = {}

    #when page is requested from home page no chart will be displayed so
    #chartToLoad set to barChartPoints as default
    if chartToLoad is None:
        chartToLoad = 'barChartPoints'

    if chartToLoad == 'lineChart':
        #get the minimum and maximum week range stored in the
        #database to generate data for line chart
        min_week = Result.select(fn.MIN(Result.week))
        max_week = Result.select(fn.MAX(Result.week))
        team_positions = get_results_by_week(min_week,max_week)

        if len(teams_filter):
            for team in team_positions:
                if team.team in teams_filter:
                    t = dict(TeamName=team.team,Positions=team.position)
                    team_positions_dict[team.team] = t
            return render_template('charts_home.html',team_data=team_positions_dict,team_list = team_list,chartToLoad=chartToLoad,state=state)
        else:
            for team in team_positions:
                t = dict(TeamName=team.team,Positions=team.position)
                team_positions_dict[team.team] = t
            return render_template('charts_home.html', team_data=team_positions_dict, team_list = team_list,chartToLoad=chartToLoad,state=state)
    else:
        if len(teams_filter):
            teams = Team.select().where(Team.name.in_(teams_filter))
        else:
            teams = Team.select()
        teams_in_points_order = sorted(teams, key=methodcaller('points'), reverse=True)
        for team in teams_in_points_order:
            team_positions_dict[team.name] = team.lost, team.drawn, team.won, team.points(), team.max_possible()

        if len(teams) > 0:
            return render_template('charts_home.html', team_data=team_positions_dict,team_list = team_list,chartToLoad=chartToLoad,state=state)
        else:
            feedback = "There are no teams in the system. Please add some."
            return render_template('feedback.html', feedback = feedback, state=state)

@app.route('/statiscal_analysis/<team>', methods=['GET'])
# I should refactor this so only the team is processed by create_weekly_position_table...
# Actually after investigating all teams have to be processed as weekly positional data
# is in relation to all the other teams positions...otherwise the stats for a single team
# would have the team is position 1 all the time (nothing to sort into order against)
def stats_drill_down(team):
    state = g.get('state',None)
    team_stats=Team.get(Team.name == team)
    home_form_dict = get_stats_home_form(team_stats)
    away_form_dict = get_stats_away_form(team_stats)
    min_week = Result.select(fn.MIN(Result.week))
    max_week = Result.select(fn.MAX(Result.week))
    # get all valid results
    team_positions = get_results_by_week(min_week,max_week)
    # get the TeamPostion domain object for the team in question
    position_history = [x for x in team_positions if x.team == team]
    # get a list of weekly positions from the object's postion property
    # note there is only one object in the list
    positions = position_history[0].position
    average_pos = mean(positions)

    weeks = range(1,39)
    chartToLoad = 'pieChart'
    team_dict = dict(TeamName=team_stats.name,Lost=team_stats.lost,Drawn=team_stats.drawn,Won=team_stats.won,
                     GS=team_stats.goals_scored,GC=team_stats.goals_conceded,Rating=team_stats.rating(),
                     Played=team_stats.games_played(),Average=average_pos)
    # week_start = request.args.get('week_select_start')
    # week_end = request.args.get('week_select_end')
    return render_template('stats_breakdown.html',team_data=team_dict,weeks=weeks,chartToLoad=chartToLoad,
                            history=positions,Home_Form=home_form_dict,Away_Form=away_form_dict,state=state)

@app.route('/get_comparison_data', methods=['GET'])
# build up the data requirements for the display_comparison(data) action
def get_comparison_data():
    teams_filter = request.args.getlist('teams_for_comparison[]');
    teams = Team.select().where(Team.name.in_(teams_filter))
    min_week = Result.select(fn.MIN(Result.week))
    max_week = Result.select(fn.MAX(Result.week))
    # get valid results
    team_positions = get_results_by_week(min_week,max_week)
    comparison_data = []
    for team in teams:
        performance_data = {}
        # get the TeamPostion domain objects for the teams in question
        position_history = [x for x in team_positions if x.team == team.name]
        positions = position_history[0].position

        performance_data['Team'] = team.name
        performance_data['Rating'] = team.rating()
        performance_data['CurrentPosition'] = positions[-1]
        performance_data['Average'] = mean(positions)
        performance_data['Points'] = team.points()
        performance_data['GS'] = team.goals_scored
        performance_data['GC'] = team.goals_conceded
        performance_data['Won'] = team.won
        performance_data['Drawn'] = team.drawn
        performance_data['Lost'] = team.lost
        comparison_data.append(performance_data)
    return jsonify({'teams' : comparison_data})

@app.route('/comparison/<data>', methods=['GET'])
def display_comparison(data):
    state = g.get('state',None)
    data_in = json.loads(data)
    team1 = data_in['data']['teams'][0]
    team2 = data_in['data']['teams'][1]
    teams = [team1['Team'], team2['Team']]

    # wrap data required for the comparison charts into dict:
    comparison_chart_data = {}
    comparison_chart_data['T1_GS'] = team1['GS']
    comparison_chart_data['T1_GC'] = team1['GC']
    comparison_chart_data['T1_Won'] = team1['Won']
    comparison_chart_data['T1_Drawn'] = team1['Drawn']
    comparison_chart_data['T1_Lost'] = team1['Lost']
    comparison_chart_data['T2_GS'] = team2['GS']
    comparison_chart_data['T2_GC'] = team2['GC']
    comparison_chart_data['T2_Won'] = team2['Won']
    comparison_chart_data['T2_Drawn'] = team2['Drawn']
    comparison_chart_data['T2_Lost'] = team2['Lost']
    # get the actual results between the 2 teams
    results=Result.select().where(((Result.home_team == teams[0]) | (Result.away_team == teams[0]))
                                   & ((Result.home_team == teams[1]) | (Result.away_team == teams[1])))
    return render_template("comparison.html",team1=team1,team2=team2,
                            chart_data=comparison_chart_data,results=results,state=state)

@app.route('/upload_errors/', methods=['GET'])
def display_upload_errors():
    state = g.get('state',None)
    result_errors = Result.select().where(Result.is_error == True)
    if len(result_errors) > 0:
        return render_template('uploadErrors.html',invalid_results=result_errors,
                               error_count=Error.select().count(),state=state)
    else:
        return render_template('uploadErrors.html',feedback = "No errors to report",state=state)

def get_results_by_week(from_week,to_week):
    """"""
    # get results only - not error results or fixtures
    results = Result.select().where(Result.week.between(from_week,to_week) &
                                   (Result.is_error == False) &
                                   (Result.match_status == 'result'))
    return create_weekly_position_table(results)

def create_weekly_position_table(results):
    """
    This function obtains and returns for each team their positional history in the league week by week.
    This data feeds the data visualisation functionality where it is used to create a trendline for each team.
    Input parameter 'results' is a set of results returned by a query executed in get_results_by_week(from_week,to_week).
    TeamPosition objects store the week by week league table position history based on a teams performance.
    For each week results data is processed and for each result the result type is determined (which will either be a home win, away win or a draw).
    Based on this the TeamPosition's points, goals scored and conceded attributes are updated.
    Once these stats are updated the 'positions' list is sorted so TeamPosition objects are in ascending points order (stored in in_points_order list).
    Now the in_points_order list is looped through getting the index of each TeamPosition object), this index
    (when 1 is added to it therefore negating zero based numbering) represents the league position for a team in the week being currently iterated,
    this league position is added the position list for the team - this postion attribute (list) represents the position history of a team through the season.
    """
    teams = Team.select(Team.name)
    teams_list = []
    for team in teams:
        team_position = TeamPosition(team.name)
        teams_list.append((team_position))
    # 'week_range' is a set of distinct weeks that informs how many weeks of results data is to be processed
    week_range = results.select(Result.week).distinct()
    for w in week_range:
        match_week = [w.week]
        # 'positions' is a list of match weeks and TeamPosition objects
        positions = [*match_week,*teams_list]
        for result in results:
            if result.week == positions[0]:
                if result.result_type() == 'home win':
                    winner = result.home_team
                    loser = result.away_team
                    #skip the first element as it is an integer and
                    #not a TeamPosition object
                    for item in positions[1:]:
                        if item.team == winner:
                            item.points += 3
                            item.scored += result.home_ftg
                            item.conceded += result.away_ftg
                        if item.team == loser:
                            item.scored += result.away_ftg
                            item.conceded += result.home_ftg
                elif result.result_type() == 'away win':
                    winner = result.away_team
                    loser = result.home_team
                    for item in positions[1:]:
                        if item.team == winner:
                            item.points += 3
                            item.scored += result.away_ftg
                            item.conceded += result.home_ftg
                        if item.team == loser:
                            item.scored += result.home_ftg
                            item.conceded += result.away_ftg
                elif result.result_type() == 'draw':
                    home_team = result.home_team
                    away_team = result.away_team
                    for item in positions[1:]:
                        if item.team == home_team:
                            item.points += 1
                            item.scored += result.home_ftg
                            item.conceded += result.away_ftg
                        if item.team == away_team:
                            item.points += 1
                            item.scored += result.away_ftg
                            item.conceded += result.home_ftg
        #sort positions[] into points order
        in_goals_scored_order = sorted(positions[1:], key=attrgetter('scored'))
        in_GD_order = sorted(in_goals_scored_order, key=methodcaller('goal_difference'), reverse=True)
        in_points_order = sorted(in_GD_order, key=attrgetter('points'),reverse=True)
        for pos in in_points_order:
            i = in_points_order.index(pos)
            pos.position.append(i+1)
    return in_points_order

def result_is_valid(teams,goals,**kwargs):
    res = defaultdict(list,{**teams, **goals})
    results_validator = ResultsValidator()
    UI_msg, goal_types_valid = results_validator.validate_goal_types(goals)
    if not goal_types_valid:
        res['Errors'].append(UI_msg)
    UI_msg, goal_values_valid = results_validator.validate_goal_values(goals)
    if not goal_values_valid:
        res['Errors'].append(UI_msg)

    UI_msg, team_names_provided = results_validator.validate_team_names_present(teams)
    if not team_names_provided:
        res['Errors'].append(UI_msg)

    UI_msg, teams_exist = results_validator.validate_teams_exist(teams)
    if not teams_exist:
        res['Errors'].append(UI_msg)
    # print("4 - Outcome = {}".format(teams_exist))

    UI_msg, different_teams = results_validator.validate_home_and_away_teams_different(teams)
    if not different_teams:
        res['Errors'].append(UI_msg)
    # print("5 - Outcome = {}".format(different_teams))

    #this validation needs to skipped when result is being re-validated after upload
    if 'ignore_result_is_new' in kwargs:
        UI_msg = None
        new_result = True
        # print("6 - Ignored so Outcome = {}".format(new_result))
    else:
        UI_msg, new_result = results_validator.result_is_new(teams)

    if not new_result:
        res['Errors'].append(UI_msg)
    # print("7 - Outcome = {}".format(new_result))

    if goal_types_valid and goal_values_valid and team_names_provided and teams_exist and different_teams and new_result:
        # print("Valid result - {}".format(res))
        return True
    else:
        # print("ERROR in {}".format(res))
        return res

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
    """After a result has been updated this method amends EXISTING stats (matches
    won, drawn, lost, goals scored and conceded)for each team in the match."""
    current_result = Result.get(Result.result_id == previous_result['ID'])
    home_team = Team.get(Team.name == current_result.home_team)
    away_team = Team.get(Team.name == current_result.away_team)

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

def get_stats_home_form(team):
    wins = draws = losses = gs = gc = 0
    results=Result.select().where((Result.home_team == team.name) & (Result.match_status == 'result') & (Result.is_error == False))
    for r in results:
        if r.result_type() == 'home win':
            wins += 1
        elif r.result_type() == 'away win':
            losses += 1
        else:
            draws +=1
        gs += r.home_ftg
        gc += r.away_ftg
    points = (wins*3) + draws
    played = wins + losses + draws
    if played > 0:
        rating = team.rating(points,played)
    else:
        rating = "Rating not available - no games played"
    return dict(Won=wins,Lost=losses,Drawn=draws,GS=gs,GC=gc,Rating=rating,Played=played)


def get_stats_away_form(team):
    wins = draws = losses = gs = gc = 0
    results=Result.select().where((Result.away_team == team.name) & (Result.match_status == 'result') & (Result.is_error == False))
    for r in results:
        if r.result_type() == 'home win':
            losses += 1
        elif r.result_type() == 'away win':
            wins += 1
        else:
            draws +=1
        gs += r.away_ftg
        gc += r.home_ftg
    points = (wins*3) + draws
    played = wins + losses + draws
    if played > 0:
        rating = team.rating(points,played)
    else:
        rating = "Rating not available - no games played"
    return dict(Won=wins,Lost=losses,Drawn=draws,GS=gs,GC=gc,Rating=rating,Played=played)

def get_system_state():
    if Team.select().count() == 0 and Result.select().count() == 0:
        return "NO DATA"
    elif Team.select().count() < 2 and Result.select().count() == 0:
        return "1 TEAM"
    elif Team.select().count() >= 2 and Result.select().count() > 0 and Error.select().count() == 0:
        return "TEAM AND RESULT EXIST"
    elif Team.select().count() >= 2 and Error.select().count() > 0:
        return "ERRORS EXIST"
    else:
        return "TEAM DATA EXISTS"

def set_week(result):
    return math.ceil(result.result_id/10)

if __name__ == '__main__':
    app.secret_key ='sum fink' #THIS SHOULD BE IN CONFIG - SECRET_KEY = 'string'
    app.send_file_max_age_default = 0
    app.run(debug=True)
