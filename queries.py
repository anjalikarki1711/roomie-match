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



"""
The getConnection function establishes a connection to the database.

Returns: A database connection object.
"""
def getConnection():
    return dbi.connect()

###### Profile queries

"""
The getFile function retrieves the profile picture filename associated with a given file ID.

Input: 
    conn: A database connection object.
    file_id: The ID of the file to retrieve.

Returns: 
    The profile picture filename associated with the provided file_id.
"""
def getFile(conn, file_id):
    curs = dbi.dict_cursor(conn)
    curs.execute(
        '''select profile_pic_filename from file where file_id = %s''',
        [file_id])
    numrows = curs.fetchone()
    return numrows

"""
The getUserInfo function retrieves user information for a given user ID.

Input: 
    conn: A database connection object.
    user_id: The ID of the user to retrieve information for.

Returns: A dictionary containing user information such as user_id, name, gender, age, 
profession, profile description, location, pets, hobbies, and seeking status.
"""
def getUserInfo(conn, user_id):
    curs = dbi.dict_cursor(conn)
    curs.execute('''SELECT user_id, name, gender, age, profession, profile_desc, location, pets, 
                 hobbies, seeking FROM user WHERE user_id = %s''', [user_id])
    user = curs.fetchone()
    return user

"""
The getProfpic function retrieves the profile picture data for a given user ID.

Input: 
    conn: A database connection object.
    user_id: The ID of the user to retrieve the profile picture for.

Returns: A dictionary containing the file ID and profile picture filename associated with the user.
"""
def getProfpic(conn, user_id):
    curs = dbi.dict_cursor(conn)
    curs.execute('SELECT file_id, profile_pic_filename FROM file WHERE user_id = %s', [user_id])
    profile_pic_data = curs.fetchone()
    return profile_pic_data

"""
The updateProfPic function updates the profile picture filename for a given user ID.

Input: 
    conn: A database connection object.
    filename: The new profile picture filename.
    user_id: The ID of the user to update the profile picture for.
"""
def updateProfPic(conn, filename, user_id):
    curs = dbi.cursor(conn)
    curs.execute('UPDATE file SET profile_pic_filename = %s WHERE user_id = %s', [filename, user_id])
    conn.commit()

"""
The insertProfPic function inserts a new profile picture filename for a given user ID.

Input: 
    conn: A database connection object.
    filename: The profile picture filename to insert.
    user_id: The ID of the user to insert the profile picture for.
"""
def insertProfPic(conn, filename, user_id):
    curs = dbi.cursor(conn)
    curs.execute('INSERT INTO file (user_id, profile_pic_filename) VALUES (%s, %s)', [user_id, filename])
    conn.commit()

"""
The deleteProfPic function deletes the profile picture record for a given user ID.

Input: 
    conn: A database connection object.
    user_id: The ID of the user to delete the profile picture for.
"""
def deleteProfPic(conn, user_id):
    curs = dbi.cursor(conn)
    curs.execute('DELETE FROM file WHERE user_id = %s', [user_id])
    conn.commit()  # Commit after deleting the file record

"""
The deleteAccount function deletes the user account and associated profile picture for a given user ID.

Input: 
    conn: A database connection object.
    user_id: The ID of the user to delete the account for.

"""
def deleteAccount(conn, user_id):
    deleteProfPic(conn, user_id)
    curs = dbi.cursor(conn)
    curs.execute('DELETE FROM user WHERE user_id = %s', [user_id])
    curs.execute('DELETE FROM login WHERE user_id = %s', [user_id])
    conn.commit()

"""
The updateProfile function updates the user profile information for a given user ID.

Input: 
    conn: A database connection object.
    new_name: The new name of the user.
    new_gender: The new gender of the user.
    new_age: The new age of the user.
    new_profession: The new profession of the user.
    new_location: The new location of the user.
    new_desc: The new profile description of the user.
    new_pets: The new pets information of the user.
    new_hobbies: The new hobbies of the user.
    new_seeking: The new seeking status of the user.
    user_id: The ID of the user to update the profile for.
"""
def updateProfile(conn, new_name, new_gender, new_age, new_profession, new_location, 
                  new_desc, new_pets, new_hobbies, new_seeking, user_id):
    curs = dbi.cursor(conn)
    curs.execute('''UPDATE user SET name = %s, gender = %s, age = %s, profession = %s, location = %s, 
                 profile_desc = %s, pets = %s, hobbies = %s, seeking = %s WHERE user_id = %s''',
                         [new_name, new_gender, new_age, new_profession, new_location, new_desc, 
                          new_pets, new_hobbies, new_seeking, user_id])
    conn.commit()
