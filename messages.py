from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app
import datetime
import homepage
import queries as q

import cs304dbi as dbi

#Helper functions for messaging feature
def getChatsFrom(conn, id):
    """
    This function retrieves messages sent by the given user id.
    Input: Connection, user id

    It connects to the database, executes a query to select all messages that the 
    given user ID has sent, and returns the fetched result.

    Returns: A list of dictionaries containing the fetched messages.

    """
    conn = q.getConnection()
    curs = dbi.dict_cursor(conn)
    curs.execute('''select `to` as recipient, message_text as message,
                 message_time as time from message where `from` = %s ''', [id])
    return curs.fetchall()

def getChatsTo(conn, id):
    """
    This function retrieves messages sent to the given user id.
    Input: Connection, user id

    It connects to the database, executes a query to select all messages that was 
    sent to the given user ID, and returns the fetched result.

    Returns: A list of dictionaries containing fetched messages.

    """
    conn = q.getConnection()
    curs = dbi.dict_cursor(conn)
    curs.execute('''select `from` as sender, message_text as message,
                 message_time as time from message where `to` = %s ''', [id])
    return curs.fetchall()

def getChatsbetween(conn, rec_id, send_id):
    """
    This function retrieves messages exchanged between the given user ids.
    Input: Connection, user id, user id

    It connects to the database, executes a query to select all messages that the 
    given user IDs have sent each other, and returns the fetched result.

    Returns: A list of dictionaries containing all the fetched messages.

    """
    conn = q.getConnection()
    curs = dbi.dict_cursor(conn)
    curs.execute('''select `from` as sender, `to` as recipient, 
                message_text as message, message_time as time from message 
                where `to`= %s and `from` = %s or `to`= %s and `from` = %s
                order by message_time asc''',
                 [rec_id, send_id, send_id, rec_id])
    return curs.fetchall()

def addMessage(conn, rec_id, sender_id, message):
    """
    This function adds a given message between the given ids to the message table.
    Input: Connection, recipient's user id, sender's uder id, message text

    It connects to the database, executes a query to 
    insert the given messageto the message table.

    Returns: None.
    """
     # Insert into database or further processing
    conn = q.getConnection()
    curs = dbi.cursor(conn)
    timestamp = datetime.datetime.now()
    sql = '''insert into message(`from`, `to`, message_text, message_time)
        values(%s, %s, %s, %s)'''
    curs.execute(sql, [sender_id, rec_id, message, timestamp])
    conn.commit()

        
@app.route('/chat/<rec_id>', methods =["POST", "GET"])
def sendMessage(rec_id):
    """
    This function handles sending messages.
    Input: recipient user id
    It renders the message page for GET requests. For POST requests, it retrieves the message from the form, 
    gets the senders user ID from the session, records the current timestamp, inserts the message details into the database, 
    and displays a confirmation message.

    Returns: For GET requests: Renders the messages.html template with the page title “Message” and the recipients user ID.
    For POST requests: Inserts the message into the database and renders the messages.html template with a confirmation message.
    """
    if 'user_id' in session:
        user_id = session.get('user_id')
        conn = q.getConnection()
        allmessages = getChatsbetween(conn, rec_id, user_id)
        if len(allmessages) != 0:
            for message in allmessages:
                sender_id = message['sender']
                recipient_id = message['recipient']
                sender_name = homepage.getUserDetails(conn, sender_id)['name']
                rec_name = homepage.getUserDetails(conn, recipient_id)['name']
                message['sender_name'] = sender_name
                message['recipient_name'] = rec_name
        else:
            sender_id = user_id
            rec_name = homepage.getUserDetails(conn, rec_id)['name']
            sender_name = homepage.getUserDetails(conn, user_id)['name']
        if request.method == "GET":                
            return render_template('messages.html', 
                                page_title = "Individual Chats",
                                messages = allmessages,
                                to_name = rec_name,
                                from_name = sender_name,
                                recipient_id = rec_id,
                                current_user_id = user_id )
        else:
           message = request.form.get('message')
           addMessage(conn, rec_id, sender_id, message)
           flash("Message sent!")
           return redirect(url_for('sendMessage', rec_id=rec_id))
    else:
        flash("You should be logged in!")
        return redirect(url_for('login'))
        
@app.route('/chat/', methods=["GET", "POST"])
def viewChat():
    """
    The viewChat function handles the display of the chat history. It supports both GET and POST requests. 
    Users must be logged in to access this functionality.

    If it receives a GET request: It renders the chat.html template.

    If it receives a POST request: It performs the same action as a GET request.

    Returns: the chat.html template if the user is logged in, or redirects to the index page 
    with an error message if the user is not logged in.
    """
    if 'user_id' in session:
        flash('Chat coming soon')
        # return render_template('chat.html',
        #                    page_title='Chat History')
    else:
        flash('You must be logged in to use the Chat feature!')
        return redirect(url_for('index'))

###################################################################################################################
