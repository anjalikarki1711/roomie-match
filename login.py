from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

import bcrypt
import cs304dbi as dbi

@app.route('/sign-up/', methods=["POST"])
def join():
    username = request.form.get('username')
    passwd1 = request.form.get('password1')
    passwd2 = request.form.get('password2')
    if passwd1 != passwd2:
        flash('passwords do not match')
        return redirect( url_for('join'))
    hashed = bcrypt.hashpw(passwd1.encode('utf-8'),
                           bcrypt.gensalt())
    stored = hashed.decode('utf-8')
    print(passwd1, type(passwd1), hashed, stored)

    #connect to database
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('''INSERT INTO login(user_id,hashed_password)
                        VALUES(null,%s,%s)''',
                     [username, stored])
        conn.commit()
    except Exception as err:
        flash('That email is tied to an existing account: {}'.format(repr(err)))
        return redirect(url_for('index'))
    curs.execute('select last_insert_id()')
    row = curs.fetchone()
    uid = row[0]
    flash('FYI, you were issued UID {}'.format(uid))
    session['username'] = username
    session['uid'] = uid
    session['logged_in'] = True
    session['visits'] = 1
    return redirect( url_for('viewProfile' ) ) #, username=username) )