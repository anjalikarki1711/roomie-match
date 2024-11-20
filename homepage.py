# Roomie-match Homepage flask code 

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import secrets

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True


#helper functions
def getPostDetails(conn):
    '''gets post details from the database'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    posts = curs.execute('''select user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates,
            budget, housing_type, post_type from post ''')
    return curs.fetchall()



def getUser(conn, id):
    '''gets user's details '''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    userInfo = curs.execute('''select name, profile_desc from user inner join post
                            using(user_id) where user_id = %s''', [id])
    return curs.fetchone()

""" def insert_new_post(conn):
    '''Inserts new post data'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into post values(%s, %s, %s, %s)''', [], [], [], ) """
