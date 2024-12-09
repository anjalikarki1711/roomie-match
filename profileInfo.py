from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from __main__ import app

from werkzeug.utils import secure_filename
import cs304dbi as dbi
import os
import homepage
import login
import queries as q

"""
This function looks up a profile picture based on it's file id and returns a webpage with the profile picture associated with that id.

Input: file id

It executes a query that gets a given file name based on a file id. It then gets the picture associated with the given filename.

Return: A specifi profile picture
"""
@app.route('/prof_pic/<file_id>')
def profpic(file_id):
    conn = dbi.connect()

    row = q.getFile(conn, file_id)
    if row == 0:
        flash('No picture for {}'.format(file_id))
        return redirect(url_for('index'))
    
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
    user = q.getUserInfo(conn, user_id) #curs.fetchone()
    

    # Fetch profile picture
    profile_pic_data = q.getProfpic(conn, user_id) #curs.fetchone()

    if user:
        if profile_pic_data:
            profile_pic_filename = profile_pic_data['profile_pic_filename']
            profile_pic = url_for('profpic', file_id=profile_pic_data['file_id'])
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
    #curs.execute('SELECT file_id, profile_pic_filename FROM file WHERE user_id = %s', [user_id])
    existing_file = q.getProfpic(conn, user_id) #curs.fetchone()

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

    confirm_delete = request.form.get('confirm_delete')
    if confirm_delete == "yes":
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
    else:
        return "Deletion not confirmed.", 400

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
@app.route('/update-profile/', methods=["GET", "POST"])
def updateProfile():
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

        # Validate inputs
        errors = []
        
        # Validate age (must be a number)
        try:
            new_age = int(new_age)
        except ValueError:
            errors.append("Age must be a number.")

        # Validate gender (check if it's one of the allowed values)
        if new_gender not in ['man', 'woman', 'nonbinary']:
            errors.append("Gender must be 'Man', 'Woman', or 'Nonbinary'.")

        # Check if name, age, and location are empty or just spaces
        if not new_name.strip():  # Checks if name is just spaces
            errors.append("Name cannot be empty or just spaces.")
        if not new_location.strip():  # Checks if location is just spaces
            errors.append("Location cannot be empty or just spaces.")

        # Check if profession, profile description, and hobbies are just spaces (but allow empty)
        if new_profession and not new_profession.strip():  # if profession is not empty but only contains spaces
            errors.append("Profession cannot be just spaces.")
        if new_desc and not new_desc.strip():  # if profile description is not empty but only contains spaces
            errors.append("Profile description cannot be just spaces.")
        if new_hobbies and not new_hobbies.strip():  # if hobbies is not empty but only contains spaces
            errors.append("Hobbies cannot be just spaces.")
        
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('viewProfile'))

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

@app.route('/edit-profile/', methods=["GET", "POST"])
def editProfile():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must log in to edit the profile.")
        return redirect(url_for('login'))

    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)

    if request.method == "POST":
        # Retrieve form values
        form_data = {
            "name": request.form.get("name"),
            "gender": request.form.get("gender"),
            "age": request.form.get("age"),
            "profession": request.form.get("profession"),
            "location": request.form.get("location"),
            "profile_desc": request.form.get("profile_desc"),
            "pets": request.form.get("pets"),
            "hobbies": request.form.get("hobbies"),
            "seeking": request.form.get("seeking"),
        }

        # Validate input types
        errors = []

        # Validate age (should be an integer)
        try:
            form_data["age"] = int(form_data["age"])
        except ValueError:
            errors.append("Age must be a number.")

        # Validate gender (should be 'Man', 'Woman', or 'Nonbinary')
        if form_data["gender"] not in ['man', 'woman', 'nonbinary']:
            errors.append("Gender must be 'Man', 'Woman', or 'Nonbinary'.")
        
        # Check if name, age, and location are empty or just spaces
        if not form_data["name"].strip():  # Checks if name is just spaces
            errors.append("Name cannot be empty or just spaces.")
        if not form_data["location"].strip():  # Checks if location is just spaces
            errors.append("Location cannot be empty or just spaces.")

        # Check if profession, profile description, and hobbies are just spaces (but allow empty)
        if form_data["profession"] and not form_data["profession"].strip():  # if profession is not empty but only contains spaces
            errors.append("Profession cannot be just spaces.")
        if form_data["profile_desc"] and not form_data["profile_desc"].strip():  # if profile description is not empty but only contains spaces
            errors.append("Profile description cannot be just spaces.")
        if form_data["hobbies"] and not form_data["hobbies"].strip():  # if hobbies is not empty but only contains spaces
            errors.append("Hobbies cannot be just spaces.")

        # # Check if name or profession is empty
        # if not form_data["name"] or not form_data["profession"]:
        #     errors.append("Name and profession must not be empty.")

        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('editProfile'))

    try:
        # Update all fields at once
        curs.execute('''
            UPDATE user 
            SET name = %s, gender = %s, age = %s, profession = %s, location = %s, 
                profile_desc = %s, pets = %s, hobbies = %s, seeking = %s 
            WHERE user_id = %s
        ''', [
            form_data["name"], form_data["gender"], form_data["age"], 
            form_data["profession"], form_data["location"], form_data["profile_desc"], 
            form_data["pets"], form_data["hobbies"], form_data["seeking"], 
            user_id
        ])
        conn.commit()
        flash("Profile updated successfully!")
        return redirect(url_for('viewProfile'))
    except Exception as e:
        flash(f"Error updating profile: {e}")
        conn.rollback()

    # Fetch current user data for GET request
    curs.execute('SELECT name, gender, age, profession, location, profile_desc, pets, hobbies, seeking FROM user WHERE user_id = %s', [user_id])
    user = curs.fetchone()
    
    return render_template('editProfile.html', user=user)