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
import profile as profile
import secrets
from flask import g

#for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 20*1024*1024 # 20 MB
# Directory for profile picture uploads
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
            sbath = request.form.get('mshared_bathroom')
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
        posts = homepage.getPostDetails(conn)
        print(posts)
    
        if posts:
            for info in posts:
                userInfo = homepage.getUser(conn, info['user_id'])
                if userInfo['name'] != None:
                    info['name'] = userInfo['name']
                else:
                    info['name'] = "Unknown"
            return render_template('feed.html',
                            page_title='Posts',
                            allPosts = posts)
    #If they are not logged in, redirect to log in page with a message
    else:
        flash('You must be logged in to view the posts!')
        return redirect(url_for('index'))
#######################################################################################################################

"""
The viewChat function handles the display of the chat history. It supports both GET and POST requests. 
Users must be logged in to access this functionality.

If it receives a GET request: It renders the chat.html template.

If it receives a POST request: It performs the same action as a GET request.

Returns: the chat.html template if the user is logged in, or redirects to the index page 
with an error message if the user is not logged in.
"""
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