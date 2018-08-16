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
