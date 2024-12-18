##Authors: Anjali Karki, Ali Bichanga, Flora Mukako, Indira Ruslanova

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)


from werkzeug.utils import secure_filename
import cs304dbi as dbi
import sys, os
import homepage as homepage
import login as login

import datetime
import profile as profile
import queries as q
import secrets

#for file upload
# app.config['UPLOADS'] = os.path.expanduser('/students/roomie_match/uploads/')
app.config['UPLOADS'] = os.path.expanduser('~/cs304/roomie-match/uploads/')
app.config['MAX_CONTENT_LENGTH'] = 20*1024*1024 # 20 MB
# Directory for profile picture uploads
# app.config['UPLOADS1'] = os.path.expanduser('/students/roomie_match/uploads/profile_pics')  
app.config['UPLOADS1'] = os.path.expanduser('~/cs304/roomie-match/uploads/profile_pics')


app.secret_key = 'your secret here'
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True


"""
This route directs users to the homepage where they can choose to either login or sign up to this app
Returns: the template home.html
"""
@app.route('/')
def index():
    '''Route for rendering the home page'''
    return render_template('home.html',
                           page_title='Home Page')


"""
The makePosts function handles the creation of new posts by users. It supports both GET and POST requests. 
Users must be logged in to access this functionality.

If it receives a GET request: Renders the makePosts.html template with the page title “Make a Post”.
If it receives a POST request: It retrieves form data such as post type, housing type, budget, max roommates, shared bedroom, shared bathroom, 
pet preferences, a description and location of the post. This is the added to the database and it redirects to the view posts page.

It returns the makePosts.html from a GET request and it redirects to the viewPosts page from a successful POST request
"""
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
            
            conn = dbi.connect()
            curs = dbi.dict_cursor(conn)
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


"""
The roompic function handles the retrieval and display of a picture associated with a given file ID. 

Input: Users must provide a valid file_id.

If it receives a GET request: It connects to the database and retrieves the filename of the picture associated 
with the provided file_id. If no picture is found, it displays an error message and redirects to the index page. 
If a picture is found, it sends the file from the uploads directory.

Returns: the picture file from the uploads directory if found, or redirects to the index page if no picture is found.
"""
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

""" 
The addPostDetails function processes a list of posts to add additional details such as the time 
difference since the post was made and the name of the user who made the post. 

Input: conn: A database connection object. 
       posts: A list of dictionaries, where each dictionary contains information about a post, 
        including 'posted_time' and 'user_id'. 


For each post in the list: - Calculates the time difference between the
 current time and the time the post was made. - Adds a 'time_diff' key to the post 
 dictionary, indicating the number of days since the post was made. If the post was 
 
 made less than a day ago, 'time_diff' is set to '< 1'. It retrieves user information based 
 on 'user_id' and adds the user's name to the post dictionary. If the user's name is not available, 
 sets the name to "Unknown". 
 
 Returns: The updated list of posts with additional details. 
 """
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

"""
Parameter: post_id, a unique integer value assigned to each post
The delete_post function handles the deletion of a post and its associated file.

Users must be logged in to access this functionality. It supports both GET and POST requests.

If the user is not logged in: It redirects to the login page with an error message.

If the user is logged in:
- It connects to the database and retrieves the filename of the post's associated file.
- Deletes the file from the file system if it exists and removes its entry from the `file` table.
- Deletes the post entry from the `post` table.
- Displays a success message if the deletion is successful.

If an error occurs during the process, it rolls back the changes and displays an error message.

Returns: Redirects to the `viewPosts` page with updated posts if the deletion is successful, 
or redirects to the `viewPosts` page with an error message if the deletion fails.
"""
@app.route('/delete-post/<post_id>', methods=["GET", "POST"])
def delete_post(post_id):
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


"""
Parameter: post_id, a unique integer value assigned to each post
The updatePost function allows users to edit an existing post, with the option to update its associated picture.

Users must be logged in to access this functionality. It supports both GET and POST requests.

If the user is not logged in: It redirects to the login page with an error message.

If it receives a GET request:
- It connects to the database and retrieves the details of the specified post.
- Renders the `makePosts.html` template with the post details pre-filled for editing.

If it receives a POST request:
- It retrieves form data submitted by the user, including the updated post details.
- Validates that `budget` and `max_roommates` are integers.
- Updates the post details in the `post` table in the database.
- If a new picture is uploaded, it saves the file, updates its filename in the `file` table, and commits the changes.

If an error occurs during the update process, it displays an error message and rolls back any changes.

Returns: Redirects to the `viewPosts` page with a success message if the update is successful,
or with an error message if the update fails.
"""
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

""" 
The chatlist function handles the `/chatlist/` route and generates 
a list of people available for messaging. It retrieves the current 
user's ID from the session, fetches relevant data from the database, 
and renders the `chatlist.html` template with the list of people.
"""
@app.route('/chatlist/')
def chatList():
    user_id = session['user_id']
    conn = q.getConnection()
    allMessaging = q.peopleMessaging(conn, user_id)
    
    #display results
    return(render_template('chatlist.html', allPeople = allMessaging))


"""
The viewChat function handles the display of the chat history. It supports both GET and POST requests. 
Users must be logged in to access this functionality.

If it receives a GET request: It renders the chat.html template.

If it receives a POST request: It performs the same action as a GET request.

Returns: the chat.html template if the user is logged in, or redirects to the index page 
with an error message if the user is not logged in.
"""
@app.route('/chat/', methods=["GET"]) #, "POST"])
def viewChat():
    '''Shows the user's chat history and people - yet to be implemented'''
    #if 'user_id' in session:
        #return render_template('chat.html', page_title="Chat History")
    #'''Shows the user's chat history and people - yet to be implemented''')
    if 'user_id' in session:
        return redirect(url_for('chatList'))
    else:
        flash('You must be logged in to use the Chat feature!')
        flash('You must be logged in to use the Chat feature!')
        return redirect(url_for('index'))
###################################################################################################################
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