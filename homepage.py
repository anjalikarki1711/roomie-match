# # Roomie-match Homepage flask code 

# Database related functions for homepage

import cs304dbi as dbi
import datetime
import homepage

def getPostDetails(conn):
    """
    This function handles sending messages.
    Input: recipient user id
    It renders the message page for GET requests. For POST requests, it retrieves the message from the form, 
    gets the senders user ID from the session, records the current timestamp, inserts the message details into the database, 
    and displays a confirmation message.

    Returns: For GET requests: Renders the messages.html template with the page title “Message” and the recipients user ID.
    For POST requests: Inserts the message into the database and renders the messages.html template with a confirmation message.
    """
    curs = dbi.dict_cursor(conn)
    posts = curs.execute('''select post.post_id, post.user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates,
            budget, housing_type, post_type, location, post_desc, posted_time, room_pic_filename, 
            file_id from post join file on post.post_id= file.post_id order by posted_time desc''')
    return curs.fetchall()


def getProfilePic(conn, postId):
    """
    This function retrieves the picture associated with a post from the database for the feed.

    Input: Connection and postID

    It connects to the database, executes a query to select the room picture  filename for the given post ID, and returns the fetched result.

    Returns: A dictionary containing the room picture filename.
    """
    curs = dbi.dict_cursor(conn)
    picture = curs.execute('''select room_pic_filename from file where post_id = %s''', [postId])
    return curs.fetchone()
    
def getUserDetails(conn, id):
    """
    This function retrieves a user’s details from the database.
    Input: Connection, user id

    It connects to the database, executes a query to select everything for the given user ID, and returns the fetched result.

    Returns: A dictionary containing the user details from the user table.

    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from user where user_id = %s''', [id])
    return curs.fetchone()

def getUser(conn, id):
    """
    This function retrieves a user’s details from the database.
    Input: Connection, user id

    It connects to the database, executes a query to select the users name and 
    profile description for the given user ID, and returns the fetched result.

    Returns: A dictionary containing the users name and profile description.

    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select name, profile_desc from user inner join post
                            using(user_id) where user_id = %s''', [id])
    return curs.fetchone()

def isInt(var):
    """
    This function attempts to convert the variable to an integer. If successful, it returns True; otherwise, it returns False.
    Input: var 

    Returns: True if the variable can be converted to an integer, False otherwise.
    """
    try:
        var = int(var)
        return True
    except ValueError:
        return False


def getHousingNeed(conn, uid):
    """
    This function retrieves user's housing need from user table.
    Input: Connection, user_id

    It connects to the database, executes a query to select 
    what kind of housing the user is seeking for(roommates or housing) 
    and returns the fetched result.

    Returns: A dictionary containing the user's housing need

    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select seeking as housing_need from user where user_id = %s ''', [uid])
    return curs.fetchone()


def getHousingOptions(conn):
    """
    This function retrieves housing needs that were posted by our app's users 
    Input: Connection

    It connects to the database, executes a query to select 
    the distinct housing needs users have posted from the post database
    and returns the fetched result.

    Returns: A list of dictionaries containing the all available housing options 

    """
    curs = dbi.dict_cursor(conn)
    curs.execute('''select distinct post_type as housing_option from post''')
    return curs.fetchall()


def filterPostDetails(conn, housing_need):
    """
    This function retrieves filtered post details from the database.
    Filters the posts by the housing need specified (post_type)

    Input: connection, housing_need

    It connects to the database, executes a query
    to select post details filtered by post_type, 
    and returns the fetched results.

    Returns: A list of dictionaries containing post details, including user ID, 
    shared bathroom, shared bedroom, pet preferences, maximum roommates, budget, housing type, 
    post type, location, post description, room picture filename, and file ID.

    """
    curs = dbi.dict_cursor(conn)
    #filter by post_type(type of their housing needs(either housing or roommates))
    curs.execute('''select post.post_id, post.user_id, shared_bathroom, shared_bedroom, ok_with_pets, max_roommates,
            budget, housing_type, post_type, location, post_desc, posted_time, room_pic_filename, 
            file_id from post join file on post.post_id= file.post_id where post.post_type = %s order by posted_time desc''', [housing_need])
    return curs.fetchall()

def getTimeDiff(posts):
    """ 
    The getTimeDiff function processes a list of posts to add additional details such as the time 
    difference since the post was made. 

    Input:
        posts: A list of dictionaries, where each dictionary contains information about a post, 
            including 'posted_time' and 'user_id'. 


    For each post in the list: - Calculates the time difference between the
    current time and the time the post was made. - Adds a 'time_diff' key to the post 
    dictionary, indicating the number of days since the post was made. If the post was 
    made less than a day ago, 'time_diff' is set to '< 1'.
    
    Returns: The updated list of posts with additional details. 
    """
    for info in posts:
        posted_time = info['posted_time']
        current_time = datetime.datetime.now()
        time_diff = (current_time - posted_time)
        daysago = time_diff.days
        info['time_diff'] = '< 1' if daysago < 1 else daysago
    return posts

def getPostUser(conn, posts):
    """ 
    The getPostUser function processes a list of posts to add additional details such as the name of the user who made the post. 

    Input: conn: A database connection object. 
        posts: A list of dictionaries, where each dictionary contains information about a post, 
            including 'posted_time' and 'user_id'. 


    For each post in the list: 
        It retrieves user information based 
        on 'user_id' and adds the user's name to the post dictionary. If the user's name is not available, 
        sets the name to "Unknown". 
    
    Returns: The updated list of posts with additional details. 
    """
    for info in posts:
        userInfo = homepage.getUser(conn, info['user_id'])
        if userInfo['name'] != None:
            info['name'] = userInfo['name']
        else:
            info['name'] = "Unknown"
    return posts

