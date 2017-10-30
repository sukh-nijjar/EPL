from flask import Flask, render_template, request, url_for, redirect, flash
from models import *
#from domain import FBTeam

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
    return render_template('home.html', teams=Team.select())

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
        name = request.form['team'].lower(),
        won = 0,
        drawn = 0,
        lost = 0,
        # won = request.form['won'],
        # drawn = request.form['drawn'],
        # lost = request.form['lost'],
        )
        return redirect(url_for('home'))
    except IntegrityError:
        error = 'Team already exists'
        return render_template('createTeam.html',error=error, drop_down_values = wdl_dd)

@app.route('/enter_result/')
def enter_result():
    goals_dd = create_dd_of_ints(11)
    team_dd = Team.select().order_by(Team.name)
    return render_template('enterResult.html',team_dd = team_dd, goals_dd = goals_dd)

@app.route('/create_result/', methods=['POST'])
def create_result():
    Result.create(
    home_team = request.form.get('home_team'),
    away_team = request.form.get('away_team'),
    home_htg = request.form['hhtg'],
    away_htg = request.form['ahtg'],
    home_ftg = request.form['hftg'],
    away_ftg = request.form['aftg']
    )
    #at this point do Team update for games w/d/l
    return redirect(url_for('home'))

@app.route('/view_results/')
def view_results():
    return render_template('results.html', results = Result.select())

@app.route('/delete_all_results/')
def delete_all_results():
    delete_query = Result.delete()
    delete_query.execute()
    return redirect(url_for('home'))

@app.route('/delete_all_teams/')
def delete_all_teees():
    delete_query = Team.delete()
    delete_query.execute()
    return redirect(url_for('home'))

@app.route('/team_drill_down/<team>', methods=['GET'])
def drill_down(team):
    return render_template('teamDetails.html', team=Team.get(Team.name == team))

def create_dd_of_ints(required_range):
    dd = []
    for i in range(required_range):
        dd.append(i)
    return dd

if __name__ == '__main__':
    app.secret_key ='sum fink' #THIS SHOULD BE IN CONFIG - SECRET_KEY = 'string'
    app.send_file_max_age_default = 0
    app.run(debug=True)
