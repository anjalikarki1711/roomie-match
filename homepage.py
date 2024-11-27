# Roomie-match Homepage flask code 

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite


# import cs304dbi_sqlite3 as dbi
from werkzeug.utils import secure_filename
import secrets
import homepage

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import secrets

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True


#helper functions
"""
This function retrieves post details from the database.

Input: connection

It connects to the database, executes a query to select post details, and returns the fetched results.

Returns: A list of dictionaries containing post details, including user ID, 
shared bathroom, shared bedroom, pet preferences, maximum roommates, budget, housing type, 
post type, location, post description, room picture filename, and file ID.

"""
def getPostDetails(conn):
    '''gets post details from the database'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    posts = curs.execute('''select post.user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates,
            budget, housing_type, post_type, location, post_desc, room_pic_filename, file_id from post join file on post.post_id= file.post_id''')
    return curs.fetchall()

"""
This function retrieves the picture associated with a post from the database for the feed.

Input: Connection and postID

It connects to the database, executes a query to select the room picture  filename for the given post ID, and returns the fetched result.

Returns: A dictionary containing the room picture filename.
"""
def getProfilePic(conn, postId):
    '''gets picture associated with the post from the database for the feed'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    picture = curs.execute('''select room_pic_filename from file where post_id = %s''', [postId])
    return curs.fetchone()
    


"""
This function retrieves a user’s details from the database.
Input: Connection, user id

It connects to the database, executes a query to select the users name and 
profile description for the given user ID, and returns the fetched result.

Returns: A dictionary containing the users name and profile description.

"""
def getUser(conn, id):
    '''gets user's details '''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    userInfo = curs.execute('''select name, profile_desc from user inner join post
                            using(user_id) where user_id = %s''', [id])
    return curs.fetchone()


"""
This function attempts to convert the variable to an integer. If successful, it returns True; otherwise, it returns False.
Input: var 

Returns: True if the variable can be converted to an integer, False otherwise.
"""
def isInt(var):
    try:
        var = int(var)
        return True
    except ValueError:
        return False
