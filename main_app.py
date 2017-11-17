import csv
from flask import Flask, render_template, request, url_for, redirect, flash, json, jsonify
from models import *
from operator import methodcaller, attrgetter
from playhouse.shortcuts import model_to_dict

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
    # wdl_dd = create_dd_of_ints(39) > no longer using this on creat team view
    return render_template('createTeam.html')

@app.route('/create/', methods=['POST'])
def create_team():
    error = None
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

@app.route('/load_data/')
def display_upload_form():
    return render_template('upload.html')

@app.route('/upload_teams/', methods=['POST'])
def perform_teams_upload():
    error = None
    try:
        with open('Teams.csv') as team_csv:
            csv_reader = csv.reader(team_csv)
            next(csv_reader)

            for row in csv_reader:
                Team.create(
                name = row[0],
                won = 0,
                drawn = 0,
                lost = 0,
                goals_scored = 0,
                goals_conceded = 0
                )
                #print (row)
            return redirect(url_for('home'))
    except IOError:
        error = 'That file has not been found'
        return render_template('upload.html',error=error)

@app.route('/upload_results/', methods=['POST'])
def perform_results_upload():
    error = None
    feedback = None
    invalid_rows = []
    if Team.select().count() < 1:
        feedback = "Teams must be loaded before loading results"
        return render_template('feedback.html', feedback=feedback)
    try:
        with open('2017ResultsShortVersion.csv') as results_csv:
            csv_reader = csv.reader(results_csv)
            next(csv_reader)

            for row in csv_reader:
                if row_is_valid(row):
                    Result.create(
                    home_team = row[0],
                    away_team = row[1],
                    home_ftg = row[2],
                    away_ftg = row[3],
                    home_htg = row[4],
                    away_htg = row[5]
                    )
                    #print (row)
                    update_team_stats(row[0],row[1],int(row[2]),int(row[3]))
                else:
                    invalid_rows.append(row)
            #in the case of errors show the upload errors view
            if len(invalid_rows) > 0:
                with open('result_upload_errors.csv', 'w') as results_errors_csv:
                    csv_writer = csv.writer(results_errors_csv)
                    csv_writer.writerows(invalid_rows)
                return render_template('uploadErrors.html',invalid_rows=invalid_rows)
            else:
                return redirect(url_for('view_results'))

    except IOError:
        error = 'That file has not been found'
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
    error = None
    # check home and away teams are different
    if request.form.get('home_team') == request.form.get('away_team'):
        error = request.form.get('home_team').title() + " cannot play themselves!"
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = error, team_dd = team_dd)
    # check half-time goals are not greater than full-time goals
    # before saving result:
    if int(request.form['hftg']) >= int(request.form['hhtg']) and int(request.form['aftg']) >= int(request.form['ahtg']):
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
    else:
        error = ("INVALID RESULT - half time goals " +
        str(int(request.form['ahtg']) + int(request.form['hhtg'])) +
        " cannot be higher than full time goals total of " +
        str(int(request.form['aftg']) + int(request.form['hftg']))
        )
        team_dd = Team.select().order_by(Team.name)
        return render_template('enterResult.html', error = error, team_dd = team_dd)

@app.route('/view_results/')
def view_results():
    feedback = None
    results = Result.select()
    if len(results) > 0:
        return render_template('results.html', results = results)
    else:
        feedback = "No results available"
        return render_template("feedback.html", feedback = feedback)

@app.route('/delete_all_results/')
def delete_all_results():
    delete_query = Result.delete()
    delete_query.execute()
    return redirect(url_for('home'))

@app.route('/delete_all_teams/', methods=['POST'])
def delete_all_teees():
    """deleting teams also causes all results to be deleted
    """
    delete_query = Team.delete()
    delete_query.execute()
    delete_query = Result.delete()
    delete_query.execute()
    return redirect(url_for('home'))

@app.route('/team_drill_down/<team>', methods=['GET'])
def drill_down(team):
    return render_template(
    'teamDetails.html', team=Team.get(Team.name == team),
    results=Result.select()
                  .where((Result.away_team == team) | (Result.home_team == team))
    )

@app.route('/get_teams_autocompletion_data', methods=['GET'])
def team_autocompletion_src():
    team_source=["arsenal","rs","Man Utd","Man City"]
    return jsonify(team_source)
    # team_source = Team.select(Team.name).order_by(Team.name)
    # print (team_source)
    # print (json.dumps(model_to_dict(team_source.get())))
    # return json.dumps(model_to_dict(team_source.get()))

def create_dd_of_ints(required_range):
    dd = []
    for i in range(required_range):
        dd.append(i)
    return dd

def row_is_valid(row):
    """
    check half times don't exceed full time goals
    check all data presents
    check team actually exist
    check if valid result already exists > TODO
    """
    # rules = [goals_valid(row),mandatory_data_present(row),teams_exist(row),result_is_new()]
    rules = [goals_valid(row),mandatory_data_present(row),teams_exists(row)]
    return all(rules)

def goals_valid(row):
    if row[2] >= row[4] and row[3] >= row[5]:
        return True
    else:
        return False

def mandatory_data_present(row):
    for item in row:
        if item == '':
            return False
    else:
        return True

def teams_exists(row):
        home_team = Team.select().where(Team.name == row[0])
        away_team = Team.select().where(Team.name == row[1])

        if home_team.exists() & away_team.exists():
            return True
        else:
            return False

def update_team_stats(home_team, away_team, goals_scored_by_home_team, goals_scored_by_away_team):
    if goals_scored_by_home_team > goals_scored_by_away_team:
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
        update_query = Team.update(drawn = Team.drawn + 1,
        goals_scored = Team.goals_scored + goals_scored_by_home_team,
        goals_conceded = Team.goals_conceded + goals_scored_by_away_team
        ).where(Team.name << [home_team, away_team])
        update_query.execute()

if __name__ == '__main__':
    app.secret_key ='sum fink' #THIS SHOULD BE IN CONFIG - SECRET_KEY = 'string'
    app.send_file_max_age_default = 0
    app.run(debug=True)
