# Roomie-match Homepage flask code 

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite


# import cs304dbi_sqlite3 as dbi
from werkzeug.utils import secure_filename
import secrets
import homepage

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import secrets

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
    posts = curs.execute('''select post.user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates,
            budget, housing_type, post_type, location, post_desc, room_pic_filename, file_id from post join file on post.post_id= file.post_id''')
    return curs.fetchall()

def getProfilePic(conn, postId):
    '''gets picture associated with the post from the database for the feed'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    picture = curs.execute('''select room_pic_filename from file where post_id = %s''', [postId])
    return curs.fetchone()
    



def getUser(conn, id):
    '''gets user's details '''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    userInfo = curs.execute('''select name, profile_desc from user inner join post
                            using(user_id) where user_id = %s''', [id])
    return curs.fetchone()

def isInt(var):
    try:
        var = int(var)
        return True
    except ValueError:
        return False

""" def insert_new_post(conn):
    '''Inserts new post data'''
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into post values(%s, %s, %s, %s)''', [], [], [], )
@app.route('/makePost/', methods=["GET", "POST"])
def makePosts():
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
    uid = session.get('user_id')
    f = request.files['pic']
    user_filename = f.filename
    ext = user_filename.split('.')[-1]
    filename = secure_filename('{}_{}.{}'.format(pid, uid, ext))
    pathname = os.path.join(app.config['UPLOADS'],filename)
    f.save(pathname)
    #insert into the database
    curs.execute('''insert into post(user_id, shared_bathroom, shared_bedroom, 
        ok_with_pets, max_roommates, budget, housing_type, post_type) 
        values (%s,%s,%s,%s,%s,%s,%s,%s)''',
        [uid, sbath, sbed, pets, roommatesNum, rent, h_type, p_type])

    curs.execute(
        '''insert into file(user_id, post_id, room_pic) values (%s,%s, %s)
            ''',
                [uid, pid, filename])
    conn.commit()
    flash('Post successful')
    return redirect(url_for('viewPosts'))



@app.route('/insert-postData/', methods=['POST'])
def insert_new_post():
    

@app.route('/feed/', methods=["GET", "POST"])
def viewPosts():
    conn = dbi.connect()
    posts = homepage.getPostDetails(conn)
   
    if posts:
        for info in posts:
            userInfo = homepage.getUser(conn, info['user_id'])
    return render_template('feed.html',
                           page_title='Posts',
                            allPosts = posts,
                            userDetails = userInfo,
                            name = userInfo["name"],
                            prof_desc = userInfo['profile_desc'] ) """