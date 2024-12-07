from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app
import datetime

#import bcrypt
import cs304dbi as dbi

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