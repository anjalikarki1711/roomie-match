from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
import sys, os, random
import bcrypt
import secrets
from werkzeug.utils import secure_filename
import homepage as homepage
import login as login
from flask import g

app.secret_key = ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for _ in range(20)])
app.config['UPLOADS'] = os.path.expanduser('~/cs304/roomie-match/uploads/profile_pics')  # Directory for profile picture uploads
app.config['MAX_CONTENT_LENGTH'] = 5*1024*1024 # 5 MB

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True


""" @app.route('/test-login')
def test_login():
    # Set session to simulate logged-in user
    session['uid'] = 1
    flash("Logged in as Ella Bates for testing purposes.")
    return redirect(url_for('viewProfile')) """

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
    if 'user_id' in session:
        uid = session['user_id']
        if request.method == 'GET':
            return render_template('makePosts.html',
                            page_title='Make a Post')
        else: 
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)
            #use last_inserted_id to get the post id
            curs.execute('''
                        select last_insert_id''')
            pidDict = curs.fetchone()
            pid = pidDict['last_insert_id()']
            #retrieves form data 
            p_type = request.form.get('post_type')
            h_type = request.form.get('housing_type')
            rent = request.form.get('budget')
            roommatesNum = request.form.get('max_roommates')
            sbed = request.form.get('shared_bedroom')
            sbath = request.form.get('mshared_bathroom')
            pets = request.form.get('ok_with_pets')
            description = request.form.get("descr")
            f = request.files['pic']
            user_filename = f.filename
            ext = user_filename.split('.')[-1]
            filename = secure_filename('{}_{}.{}'.format(pid, uid, ext))
            pathname = os.path.join(app.config['UPLOADS'],filename)
            f.save(pathname)

        #insert into the database
        #checks wether the inputs are integers
            if homepage.isInt(rent) and homepage.isInt(roommatesNum):
                curs.execute(
                    '''insert into post(user_id, shared_bathroom, shared_bedroom, 
                    ok_with_pets, max_roommates, budget, housing_type, post_type) 
                    values (%s,%s,%s,%s,%s,%s,%s,%s)''',
                    [uid, sbath, sbed, pets, roommatesNum, rent, h_type, p_type])

                curs.execute(
                    '''insert into file(user_id, post_id, room_pic) values (%s,%s, %s)
                        ''', [uid, pid, filename])
                conn.commit()
                flash('Post successful')
                return redirect(url_for('viewPosts'))
            else:
                flash('Budget and max_number of roomates should be integers')
    else:
        flash('Please log in to continue!') 
        return redirect(url_for('index'))

@app.route('/feed/', methods=["GET", "POST"])
def viewPosts():
    #Only allow logged in users to view the feed
    if 'user_id' in session:
        conn = dbi.connect()
        posts = homepage.getPostDetails(conn)
        print(posts)
    
        if posts:
            for info in posts:
                userInfo = homepage.getUser(conn, info['user_id'])
                info['name'] = userInfo['name']
                # print(userInfo)
                # print(info)

            return render_template('feed.html',
                            page_title='Posts',
                            allPosts = posts)
    #If they are not logged in, redirect to log in page with a message
    else:
        flash('You must be logged in to view the posts!')
        return redirect(url_for('index'))

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
@app.route('/profile/', methods=["GET", "POST"])
def viewProfile():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to view the profile.")
        return redirect(url_for('login'))

    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    
    # Fetch user information
    curs.execute('SELECT user_id, name, gender, age, profession, profile_desc, location, pets, hobbies, seeking FROM user WHERE user_id = %s', [user_id])
    user = curs.fetchone()
    
    # Fetch profile picture
    curs.execute('SELECT file_id, profile_pic_filename FROM file WHERE user_id = %s', [user_id])
    profile_pic_data = curs.fetchone()

    if user:
        if profile_pic_data:
            profile_pic_filename = profile_pic_data['profile_pic_filename']
            profile_pic = url_for('pic', file_id=profile_pic_data['file_id'])
        else:
            profile_pic = None
        
        # Render the profile page after gathering the data
        return render_template('viewProfile.html', user=user, profile_pic=profile_pic)
    else:
        flash("User not found.")
        return redirect(url_for('index'))

@app.route('/prof_pic/<file_id>')
def pic(file_id):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    numrows = curs.execute(
        '''select profile_pic_filename from file where file_id = %s''',
        [file_id])
    if numrows == 0:
        flash('No picture for {}'.format(file_id))
        return redirect(url_for('index'))
    row = curs.fetchone()
    return send_from_directory(app.config['UPLOADS'],row['profile_pic_filename'])

@app.route('/upload-profile-pic/', methods=["POST"])
def upload_profile_pic():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to upload a profile picture.")
        return redirect(url_for('viewProfile'))

    conn = dbi.connect()
    curs = dbi.cursor(conn)

    # Check if the user already has a profile picture
    curs.execute('SELECT file_id, profile_pic_filename FROM file WHERE user_id = %s', [user_id])
    existing_file = curs.fetchone()

    if 'file' not in request.files:
        flash("No file part.")
        return redirect(url_for('viewProfile'))

    f = request.files['file']
    if f.filename == '':
        flash("No selected file.")
        return redirect(url_for('viewProfile'))

    filename = secure_filename(f.filename)
    file_path = os.path.join(app.config['UPLOADS'], filename)
    f.save(file_path)

    try:
        if existing_file:
            # Update existing profile picture
            curs.execute('UPDATE file SET profile_pic_filename = %s WHERE user_id = %s', [filename, user_id])
        else:
            # Insert new profile picture record
            curs.execute('INSERT INTO file (user_id, profile_pic_filename) VALUES (%s, %s)', [user_id, filename])

        conn.commit()  # Commit changes to the database
        flash("Profile picture uploaded successfully!")
    except Exception as e:
        flash(f"An error occurred while saving the file: {e}")
        return redirect(url_for('viewProfile'))

    return redirect(url_for('viewProfile'))

@app.route('/delete-profile-pic/', methods=["POST"])
def delete_profile_pic():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to delete your profile picture.")
        return redirect(url_for('viewProfile'))

    conn = dbi.connect()
    curs = dbi.cursor(conn)

    try:
        # Fetch and delete the file from the file system
        curs.execute('SELECT profile_pic_filename FROM file WHERE user_id = %s', [user_id])
        profile_pic_file = curs.fetchone()

        if profile_pic_file:
            filename = profile_pic_file[0]  # Accessing the filename by index
            file_path = os.path.join(app.config['UPLOADS'], filename)

            if os.path.exists(file_path):
                os.remove(file_path)

            # Remove the file record from the database
            curs.execute('DELETE FROM file WHERE user_id = %s', [user_id])
            conn.commit()  # Commit after deleting the file record
            flash("Profile picture deleted successfully.")
        else:
            flash("No profile picture to delete.")
    except Exception as e:
        flash(f"An error occurred while deleting the profile picture: {e}")
        conn.rollback()  # Rollback in case of an error

    return redirect(url_for('viewProfile'))


@app.route('/delete_account/', methods=['POST'])
def delete_account():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to delete your account.")
        return redirect(url_for('login'))

    conn = dbi.connect()
    curs = dbi.cursor(conn)

    try:
        # Call delete_profile_pic to remove the profile picture
        delete_profile_pic()

        # Delete the user's account record from the database
        curs.execute('DELETE FROM user WHERE user_id = %s', [user_id])
        curs.execute('DELETE FROM login WHERE user_id = %s', [user_id])
        conn.commit()

        # Clear the user's session
        session.clear()

        flash("Account and profile picture deleted successfully.")
        return redirect(url_for('join'))
    except Exception as e:
        flash(f"Error deleting account: {e}")
        return redirect(url_for('viewProfile'))

@app.route('/edit-profile/', methods=["GET", "POST"])
def editProfile():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to edit the profile.")
        return redirect(url_for('login'))

    if request.method == "POST":
        new_name = request.form.get('name')
        new_gender = request.form.get('gender')
        new_age = request.form.get('age')
        new_profession = request.form.get('profession')
        new_location = request.form.get('location')
        new_desc = request.form.get('profile_desc')
        new_pets = request.form.get('pets')
        new_hobbies = request.form.get('hobbies')
        new_seeking = request.form.get('seeking')

        conn = dbi.connect()
        curs = dbi.cursor(conn)

        try:
            curs.execute('UPDATE user SET name = %s, gender = %s, age = %s, profession = %s, location = %s, profile_desc = %s, pets = %s, hobbies = %s, seeking = %s WHERE user_id = %s',
                         [new_name, new_gender, new_age, new_profession, new_location, new_desc, new_pets, new_hobbies, new_seeking, user_id])
            conn.commit()
            flash("Profile updated successfully!")
            return redirect(url_for('viewProfile'))
        except Exception as e:
            flash(f"Error updating profile: {e}")
    
    # Show the form to edit
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('SELECT name, gender, age, profession, location, profile_desc, pets, hobbies, seeking FROM user WHERE user_id = %s', [user_id])
    user = curs.fetchone()

    return render_template('editProfile.html', user=user)

@app.route('/edit-profile-desc/', methods=["POST"])
def edit_profile_desc():
    user_id = session.get('user_id')
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
    user_id = session.get('user_id')
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
    user_id = session.get('user_id')
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

@app.route('/edit-name/', methods=["POST"])
def edit_name():
    user_id = session.get('user_id')
    new_name = request.form.get('name')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET name = %s WHERE user_id = %s',
                     [new_name, user_id])
        conn.commit()
        flash("Name updated successfully!")
    except Exception as e:
        flash(f"Error updating name: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-gender/', methods=["POST"])
def edit_gender():
    user_id = session.get('user_id')
    new_gender = request.form.get('gender')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET gender = %s WHERE user_id = %s',
                     [new_gender, user_id])
        conn.commit()
        flash("Gender updated successfully!")
    except Exception as e:
        flash(f"Error updating gender: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-age/', methods=["POST"])
def edit_age():
    user_id = session.get('user_id')
    new_age = request.form.get('age')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET age = %s WHERE user_id = %s',
                     [new_age, user_id])
        conn.commit()
        flash("Age updated successfully!")
    except Exception as e:
        flash(f"Error updating age: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-profession/', methods=["POST"])
def edit_profession():
    user_id = session.get('user_id')
    new_profession = request.form.get('profession')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET profession = %s WHERE user_id = %s',
                     [new_age, user_id])
        conn.commit()
        flash("Profession updated successfully!")
    except Exception as e:
        flash(f"Error updating profession: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-pets/', methods=["POST"])
def edit_pets():
    user_id = session.get('user_id')
    new_pets = request.form.get('pets')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET pets = %s WHERE user_id = %s',
                     [new_pets, user_id])
        conn.commit()
        flash("Pets updated successfully!")
    except Exception as e:
        flash(f"Error updating pets: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-seeking/', methods=["POST"])
def edit_seeking():
    user_id = session.get('user_id')
    new_seeking = request.form.get('seeking')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('UPDATE user SET seeking = %s WHERE user_id = %s',
                     [new_seeking, user_id])
        conn.commit()
        flash("Seeking updated successfully!")
    except Exception as e:
        flash(f"Error updating seeking: {e}")
    return redirect(url_for('viewProfile'))

# Code NOT using login
# @app.route('/profile/', methods=["GET", "POST"])
# def viewProfile():
#     user_id = session.get('uid')
#     if not user_id:
#         flash("You must log in to view the profile.")
#         return redirect(url_for('index'))  # Redirecting to home instead of login

#     # Connect to the database
#     conn = dbi.connect()
#     curs = dbi.dict_cursor(conn)

#     # Fetch user information
#     curs.execute('SELECT user_id, username, profile_pic, profile_desc, location, hobbies FROM user WHERE user_id = %s', [user_id])
#     user = curs.fetchone()

#     if user:
#         # Fetch profile picture if available
#         profile_pic = None
#         if user['profile_pic']:
#             profile_pic = url_for('pic', filename=user['profile_pic'])

#         return render_template('viewProfile.html', user=user, profile_pic=profile_pic)
#     else:
#         flash("User not found.")
#         return redirect(url_for('index'))

# @app.route('/edit-profile/', methods=["GET", "POST"])
# def editProfile():
#     user_id = session.get('uid')
#     if not user_id:
#         flash("You must log in to edit the profile.")
#         return redirect(url_for('index'))  # Redirecting to home instead of login

#     if request.method == "POST":
#         new_desc = request.form.get('profile_desc')
#         new_location = request.form.get('location')
#         new_hobbies = request.form.get('hobbies')

#         conn = dbi.connect()
#         curs = dbi.cursor(conn)

#         try:
#             curs.execute('UPDATE user SET profile_desc = %s, location = %s, hobbies = %s WHERE user_id = %s',
#                          [new_desc, new_location, new_hobbies, user_id])
#             conn.commit()
#             flash("Profile updated successfully!")
#             return redirect(url_for('viewProfile'))
#         except Exception as e:
#             flash(f"Error updating profile: {e}")

#     # Show the form to edit
#     conn = dbi.connect()
#     curs = dbi.dict_cursor(conn)
#     curs.execute('SELECT profile_desc, location, hobbies FROM user WHERE user_id = %s', [user_id])
#     user = curs.fetchone()

#     return render_template('editProfile.html', user=user)

# @app.route('/upload-profile-pic/', methods=["POST"])
# def upload_profile_pic():
#     user_id = session.get('uid')
#     if not user_id:
#         flash("Please log in to upload a profile picture.")
#         return redirect(url_for('viewProfile'))

#     file = request.files['profile_pic']
#     if file:
#         # Secure the file name and save it to the uploads directory
#         filename = secure_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOADS'], filename)
#         file.save(filepath)

#         # Store the filename in the database
#         conn = dbi.connect()
#         curs = dbi.dict_cursor(conn)
#         curs.execute('''UPDATE user SET profile_pic = %s WHERE user_id = %s''', [filename, user_id])
#         conn.commit()

#         flash("Profile picture uploaded successfully!")
#     return redirect(url_for('viewProfile'))

# @app.route('/edit-profile-desc/', methods=["POST"])
# def edit_profile_desc():
#     user_id = session.get('uid')
#     new_desc = request.form.get('profile_desc')
#     conn = dbi.connect()
#     curs = dbi.cursor(conn)
#     try:
#         curs.execute('UPDATE user SET profile_desc = %s WHERE user_id = %s',
#                      [new_desc, user_id])
#         conn.commit()
#         flash("Profile description updated successfully!")
#     except Exception as e:
#         flash(f"Error updating profile description: {e}")
#     return redirect(url_for('viewProfile'))

# @app.route('/edit-location/', methods=["POST"])
# def edit_location():
#     user_id = session.get('uid')
#     new_location = request.form.get('location')
#     conn = dbi.connect()
#     curs = dbi.cursor(conn)
#     try:
#         curs.execute('UPDATE user SET location = %s WHERE user_id = %s',
#                      [new_location, user_id])
#         conn.commit()
#         flash("Location updated successfully!")
#     except Exception as e:
#         flash(f"Error updating location: {e}")
#     return redirect(url_for('viewProfile'))

# @app.route('/edit-hobbies/', methods=["POST"])
# def edit_hobbies():
#     user_id = session.get('uid')
#     new_hobbies = request.form.get('hobbies')
#     conn = dbi.connect()
#     curs = dbi.cursor(conn)
#     try:
#         curs.execute('UPDATE user SET hobbies = %s WHERE user_id = %s',
#                      [new_hobbies, user_id])
#         conn.commit()
#         flash("Hobbies updated successfully!")
#     except Exception as e:
#         flash(f"Error updating hobbies: {e}")
#     return redirect(url_for('viewProfile'))

# @app.route('/delete_account/', methods=['POST'])
# def delete_account():
#     if 'logged_in' not in session:
#         flash('You need to log in first.')
#         return redirect(url_for('index'))  # Redirecting to home instead of login

#     # Establish connection
#     conn = dbi.connect()
#     curs = dbi.cursor(conn)

#     try:
#         # Delete user account from the database
#         curs.execute('DELETE FROM userpass WHERE uid = %s', [session['uid']])
#         conn.commit()

#         # Clear the session
#         session.clear()
#         flash('Your account has been deleted successfully.')
#     except Exception as err:
#         flash(f'Error deleting account: {repr(err)}')
#         return redirect(url_for('viewProfile'))

#     return redirect(url_for('index'))  # Redirecting to home instead of login

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