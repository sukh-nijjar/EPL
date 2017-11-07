from flask import Flask, render_template, request, url_for, redirect, flash, json, jsonify
from operator import itemgetter, attrgetter, methodcaller
from models import *
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
        teams_in_GD_order = sorted(teams, key=methodcaller('goal_difference'), reverse=True)
        teams_in_points_order = sorted(teams_in_GD_order, key=methodcaller('points'), reverse=True)
        return render_template('home.html', teams=teams_in_points_order)
    else:
        feedback = "No teams exist yet me lad"
        return render_template('feedback.html', feedback = feedback)

@app.route('/new_team/')
def new_team():
    wdl_dd = create_dd_of_ints(39)
    return render_template('createTeam.html', drop_down_values = wdl_dd)

@app.route('/create/', methods=['POST'])
def create_team():
    error = None
    wdl_dd = create_dd_of_ints(39)
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
        return render_template('createTeam.html',error=error, drop_down_values = wdl_dd)

@app.route('/enter_result/')
def enter_result():
    feedback = None
    team_dd = Team.select().order_by(Team.name)
    if len(team_dd) > 1:
        return render_template('enterResult.html',team_dd = team_dd)
    else:
        feedback = "Add at least a couple o teams me lad before trying add a result!"
        return render_template("feedback.html", feedback = feedback)

@app.route('/create_result/', methods=['POST'])
def create_result():
    error = None
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
        error = "INVALID RESULT"
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
    delete_query = Team.delete()
    delete_query.execute()
    return redirect(url_for('home'))

@app.route('/team_drill_down/<team>', methods=['GET'])
def drill_down(team):
    return render_template('teamDetails.html', team=Team.get(Team.name == team))

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
