#Authors: Anjali Karki, Flora Mukako, Ali Bichanga, Indira Ruslanova
#Database related functions

from flask import (render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app

from werkzeug.utils import secure_filename
import cs304dbi as dbi
import os
import homepage
import login

def getConnection():
    """
    The getConnection function establishes a connection to the database.

    Returns: A database connection object.
    """
    return dbi.connect()

###### Profile queries


def getFile(conn, file_id):
    """
    The getFile function retrieves the profile picture filename associated with a given file ID.

    Input: 
        conn: A database connection object.
        file_id: The ID of the file to retrieve.

    Returns: 
        The profile picture filename associated with the provided file_id.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute(
        '''select profile_pic_filename from file where file_id = %s''',
        [file_id])
    numrows = curs.fetchone()
    return numrows


def getUserInfo(conn, user_id):
    """
    The getUserInfo function retrieves user information for a given user ID.

    Input: 
        conn: A database connection object.
        user_id: The ID of the user to retrieve information for.

    Returns: A dictionary containing user information such as user_id, name, gender, age, 
    profession, profile description, location, pets, hobbies, and seeking status.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''SELECT user_id, name, gender, age, profession, profile_desc, location, pets, 
                 hobbies, seeking FROM user WHERE user_id = %s''', [user_id])
    user = curs.fetchone()
    return user


def getProfpic(conn, user_id):
    """
    The getProfpic function retrieves the profile picture data for a given user ID.

    Input: 
        conn: A database connection object.
        user_id: The ID of the user to retrieve the profile picture for.

    Returns: A dictionary containing the file ID and profile picture filename associated with the user.
    """
    curs = dbi.dict_cursor(conn)
    curs.execute('SELECT file_id, profile_pic_filename FROM file WHERE user_id = %s', [user_id])
    profile_pic_data = curs.fetchone()
    return profile_pic_data


def updateProfPic(conn, filename, user_id):
    """
    The updateProfPic function updates the profile picture filename for a given user ID.

    Input: 
        conn: A database connection object.
        filename: The new profile picture filename.
        user_id: The ID of the user to update the profile picture for.
    """
    curs = dbi.cursor(conn)
    curs.execute('UPDATE file SET profile_pic_filename = %s WHERE user_id = %s', [filename, user_id])
    conn.commit()


def insertProfPic(conn, filename, user_id):
    """
    The insertProfPic function inserts a new profile picture filename for a given user ID.

    Input: 
        conn: A database connection object.
        filename: The profile picture filename to insert.
        user_id: The ID of the user to insert the profile picture for.
    """
    curs = dbi.cursor(conn)
    curs.execute('INSERT INTO file (user_id, profile_pic_filename) VALUES (%s, %s)', [user_id, filename])
    conn.commit()


def deleteProfPic(conn, user_id):
    """
    The deleteProfPic function deletes the profile picture record for a given user ID.

    Input: 
        conn: A database connection object.
        user_id: The ID of the user to delete the profile picture for.
    """
    curs = dbi.cursor(conn)
    curs.execute('DELETE FROM file WHERE user_id = %s', [user_id])
    conn.commit()  # Commit after deleting the file record


def deleteAccount(conn, user_id):
    """
    The deleteAccount function deletes the user account and associated profile picture for a given user ID.

    Input: 
        conn: A database connection object.
        user_id: The ID of the user to delete the account for.

    """
    deleteProfPic(conn, user_id)
    curs = dbi.cursor(conn)
    curs.execute('DELETE FROM user WHERE user_id = %s', [user_id])
    curs.execute('DELETE FROM login WHERE user_id = %s', [user_id])
    conn.commit()


def updateProfile(conn, new_name, new_gender, new_age, new_profession, new_location, 
                  new_desc, new_pets, new_hobbies, new_seeking, user_id):
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
    curs = dbi.cursor(conn)
    curs.execute('''UPDATE user SET name = %s, gender = %s, age = %s, profession = %s, location = %s, 
                 profile_desc = %s, pets = %s, hobbies = %s, seeking = %s WHERE user_id = %s''',
                         [new_name, new_gender, new_age, new_profession, new_location, new_desc, 
                          new_pets, new_hobbies, new_seeking, user_id])
    conn.commit()

"""
The peopleMessaging function takes in a connection and a userid and returns a list of people the person
with the uid is messaging


Input: conn, uid
Return: allPeopleList which is a list of tuples containing a name and a user id of a person who has either sent
or received messages from the person with the given uid
"""
def peopleMessaging(conn, uid):
    curs = dbi.cursor(conn)
    curs.execute('''select message.to, user.name FROM message inner
                 join user on (message.to = user.user_id) where message.from = %s''', [uid])
    toList = curs.fetchall()
    curs.execute('''select message.from, user.name FROM message inner
                 join user on (message.from = user.user_id) where message.to = %s''', [uid])
    fromList = curs.fetchall()
    allPeopleList = []
    for name in toList:
        if name not in allPeopleList:
            allPeopleList.append(name)
    for name in fromList:
        if name not in allPeopleList:
            allPeopleList.append(name)
    return allPeopleList
