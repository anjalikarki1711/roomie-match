from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app
import datetime

#import bcrypt
import cs304dbi as dbi

"""
This function handles sending messages.
Input: recipient user id
It renders the message page for GET requests. For POST requests, it retrieves the message from the form, 
gets the senders user ID from the session, records the current timestamp, inserts the message details into the database, 
and displays a confirmation message.

Returns: For GET requests: Renders the messages.html template with the page title “Message” and the recipients user ID.
For POST requests: Inserts the message into the database and renders the messages.html template with a confirmation message.
"""
@app.route('/message/<recipient_uid>', methods=["GET", "POST"])
def sendMessage(recipient_uid):
    if request.method == "GET":
        return render_template ("messages.html", page_title="Message", recipient_uid=recipient_uid)
    else:
        message = request.form.get('message')
        sender_uid = session.get('user_id')
        timestamp = datetime.datetime.now()

        # Insert into database or further processing
        conn = dbi.connect()
        curs = dbi.cursor(conn)
        sql = '''insert into message(`from`, `to`, message_text, message_time)
                values(%s, %s, %s, %s)'''

        curs.execute(sql, [sender_uid, recipient_uid, message, timestamp])
        flash("Message sent!")
        return render_template("messages.html", page_title="Message", recipient_uid=recipient_uid)
        




    