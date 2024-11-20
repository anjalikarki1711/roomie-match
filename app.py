from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite


# import cs304dbi_sqlite3 as dbi
import cs304dbi as dbi
import bcrypt

import secrets


app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/')
def index():
    return render_template('home.html',
                           page_title='Home Page')

@app.route('/makePost/', methods=["GET", "POST"])
def makePosts():
    return render_template('makePosts.html',
                           page_title='Make a Post')
@app.route('/feed/', methods=["GET", "POST"])
def viewPosts():
    return render_template('feed.html',
                           page_title='Posts')

@app.route('/profile/', methods=["GET", "POST"])
def viewProfile():
    return render_template('viewProfile.html',
                           page_title='Profile')

@app.route('/editProfile/<uid>', methods=["GET", "POST"])
def editProfile():
    return render_template('editProfile.html',
                           page_title='Edit Profile')

@app.route('/chat/', methods=["GET", "POST"])
def viewChat():
    return render_template('chat.html',
                           page_title='Chat History')

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
                            VALUES(%s,%s)''',
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
        

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'roomie_match_db' 
    print(f'will connect to {db_to_use}')
    dbi.conf(db_to_use)
    app.debug = True
    app.run('0.0.0.0',port)
