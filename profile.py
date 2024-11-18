from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import secrets

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/profile/<username>', methods = ['GET', 'POST'])
def profile(username):
    # Check if the user is logged in and if the username in session matches their username
    if 'logged_in' not in session or session['username'] != username:
        flash('Unauthorized access. Please log in.')
        return redirect(url_for('login'))

    # Database connection
    conn = dbi.connect()
    curs = dbi.cursor(conn)

    if request.method == "POST":
        # Profile updates
        new_username = request.form.get('username') # should we allow for username change?
        new_password1 = request.form.get('password1')
        new_password2 = request.form.get('password2')

        if new_password1 != new_password2:
            flash('Passwords do not match.')
            return redirect(url_for('profile', username=username))

        hashed_password = bcrypt.hashpw(new_password1.encode('utf-8'),
                                        bcrypt.gensalt()).decode('utf-8')
    
        try:
            # Update username and password
            curs.execute('''UPDATE userpass 
                            SET username = %s, hashed = %s 
                            WHERE uid = %s''',
                            [new_username, hashed_password, session['uid']])
            conn.commit()

        # Update session
            session['username'] = new_username
            flash('Profile updated successfully.')
        except Exception as err:
            flash(f'Error updating profile: {repr(err)}')
            return redirect(url_for('profile', username=username))

        return redirect(url_for('profile', username=new_username))

    else:
        # Fetch current user details for display
        curs.execute('''SELECT username 
                        FROM userpass 
                        WHERE uid = %s''',
                     [session['uid']])
        user_data = curs.fetchone()

        if not user_data:
            flash('User not found.')
            return redirect(url_for('login'))

    return render_template('profile.html', username=user_data['username'])

@app.route('/delete/', methods = ['POST'])
def delete():
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

    return redirect(url_for('join'))