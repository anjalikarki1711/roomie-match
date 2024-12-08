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



def getFile(conn, file_id):
    curs = dbi.dict_cursor(conn)
    curs.execute(
        '''select profile_pic_filename from file where file_id = %s''',
        [file_id])
    numrows = curs.fetchone()
    return numrows


def getUserInfo(conn, user_id):
    curs = dbi.dict_cursor(conn)
    curs.execute('SELECT user_id, name, gender, age, profession, profile_desc, location, pets, hobbies, seeking FROM user WHERE user_id = %s', [user_id])
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

