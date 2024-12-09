##Authors: Anjali Karki, Ali Bichanga, Flora Mukako, Indira Ruslanova

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)
import os
from werkzeug.utils import secure_filename
import secrets
import homepage as homepage
import login as login
import datetime
import cs304dbi as dbi


#for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 20*1024*1024 # 20 MB
# Directory for profile picture uploads
app.config['UPLOADS1'] = os.path.expanduser('~/cs304/roomie-match/uploads/profile_pics')  


app.secret_key = 'your secret here'
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True


@app.route('/')
def index():
    '''Route for rendering the home page'''
    return render_template('home.html',
                           page_title='Home Page')

###################################################################################################################
##Posts-related functions
@app.route('/makePost/', methods=["GET", "POST"])
def makePosts():
    '''
    Takes no parameter, 
    Allows users to create and submit a post and renders the feedpage
    '''
    if 'user_id' in session:
        uid = session['user_id']
        if request.method == 'GET':
            return render_template('makePosts.html',
                            page_title='Make a Post')
        else: 
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)

            #retrieves form data 
            p_type = request.form.get('post_type')
            h_type = request.form.get('housing_type')
            rent = request.form.get('budget')
            roommatesNum = request.form.get('max_roommates')
            sbed = request.form.get('shared_bedroom')
            sbath = request.form.get('shared_bathroom')
            pets = request.form.get('ok_with_pets')
            description = request.form.get("descr")
            pref_location = request.form.get("location")

            #insert into the database
            #checks wether the inputs are integers
            if homepage.isInt(rent) and homepage.isInt(roommatesNum):
                curs.execute(
                    '''insert into post(user_id, shared_bathroom, shared_bedroom, 
                    ok_with_pets, max_roommates, budget, housing_type, post_type, post_desc, location) 
                    values (%s,%s,%s,%s,%s,%s,%s,%s, %s, %s)''',
                    [uid, sbath, sbed, pets, roommatesNum, rent, h_type, p_type, description, pref_location])
                conn.commit()
                #use last_inserted_id to get the post id
                curs.execute('''
                            select last_insert_id() as pid''')
                pidDict = curs.fetchone()
                pid = pidDict['pid']

                if not os.path.exists('uploads'):
                    os.makedirs('uploads')

                if request.files['pic']:
                    f = request.files['pic']
                    user_filename = f.filename
                    ext = user_filename.split('.')[-1]
                    filename = secure_filename('{}_{}.{}'.format(pid, uid, ext))
                    pathname = os.path.join(app.config['UPLOADS'],filename)
                    f.save(pathname)
                
                curs.execute(
                    '''insert into file(user_id, post_id, room_pic_filename) values (%s,%s, %s)
                        ''', [uid, pid, filename])
                conn.commit()
                flash('Post successful')
                return redirect(url_for('viewPosts'))
            else:
                flash('Budget and max_number of roomates should be integers')
    else:
        flash('You must be logged in to make a post!') 
        return redirect(url_for('index'))

@app.route('/roompic/<file_id>')
def roompic(file_id):
    '''Takes an integer i.e. the file id number,
    Retrieves the room picture's filename with given file id,
    Returns a web page containing the room picture with given id'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    numrows = curs.execute(
        '''select room_pic_filename from file where file_id = %s''',
        [file_id])
    if numrows == 0:
        flash('No picture for {}'.format(file_id))
        return redirect(url_for('index'))
    row = curs.fetchone()
    return send_from_directory(app.config['UPLOADS'],row['room_pic_filename']) 

# @app.route('/feed/', methods=["GET", "POST"])
# def viewPosts():
#     '''Takes no parameter,
#     Allows user to view the feed with posts made by all users,
#     Returns the feed webpage'''
#     #Only allow logged in users to view the feed
#     if 'user_id' in session:
#         user_id = session.get('user_id')
#         conn = dbi.connect()
#         posts = homepage.getPostDetails(conn)
#         print(posts)
    
#         if posts:
#             for info in posts:
#                 userInfo = homepage.getUser(conn, info['user_id'])
#                 if userInfo['name'] != None:
#                     info['name'] = userInfo['name']
#                 else:
#                     info['name'] = "Unknown"
#             return render_template('feed.html',
#                             page_title='Posts',
#                             allPosts = posts,
#                             current_user_id = user_id)
#     #If they are not logged in, redirect to log in page with a message
#     else:
#         flash('You must be logged in to view the posts!')
#         return redirect(url_for('index'))

def addPostDetails (conn, posts):
    for info in posts:
                posted_time = info['posted_time']
                current_time = datetime.datetime.now()
                time_diff = (current_time - posted_time)
                daysago = time_diff.days
                info['time_diff'] = '< 1' if daysago < 1 else daysago
                userInfo = homepage.getUser(conn, info['user_id'])
                if userInfo['name'] != None:
                    info['name'] = userInfo['name']
                else:
                    info['name'] = "Unknown"
    return posts

"""
The viewPosts function handles the display of posts in the feed. 
It supports both GET and POST requests. Users must be logged in to access this functionality.

If it receives a GET request: It connects to the database and retrieves post details. 
For each post, it retrieves the user information and adds the users name to the post details. 
It then renders the feed.html template with the page title Posts and the list of all posts.

If it receives a POST request: It performs the same actions as a GET request.

Returns: the feed.html template with the list of posts if the user is logged in, 
or redirects to the index page with an error message if the user is not logged in.
"""
@app.route('/feed/', methods=["GET", "POST"])
def viewPosts():
    '''Takes no parameter,
    Allows user to view the feed with posts made by all users,
    Returns the feed webpage'''
    #Only allow logged in users to view the feed
    if 'user_id' in session:
        conn = dbi.connect()
        uid = session.get('user_id')
        h_options = homepage.getHousingOptions(conn)
        h_need = homepage.getHousingNeed(conn, uid)
        need = h_need["housing_need"]
        if need == 'housing':
            posts= homepage.filterPostDetails(conn, 'roommate')
        else:        
            posts= homepage.filterPostDetails(conn,'housing')

        if request.method == 'GET':
            newPosts = addPostDetails(conn,posts)
            return render_template('feed.html',
                                page_title='Posts',
                                allPosts = newPosts,
                                options = h_options,
                                current_user_id = uid
                                )
        if request.method == "POST":
            filter = request.form.get('filter')
            if filter == "both":
                posts = homepage.getPostDetails(conn)
            elif filter == "":
                flash('Choose one of the options')
            else:
                posts= homepage.filterPostDetails(conn, filter)
            print(posts)
            if posts:
                newPosts = addPostDetails(conn,posts)
                return render_template('feed.html',
                                page_title='Posts',
                                allPosts = newPosts,
                                h_needs = h_need,
                                options = h_options,
                                current_user_id = uid)

            flash('No posts available') 
            return redirect(url_for('viewPosts'))

    #If they are not logged in, redirect to log in page with a message
    else:
        flash('You must be logged in to view the posts!')
        return redirect(url_for('index'))

@app.route('/delete-post/<post_id>', methods=["GET", "POST"])
def delete_post(post_id):
    '''
    Takes an integer i.e. post_id as a parameter 
    Fetches the post from the database, allows users to delete a post
    Returns the feed page with updated posts
    '''
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to continue")
        return redirect(url_for('index'))
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        # Fetch and delete the file from the file system
        curs.execute('''SELECT room_pic_filename from file 
                     WHERE post_id = %s''', [post_id])
        pic = curs.fetchone()

        if pic:
            filename = pic[0]  # Accessing the filename by index
            file_path = os.path.join(app.config['UPLOADS'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            # Remove the file record from the database
            curs.execute('''delete from file where post_id = %s''', [post_id])
            conn.commit()  # Commit after deleting the file record

            curs.execute('''select * from post where post_id = %s''', [post_id])
            post = curs.fetchone()
            if post:
                # Remove the file record from the database
                curs.execute('''delete from post where post_id = %s''', [post_id])
                conn.commit()  # Commit after deleting the file record
                flash("Post deleted successfully.")
                return redirect(url_for('viewPosts'))
        else:
            flash("No post to delete.")
    except Exception as e:
        flash(f"An error occurred while deleting the post: {e}")
        conn.rollback()  # Rollback in case of an error

@app.route('/update_post/<post_id>/', methods=["GET", "POST"])
def updatePost(post_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to update the post.")
        return redirect(url_for('login'))
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    allPosts = homepage.getPostDetails(conn)
    filteredpost = []
    for post in allPosts:
        if post['post_id']==int(post_id):
            filteredpost.append(post)
    try:
        if request.method == "GET": 
                return render_template('makePosts.html',
                                page_title='Edit a Post',
                                post=filteredpost[0])       
        if request.method == "POST":
            #retrieves form data 
            p_type = request.form.get('post_type')
            h_type = request.form.get('housing_type')
            rent = request.form.get('budget')
            roommatesNum = request.form.get('max_roommates')
            sbed = request.form.get('shared_bedroom')
            sbath = request.form.get('shared_bathroom')
            pets = request.form.get('ok_with_pets')
            description = request.form.get("descr")
            pref_location = request.form.get("location")

            #checks wether the inputs are integers
            if homepage.isInt(rent) and homepage.isInt(roommatesNum):
                curs.execute(
                    '''UPDATE post
                    SET post_type = %s, housing_type = %s, budget = %s,
                        max_roommates = %s, shared_bedroom = %s,
                        shared_bathroom = %s, ok_with_pets = %s,
                        post_desc = %s, location = %s
                    WHERE post_id = %s''',
                    [p_type, h_type, rent, roommatesNum, sbed, sbath, pets, description, pref_location, post_id])
                conn.commit()

                if request.files['pic']:
                    f = request.files['pic']
                    user_filename = f.filename
                    ext = user_filename.split('.')[-1]
                    filename = secure_filename('{}_{}.{}'.format(post_id, user_id, ext))
                    pathname = os.path.join(app.config['UPLOADS'],filename)
                    f.save(pathname)
                
                    curs.execute(
                        '''update file set room_pic_filename = %s
                            where file_id=%s''', [filename, filteredpost[0]['file_id']])
                    conn.commit()
                flash('Post edited successfully')
            else:
                flash('Budget and max_number of roomates should be integers')
    except Exception as e:
            flash(f"Error updating post: {e}")
    return redirect(url_for('viewPosts'))
    
#######################################################################################################################

# Code related to profile feature
@app.route('/profile/', methods=["GET", "POST"])
def viewProfile():
    '''
    Takes no parameter,
    Allows user to view their profile with all their info associated,
    Returns the profile web page with all their details
    '''
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to view the profile.")
        return redirect(url_for('index'))

    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    
    # Fetch user information
    curs.execute('''SELECT user_id, name, gender, age, profession,
                  profile_desc, location, pets, hobbies, seeking 
                 FROM user WHERE user_id = %s''', [user_id])
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
        return render_template('viewProfile.html', user=user, profile_pic=profile_pic, page_title="Profile")
    else:
        flash("User not found.")
        return redirect(url_for('index'))

@app.route('/prof_pic/<file_id>')
def pic(file_id):
    '''
    Takes in an integer i.e. the file id,
    Looks up the profile picture's filename associated with the given file_id
    Returns a web page with the profile picture associated with given file_id'''
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
    '''
    Takes no parameter,
    Allows users to upload profile picture
    Returns a webpage with their profile details and new profile picture
    '''
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
    '''
    Allows users to delete a profile picture
    '''
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to delete your profile picture.")
        return redirect(url_for('viewProfile'))

    conn = dbi.connect()
    curs = dbi.cursor(conn)

    try:
        # Fetch and delete the file from the file system
        curs.execute('''SELECT profile_pic_filename 
                     FROM file WHERE user_id = %s''', [user_id])
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
    '''Allows users to delete their account from the app'''
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
    '''Allows user sto edit their profile details'''
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
            curs.execute('''UPDATE user 
                         SET name = %s, gender = %s, age = %s, profession = %s, 
                         location = %s, profile_desc = %s, pets = %s, hobbies = %s, 
                         seeking = %s WHERE user_id = %s''',
                         [new_name, new_gender, new_age, new_profession, new_location, 
                          new_desc, new_pets, new_hobbies, new_seeking, user_id])
            conn.commit()
            flash("Profile updated successfully!")
            return redirect(url_for('viewProfile'))
        except Exception as e:
            flash(f"Error updating profile: {e}")
    
    # Show the form to edit
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''SELECT name, gender, age, profession, location, 
                 profile_desc, pets, hobbies, seeking 
                 FROM user WHERE user_id = %s''', [user_id])
    user = curs.fetchone()

    return render_template('editProfile.html', user=user, page_title="Edit Profile")

@app.route('/edit-profile-desc/', methods=["POST"])
def edit_profile_desc():
    user_id = session.get('user_id')
    new_desc = request.form.get('profile_desc')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('''UPDATE user 
                     SET profile_desc = %s WHERE user_id = %s''',
                     [new_desc, user_id])
        conn.commit()
        flash("Profile description updated successfully!")
    except Exception as e:
        flash(f"Error updating profile description: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-location/', methods=["POST"])
def edit_location():
    '''
    Allows users to edit their location
    '''
    user_id = session.get('user_id')
    new_location = request.form.get('location')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('''UPDATE user 
                     SET location = %s 
                     WHERE user_id = %s''',
                     [new_location, user_id])
        conn.commit()
        flash("Location updated successfully!")
    except Exception as e:
        flash(f"Error updating location: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-hobbies/', methods=["POST"])
def edit_hobbies():
    '''
    Allows users to edit their hobbies
    '''
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
    '''
    Allows users to edit their name
    '''
    user_id = session.get('user_id')
    new_name = request.form.get('name')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('''UPDATE user 
                     SET name = %s 
                     WHERE user_id = %s''',
                     [new_name, user_id])
        conn.commit()
        flash("Name updated successfully!")
    except Exception as e:
        flash(f"Error updating name: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-gender/', methods=["POST"])
def edit_gender():
    '''
    Allows users to edit their gender
    '''
    user_id = session.get('user_id')
    new_gender = request.form.get('gender')
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('''UPDATE user 
                     SET gender = %s WHERE user_id = %s''',
                     [new_gender, user_id])
        conn.commit()
        flash("Gender updated successfully!")
    except Exception as e:
        flash(f"Error updating gender: {e}")
    return redirect(url_for('viewProfile'))

@app.route('/edit-age/', methods=["POST"])
def edit_age():
    '''
    Allows users to edit their age
    '''
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
    '''
    Allows users to edit their profession
    '''
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
    '''
    Allows users to edit their pet preference
    '''
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
    '''
    Allows users to edit what they are seeking
    '''
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
###################################################################################################################
#Yet to be implemented
@app.route('/chat/', methods=["GET", "POST"])
def viewChat():
    '''Shows the user's chat history and people - yet to be implemented'''
    if 'user_id' in session:
        return render_template('chat.html',
                           page_title='Chat History')
    else:
        flash('You must be logged in to use the Chat feature!')
        return redirect(url_for('index'))
###################################################################################################################
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