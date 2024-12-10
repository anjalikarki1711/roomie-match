from flask import (render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app

from werkzeug.utils import secure_filename
import cs304dbi as dbi
import os
import homepage as homepage
import login as login
from flask import g



def getConnection():
    return dbi.connect()

###### Profile queries
def getFile(conn, file_id):
    curs = dbi.dict_cursor(conn)
    curs.execute(
        '''select profile_pic_filename from file where file_id = %s''',
        [file_id])
    numrows = curs.fetchone()
    return numrows


def getUserInfo(conn, user_id):
    curs = dbi.dict_cursor(conn)
    curs.execute('''SELECT user_id, name, gender, age, profession, profile_desc, location, pets, 
                 hobbies, seeking FROM user WHERE user_id = %s''', [user_id])
    user = curs.fetchone()
    return user

def getProfpic(conn, user_id):
    curs = dbi.dict_cursor(conn)
    curs.execute('SELECT file_id, profile_pic_filename FROM file WHERE user_id = %s', [user_id])
    profile_pic_data = curs.fetchone()
    return profile_pic_data


def updateProfPic(conn, filename, user_id):
    curs = dbi.cursor(conn)
    curs.execute('UPDATE file SET profile_pic_filename = %s WHERE user_id = %s', [filename, user_id])
    conn.commit()

def insertProfPic(conn, filename, user_id):
    curs = dbi.cursor(conn)
    curs.execute('INSERT INTO file (user_id, profile_pic_filename) VALUES (%s, %s)', [user_id, filename])
    conn.commit()

def deleteProfPic(conn, user_id):
    curs = dbi.cursor(conn)
    curs.execute('DELETE FROM file WHERE user_id = %s', [user_id])
    conn.commit()  # Commit after deleting the file record

def deleteAccount(conn, user_id):
    deleteProfPic(conn, user_id)
    curs = dbi.cursor(conn)
    curs.execute('DELETE FROM user WHERE user_id = %s', [user_id])
    curs.execute('DELETE FROM login WHERE user_id = %s', [user_id])
    conn.commit()


def updateProfile(conn, new_name, new_gender, new_age, new_profession, new_location, new_desc, new_pets, new_hobbies, new_seeking, user_id):
    curs = dbi.cursor(conn)
    curs.execute('UPDATE user SET name = %s, gender = %s, age = %s, profession = %s, location = %s, profile_desc = %s, pets = %s, hobbies = %s, seeking = %s WHERE user_id = %s',
                         [new_name, new_gender, new_age, new_profession, new_location, new_desc, new_pets, new_hobbies, new_seeking, user_id])
    conn.commit()



########################### Login Queries
def registerNewUser(conn, username, passwd):
    curs = dbi.cursor(conn)
    curs.execute('''INSERT INTO login(user_name,hashed_password)
                            VALUES(%s,%s)
                         RETURNING user_id''',
                        [username, stored])
    user_id = curs.fetchone()[0]

            # Insert the user_id into the user table
    curs.execute('''INSERT INTO user(user_id)
                VALUES(%s)''',
             [user_id])
            
    conn.commit()
    return user_id

def loginUser(conn, username, passwd):
    curs = dbi.dict_cursor(conn)
    curs.execute('''SELECT user_id,user_name,hashed_password
                        FROM login
                        WHERE user_name = %s''',
                    [username])
    row = curs.fetchone()
    return row
