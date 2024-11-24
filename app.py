from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite


# import cs304dbi_sqlite3 as dbi
from werkzeug.utils import secure_filename
import secrets
import homepage as homepage
import login as login

import cs304dbi as dbi


#for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5*1024*1024 # 5 MB

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
    flash('Budget and max_number of roomates should be integers')

    

@app.route('/feed/', methods=["GET", "POST"])
def viewPosts():
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