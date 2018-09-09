import hashlib
import sqlite3

def set_hash_pw():
    hashed = hashlib.sha256("PasswordOfYourChoice")
    stored = hashed.hexdigest()
    return stored


stored = set_hash_pw()

connection = sqlite3.connect('EPL.db')
cursor = connection.cursor()
cursor.execute('delete from User')
#get a hashed string
stored = set_hash_pw()
#store it in table User
cursor.execute('insert into User (access_key,user_name) values (?,?)', (stored,"guest"))
connection.commit()
