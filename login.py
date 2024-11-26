from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app

import bcrypt
import cs304dbi as dbi

@app.route('/sign-up/', methods=["GET", "POST"])
def join():
    if request.method == "GET":
        return render_template ("sign-up.html", page_title="Sign Up")

    
    else: 
        username = request.form.get('user-name')
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

@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template ("login.html", page_title="Log In")
    
    else: 
        username = request.form.get('username')
        passwd = request.form.get('password')
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        curs.execute('''SELECT user_id,user_name,hashed_password
                        FROM login
                        WHERE user_name = %s''',
                    [username])
        row = curs.fetchone()
        if row is None:
            # Same response as wrong password,
            # so no information about what went wrong
            flash('login incorrect. Try again or join')
            return redirect( url_for('login'))
        
        stored = row['hashed_password']
        print('database has stored: {} {}'.format(stored,type(stored)))
        print('form supplied passwd: {} {}'.format(passwd,type(passwd)))
        hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),
                                stored.encode('utf-8'))
        hashed2_str = hashed2.decode('utf-8')
        print('rehash is: {} {}'.format(hashed2_str,type(hashed2_str)))
        if hashed2_str == stored:
            print('they match!')
            flash('successfully logged in as '+username)
            session['username'] = username
            session['user_id'] = row['user_id']
            session['logged_in'] = True
            session['visits'] = 1
            return redirect( url_for('viewProfile' ) ) #, username=username) )
        else:
            flash('password incorrect. Try again or join')
            return redirect( url_for('join'))
        
@app.route('/logout/')
def logout():
    if 'username' in session:
        username = session['username']
        session.pop('username')
        session.pop('user_id')
        session.pop('logged_in')
        flash('You are logged out')
        return redirect(url_for('index'))
    else:
        flash('you are not logged in. Please login or join')
        return redirect( url_for('index') )
    
