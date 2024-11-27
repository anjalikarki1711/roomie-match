from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app

from werkzeug.utils import secure_filename
import cs304dbi as dbi
import os
import homepage as homepage
import login as login
from flask import g

"""
This function looks up a profile picture based on it's file id and returns a webpage with the profile picture associated with that id.

Input: file id

It executes a query that gets a given file name based on a file id. It then gets the picture associated with the given filename.

Return: A specifi profile picture
"""
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


"""
The viewProfile function handles the display of the users profile. 
It supports both GET and POST requests. Users must be logged in to access this functionality.

If it receives a GET or POST request: It retrieves the users information and profile picture from the database. 
If the user is found, it renders the viewProfile.html template with the users data and profile picture. 
If the user is not found, it displays an error message and redirects to the index page.

Returns: the viewProfile.html template with the users data and profile picture if the user 
is logged in, or redirects to the login page with an error message if the user is not logged in.
"""
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



"""
The upload_profile_pic function handles the uploading of a user’s profile picture. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It checks if the user is logged in. If not, it 
displays an error message and redirects to the view profile page. If the user is logged in, 
it checks if the user already has a profile picture. It then processes the uploaded file, saves it 
to the uploads directory, and updates or inserts the profile picture record in the database. If the 
upload is successful, it displays a success message and redirects to the view profile page. If an error occurs, 
it displays an error message and redirects to the view profile page.

Returns: a redirect to the view profile page after processing the upload.
"""
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

"""
The delete_profile_pic function handles the deletion of a users profile picture. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It checks if the user is logged in. If not, it displays 
an error message and redirects to the view profile page. If the user is logged in, it 
fetches the profile picture filename from the database and deletes the file from the file system. 
It then removes the file record from the database. If the deletion is successful, it displays a success 
message and redirects to the view profile page. If an error occurs, it displays an error message and rolls back the transaction.

Returns: a redirect to the view profile page after processing the deletion.
"""
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

"""
The delete_account function handles the deletion of a users account. It supports POST requests. 
Users must be logged in to access this functionality.

If it receives a POST request: It checks if the user is logged in. If not, it displays an error 
message and redirects to the login page. If the user is logged in, it calls the delete_profile_pic function 
to remove the users profile picture. It then deletes the users account and login records from the database, 
commits the changes, and clears the users session. If the deletion is successful, it displays a success message 
and redirects to the join page. If an error occurs, it displays an error message and redirects to the view profile page.

Returns: a redirect to the join page after processing the deletion, or to the view profile page if an error occurs.
"""
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

"""
The editProfile function handles the editing of a user’s profile. It supports both GET and POST requests. 
Users must be logged in to access this functionality.

If it receives a GET request: It retrieves the user’s current profile information from the database and renders 
the editProfile.html template with the user’s data.

If it receives a POST request: It updates the user’s profile information in the database with the new data 
provided in the form and redirects to the view profile page with a success message.

Returns: the editProfile.html template with the user’s data if the user is logged in, or redirects to the 
login page with an error message if the user is not logged in.

"""
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


"""
The edit_profile_desc function handles the editing of a user’s profile description. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the user’s profile description in the database 
with the new description provided in the form and redirects to the view profile page with a success message.

Returns: redirect to the view profile page after processing the update.

"""
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

"""
The edit_location function handles the editing of a user’s location. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the users location in the database with the 
new location provided in the form and redirects to the view profile page with a success message.

Returns: a redirect to the view profile page after processing the update.
"""
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

"""
The edit_hobbies function handles the editing of a user’s hobbies. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the user’s hobbies in the database with the 
new hobbies provided in the form and redirects to the view profile page with a success message.

Returns: A redirect to the view profile page after processing the update.
"""
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

"""
The edit_name function handles the editing of a user’s name. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the user’s name in the database with the new 
name provided in the form and redirects to the view profile page with a success message.

Returns:redirect to the view profile page after processing the update.
"""
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

"""
The edit_gender function handles the editing of a user’s gender. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the user’s gender in the database with the new 
gender provided in the form and redirects to the view profile page with a success message.

Returns: redirect to the view profile page after processing the update.
"""
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

"""
The edit_age function handles the editing of a user’s age. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the user’s age in the database with the 
new age provided in the form and redirects to the view profile page with a success message.

Returns:  redirect to the view profile page after processing the update.
"""
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

"""
The edit_profession function handles the editing of a user’s profession. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the user’s profession in the database with 
the new profession provided in the form and redirects to the view profile page with a success message.

Returns:redirect to the view profile page after processing the update.
"""
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


"""
The edit_pets function handles the editing of a user’s pet preferences. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request:  It updates the user’s pet preferences in the database
with the new preferences provided in the form and redirects to the profile view page with a success message.

Returns: A redirect to the profile view page after processing the update.
"""
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

"""
The edit_seeking function handles the editing of a users seeking preferences. 
It supports POST requests. Users must be logged in to access this functionality.

If it receives a POST request: It updates the users seeking preferences in the database 
with the new preferences provided in the form and redirects to the profile view page with a success message.

Returns: A rediirect to the profile view page after processing the update.

"""
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