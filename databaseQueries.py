import sqlite3

connection = sqlite3.connect('EPL.db')
cursor = connection.cursor()

cursor.execute('select * from Error')
query_result = cursor.fetchall()
for qr in query_result:
    print(qr)

print("-") * 200

# cursor.execute('select * from Result where week in (38)')
cursor.execute('select * from Result')
query_result = cursor.fetchall()
for qr in query_result:
    print(qr)

connection.close()


#debug helpers
def display_all_error_in_DB():
    errors = Error.select()
    print("-----------Error Count = {}".format(errors.count()) + "-------------------------")
    for e in errors:
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

def display_fixtures_in_DB():
    fixtures = Result.select().where(Result.match_status == 'fixture')
    for f in fixtures:
        print("{}, {}, {}".format(f.home_team, f.away_team, f.match_status))

def display_results_in_DB():
    res = Result.select().where(Result.match_status == 'result')
    for f in res:
        print("{}, {}, {}, {}".format(f.week,f.home_team, f.away_team, f.match_status))

#end debug helpers
