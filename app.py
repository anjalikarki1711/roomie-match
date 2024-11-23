from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import sys, os, random
import imghdr

import secrets

app.secret_key = ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for _ in range(20)])
app.config['UPLOADS'] = 'uploads/profile_pics'  # Directory for profile picture uploads
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # Max file size: 1 MB

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

from flask import g

@app.route('/test-login')
def test_login():
    # Set session to simulate logged-in user
    session['uid'] = 1
    flash("Logged in as Ella Bates for testing purposes.")
    return redirect(url_for('viewProfile'))

@app.before_request
def start():
    # Only initialize once using a flag stored in 'g'
    if not hasattr(g, 'initialized'):
        dbi.cache_cnf()
        g.initialized = True

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

""" @app.route('/profile/', methods=["GET", "POST"])
def viewProfile():
    return render_template('viewProfile.html',
                           page_title='Profile')

@app.route('/editProfile/<uid>', methods=["GET", "POST"])
def editProfile():
    return render_template('editProfile.html',
                           page_title='Edit Profile') """

@app.route('/chat/', methods=["GET", "POST"])
def viewChat():
    return render_template('chat.html',
                           page_title='Chat History')


# Code using login
""" @app.route('/profile/', methods=["GET", "POST"])
def viewProfile():
    user_id = session.get('uid')
    if not user_id:
        flash("You must log in to view the profile.")
        return redirect(url_for('login'))

    # Connect to the database
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)

    # Fetch user information
    curs.execute('SELECT user_id, username, profile_pic, profile_desc, location, hobbies FROM user WHERE user_id = %s', [user_id])
    user = curs.fetchone()

    if user:
        # Fetch profile picture
        profile_pic = None
        if user['profile_pic']:
            profile_pic = url_for('pic', filename=user['profile_pic'])

        return render_template('viewProfile.html', user=user, profile_pic=profile_pic)
    else:
        flash("User not found.")
        return redirect(url_for('index')) """

""" @app.route('/upload-profile-pic/', methods=["POST"])
def upload_profile_pic():
    user_id = session.get('uid')
    if not user_id:
        flash("Please log in to upload a profile picture.")
        return redirect(url_for('viewProfile'))

    file = request.files['profile_pic']
    if file:
        # Secure the file name and save it to the uploads directory
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOADS'], filename)
        file.save(filepath)

        # Store the filename in the database
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        curs.execute('''INSERT INTO file (user_id, profile_pic)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE profile_pic = %s''', 
                     [user_id, filename, filename])
        conn.commit()

        flash("Profile picture uploaded successfully!")
    return redirect(url_for('viewProfile')) """

@app.route('/pic/<filename>')
def pic(filename):
    return send_from_directory(app.config['UPLOADS'], filename)

""" @app.route('/edit-profile/', methods=["GET", "POST"])
def editProfile():
    user_id = session.get('uid')
    if not user_id:
        flash("You must log in to edit the profile.")
        return redirect(url_for('login'))

    if request.method == "POST":
        new_desc = request.form.get('profile_desc')
        new_location = request.form.get('location')
        new_hobbies = request.form.get('hobbies')

        conn = dbi.connect()
        curs = dbi.cursor(conn)

        try:
            curs.execute('UPDATE user SET profile_desc = %s, location = %s, hobbies = %s WHERE user_id = %s',
                         [new_desc, new_location, new_hobbies, user_id])
            conn.commit()
            flash("Profile updated successfully!")
            return redirect(url_for('viewProfile'))
        except Exception as e:
            flash(f"Error updating profile: {e}")
    
    # Show the form to edit
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('SELECT profile_desc, location, hobbies FROM user WHERE user_id = %s', [user_id])
    user = curs.fetchone()

    return render_template('editProfile.html', user=user) """

""" @app.route('/edit-profile-desc/', methods=["POST"])
def edit_profile_desc():
    user_id = session.get('uid')
    new_desc = request.form.get('profile_desc')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET profile_desc = %s WHERE user_id = %s',
                     [new_desc, user_id])
        conn.commit()
        flash("Profile description updated successfully!")
    except Exception as e:
        flash(f"Error updating profile description: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-location/', methods=["POST"])
def edit_location():
    user_id = session.get('uid')
    new_location = request.form.get('location')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET location = %s WHERE user_id = %s',
                     [new_location, user_id])
        conn.commit()
        flash("Location updated successfully!")
    except Exception as e:
        flash(f"Error updating location: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-hobbies/', methods=["POST"])
def edit_hobbies():
    user_id = session.get('uid')
    new_hobbies = request.form.get('hobbies')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET hobbies = %s WHERE user_id = %s',
                     [new_hobbies, user_id])
        conn.commit()
        flash("Hobbies updated successfully!")
    except Exception as e:
        flash(f"Error updating hobbies: {e}")
    return redirect(url_for('viewProfile'))
 """
""" @app.route('/delete_account/', methods = ['POST'])
def delete_account():
    # Check if the user is logged in
    if 'logged_in' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    # Establish connection
    conn = dbi.connect()
    curs = dbi.cursor(conn)

    try:
        # Delete user account from the database
        curs.execute('DELETE FROM userpass WHERE uid = %s', [session['uid']])
        conn.commit()

        # Clear the session
        session.clear()
        flash('Your account has been deleted successfully.')
    except Exception as err:
        flash(f'Error deleting account: {repr(err)}')
        return redirect(url_for('profile', username=session['username']))

    return redirect(url_for('join')) """

# Code NOT using login
@app.route('/profile/', methods=["GET", "POST"])
def viewProfile():
    user_id = session.get('uid')
    if not user_id:
        flash("You must log in to view the profile.")
        return redirect(url_for('index'))  # Redirecting to home instead of login

    # Connect to the database
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)

    # Fetch user information
    curs.execute('SELECT user_id, username, profile_pic, profile_desc, location, hobbies FROM user WHERE user_id = %s', [user_id])
    user = curs.fetchone()

    if user:
        # Fetch profile picture if available
        profile_pic = None
        if user['profile_pic']:
            profile_pic = url_for('pic', filename=user['profile_pic'])

        return render_template('viewProfile.html', user=user, profile_pic=profile_pic)
    else:
        flash("User not found.")
        return redirect(url_for('index'))

@app.route('/edit-profile/', methods=["GET", "POST"])
def editProfile():
    user_id = session.get('uid')
    if not user_id:
        flash("You must log in to edit the profile.")
        return redirect(url_for('index'))  # Redirecting to home instead of login

    if request.method == "POST":
        new_desc = request.form.get('profile_desc')
        new_location = request.form.get('location')
        new_hobbies = request.form.get('hobbies')

        conn = dbi.connect()
        curs = dbi.cursor(conn)

        try:
            curs.execute('UPDATE user SET profile_desc = %s, location = %s, hobbies = %s WHERE user_id = %s',
                         [new_desc, new_location, new_hobbies, user_id])
            conn.commit()
            flash("Profile updated successfully!")
            return redirect(url_for('viewProfile'))
        except Exception as e:
            flash(f"Error updating profile: {e}")

    # Show the form to edit
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('SELECT profile_desc, location, hobbies FROM user WHERE user_id = %s', [user_id])
    user = curs.fetchone()

    return render_template('editProfile.html', user=user)

@app.route('/upload-profile-pic/', methods=["POST"])
def upload_profile_pic():
    user_id = session.get('uid')
    if not user_id:
        flash("Please log in to upload a profile picture.")
        return redirect(url_for('viewProfile'))

    file = request.files['profile_pic']
    if file:
        # Secure the file name and save it to the uploads directory
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOADS'], filename)
        file.save(filepath)

        # Store the filename in the database
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        curs.execute('''UPDATE user SET profile_pic = %s WHERE user_id = %s''', [filename, user_id])
        conn.commit()

        flash("Profile picture uploaded successfully!")
    return redirect(url_for('viewProfile'))

@app.route('/edit-profile-desc/', methods=["POST"])
def edit_profile_desc():
    user_id = session.get('uid')
    new_desc = request.form.get('profile_desc')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET profile_desc = %s WHERE user_id = %s',
                     [new_desc, user_id])
        conn.commit()
        flash("Profile description updated successfully!")
    except Exception as e:
        flash(f"Error updating profile description: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-location/', methods=["POST"])
def edit_location():
    user_id = session.get('uid')
    new_location = request.form.get('location')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET location = %s WHERE user_id = %s',
                     [new_location, user_id])
        conn.commit()
        flash("Location updated successfully!")
    except Exception as e:
        flash(f"Error updating location: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-hobbies/', methods=["POST"])
def edit_hobbies():
    user_id = session.get('uid')
    new_hobbies = request.form.get('hobbies')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET hobbies = %s WHERE user_id = %s',
                     [new_hobbies, user_id])
        conn.commit()
        flash("Hobbies updated successfully!")
    except Exception as e:
        flash(f"Error updating hobbies: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/delete_account/', methods=['POST'])
def delete_account():
    if 'logged_in' not in session:
        flash('You need to log in first.')
        return redirect(url_for('index'))  # Redirecting to home instead of login

    # Establish connection
    conn = dbi.connect()
    curs = dbi.cursor(conn)

    try:
        # Delete user account from the database
        curs.execute('DELETE FROM userpass WHERE uid = %s', [session['uid']])
        conn.commit()

        # Clear the session
        session.clear()
        flash('Your account has been deleted successfully.')
    except Exception as err:
        flash(f'Error deleting account: {repr(err)}')
        return redirect(url_for('viewProfile'))

    return redirect(url_for('index'))  # Redirecting to home instead of login

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