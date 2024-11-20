from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite


# import cs304dbi_sqlite3 as dbi
from werkzeug.utils import secure_filename
import secrets
import imghdr
import cs304dbi as dbi


# new for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5*1024*1024 # 5 MB

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

#helper functions
def getPostDetails(conn):
    '''gets post details from the database'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    posts = curs.execute('''select user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates,
            budget, housing_type, post_type from post ''')
    return curs.fetchall()



def getUser(conn, id):
    '''gets user's details '''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    userInfo = curs.execute('''select name, profile_desc from user inner join post
                            using(user_id) where user_id = %s''', [id])
    return curs.fetchone()

""" def insert_new_post(conn):
    '''Inserts new post data'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into post values(%s, %s, %s, %s)''', [], [], [], ) """



@app.route('/')
def index():
    return render_template('home.html',
                           page_title='Home Page')

@app.route('/makePost/', methods=["GET", "POST"])
def makePosts():
    return render_template('makePosts.html',
                           page_title='Make a Post')


@app.route('/insert-postData/', methods=['POST'])
def insert_new_post():
    p_type = request.form.get('post_type')
    h_type = request.form.get('housing_type')
    rent = request.form.get('budget')
    roommatesNum = request.form.get('max_roommates')
    sbed = request.form.get('shared_bedroom')
    sbath = request.form.get('mshared_bathroom')
    pets = request.form.get('ok_with_pets')
    description = request.form.get("descr")
    return render_template('successfulPost.html')

@app.route('/upload/', methods=["GET", "POST"])
def file_upload():
    f = request.files['pic']
    user_filename = f.filename
    ext = user_filename.split('.')[-1]
    filename = secure_filename('{}.{}'.format(nm,ext))
    pathname = os.path.join(app.config['UPLOADS'],filename)
    f.save(pathname)
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute(
        '''insert into picfile(nm,filename) values (%s,%s)
            on duplicate key update filename = %s''',
        [filename, filename])
    conn.commit()
    flash('Upload successful')

@app.route('/feed/', methods=["GET", "POST"])
def viewPosts():
    conn = dbi.connect()
    posts = getPostDetails(conn)
   
    if posts:
        for info in posts:
            userInfo = getUser(conn, info['user_id'])
    return render_template('feed.html',
                           page_title='Posts',
                            allPosts = posts,
                            userDetails = userInfo,
                            name = userInfo["name"],
                            prof_desc = userInfo['profile_desc'] )

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

# @app.route('/chat/<int:id>', methods=["GET", "POST"])
# def sendMessage(id):
#     conn = dbi.connect()
#     posts = getPostDetails(conn)
#     if posts:
#         for info in posts:
#             id = info['user_id']

#     return render_template('chat.html',
#                            page_title='Chat History')


@app.route('/processPost/', methods=["POST"])
def processPost():
    conn = dbi.connect()    
    return redirect(url_for('index'))

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