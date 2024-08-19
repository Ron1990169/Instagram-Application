import datetime  # this is the library we will use to get the current date and time.
import flask  # this is the library we will use to create the web app.
import google.oauth2.id_token  # this is the library we will use to authenticate users.
from flask import Flask, render_template, request, session  # this is the library we will use to
from flask import abort, make_response  # this is the library we will use to abort requests.
from google.auth.transport import requests  # this is the library we will use to authenticate users.
from google.cloud import datastore, storage  # this is the library we will use to store data in the datastore.
from werkzeug.utils import secure_filename  # this is the library we will use to secure file names.

import local_constants  # this is the library we will use to store constants.

app: Flask = flask.Flask(__name__)  # create the web app.

datastore_client = datastore.Client()  # Create a datastore client.

firebase_request_adapter = requests.Request()  # Create a request adapter for the Firebase Admin SDK.


def createUserInfo(claims):  # Create a new user in the datastore.
    entity_key = datastore_client.key('UserInfo', claims['email'])  # Create a user key.
    entity = datastore.Entity(key=entity_key)  # Create a new entity.
    name = claims.get('name')  # Get the 'name' value from the claims dictionary or None if it doesn't exist.
    entity.update({
        'email': claims['email'],  # Store the user email instead of the user info.
        'name': name,  # Store the username instead of the user info.
        'post_id': [],  # Store the post IDs instead of the post info.
        'followers_email': [],  # Store the follower emails instead of the follower info.
        'following_email': [],  # Store the following emails instead of the following info.
        'followers_list': [],  # Store the follower list instead of the follower info.
        'following_list': []  # Store the following list instead of the following info.
    })
    datastore_client.put(entity)  # Store the entity in the datastore.


def retrieveUserInfo(claims):  # Retrieve a user from the datastore.
    entity_key = datastore_client.key('UserInfo', claims['email'])  # Get the user key.
    entity = datastore_client.get(entity_key)  # Get the user from the datastore.
    return entity  # Return the user.


def blobList(prefix):  # List all the blobs in the storage bucket.
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)  # Create a storage client.
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)  # List the blobs.


def blobUpload(image_file, file_path):  # Upload an image to the storage bucket.
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)  # Create a storage client.
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)  # Get the storage bucket.
    blob = bucket.blob(image_file.filename)  # Create a blob with the image file name.
    blob.upload_from_file(file_path)  # Upload the image file to the blob.


def blobDownload(filename):  # Download an image from the storage bucket.
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    if not blob.exists():
        raise ValueError(f"Blob with filename {filename} does not exist.")
    return blob.download_as_bytes()


def blobDelete(image_path):  # Delete uploaded image to the storage bucket.
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)  # Create a storage client.
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)  # Get the storage bucket.
    blob = bucket.blob(image_path)  # Create a blob with the image file name.
    blob.delete(image_path)  # Delete the image file from the blob.


def blobPublicURL(filename):  # Get the public URL of a file from the storage bucket.
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    if not blob.exists():
        raise ValueError(f"Blob with filename {filename} does not exist.")
    return blob.public_url


def addCommentToPost(content):  # Add a comment to a post in the datastore.
    comment = {  # Create a comment.
        'content': content,  # Store the comment content.
        'timestamp': datetime.datetime.utcnow()  # Store the comment timestamp.
    }
    datastore_client.put(comment)  # Update the post comment in the datastore.
    return True  # Return true if the comment was added.


def deletePost(post_id, claims):
    # Verify Firebase auth
    if not claims:
        raise ValueError('User not authenticated')
    # Check if the post exists in the datastore
    post_key = datastore_client.key('Post', post_id)
    post = datastore_client.get(post_key)
    if not post:
        raise ValueError('Post not found')
    # Check if the authenticated user is the owner of the post
    if post['user_email'] != claims['email']:
        raise ValueError('User does not have permission to delete this post')
    # Delete the post from the datastore
    datastore_client.delete(post_key)
    # Delete the post image from the storage bucket
    image_path = post['image_path']
    blobDelete(image_path)
    return True


def add_follower(user_info, follower_email):  # Add a follower to the datastore.
    user_key = datastore_client.key('UserInfo', user_info['email'])  # Get the user key.
    user = datastore_client.get(user_key)  # Get the user from the datastore.
    if follower_email not in user['followers_email']:  # Check if the follower is already in the list.
        user['followers_email'].append(follower_email)  # Add the follower to the list.
        datastore_client.put(user)  # Update the user in the datastore.


def add_following(user_info, following_email):  # Add a following to the datastore.
    user_key = datastore_client.key('UserInfo', user_info['email'])  # Get the user key.
    user = datastore_client.get(user_key)  # Get the user from the datastore.
    if following_email not in user['following_email']:  # Check if the following is already in the list.
        user['following_email'].append(following_email)  # Add the following to the list.
        datastore_client.put(user)  # Update the user in the datastore.


def remove_follower(user_info, follower_email):  # Remove a follower from the user's followers list.
    user_key = datastore_client.key('UserInfo', user_info['email'])  # Get the user key.
    user = datastore_client.get(user_key)  # Get the user from the datastore.
    if follower_email in user['followers_email']:  # Check if the follower is in the list.
        user['followers_email'].remove(follower_email)  # Remove the follower from the list.
        datastore_client.put(user)  # Update the user in the datastore.


def remove_following(user_info, following_email):  # Remove a following from the user's following list.
    user_key = datastore_client.key('UserInfo', user_info['email'])  # Get the user key.
    user = datastore_client.get(user_key)  # Get the user from the datastore.
    if following_email in user['following_email']:  # Check if the following is in the list.
        user['following_email'].remove(following_email)  # Remove the following from the list.
        datastore_client.put(user)  # Update the user in the datastore.


def get_followers_list(user_info):  # Retrieve the list of followers.
    client = datastore.Client()  # Create a datastore client.
    query = client.query(kind='UserInfo')  # Create a query for the UserInfo kind.
    query.add_filter('following_email', '=', user_info['email'])  # Filter the query by the user's email.
    results = list(query.fetch())  # Execute the query and store the results.
    followers_list = [result['email'] for result in results]  # Extract the email from each result.
    return followers_list  # Return the list of followers.


def get_following_list(user_info):  # Retrieve the list of following.
    client = datastore.Client()  # Create a datastore client.
    query = client.query(kind='UserInfo')  # Create a query for the UserInfo kind.
    query.add_filter('followers_email', '=', user_info['email'])  # Filter the query by the user's email.
    results = list(query.fetch())  # Execute the query and store the results.
    following_list = [result['email'] for result in results]  # Extract the email from each result.
    return following_list  # Return the list of following.


def search_users_by_profile_name(search_query):  # Retrieve the list of users matching the search query.
    client = datastore.Client()  # Create a datastore client.
    query = client.query(kind='User')  # Create a query for the User kind.
    query.add_filter('profile_name', '>=', search_query)  # Filter the query by the search query.
    results = list(query.fetch())  # Execute the query and store the results.
    return results  # Return the list of users matching the search query.


def get_timeline_posts(user_info):  # Retrieve the list of posts for the user's timeline.
    following_list = get_following_list(user_info) + [user_info['email']]  # Get the list of following.
    query = datastore_client.query(kind='Post')  # Create a query for the Post kind.
    query.add_filter('user_email', 'in', following_list)  # Filter the query by the following list.
    query.order = ['-timestamp']  # Order the query by timestamp.
    posts = list(query.fetch())  # Execute the query and store the results.
    timeline_posts = []  # Create an empty list to store the timeline posts.
    for post in posts:  # Iterate through the posts.
        post_data = {'id': post.id, 'caption': post['caption'], 'user_email': post['user_email'],
                     'timestamp': post['timestamp'], 'image_url': blobPublicURL(post['image_path']),
                     'image_bytes': blobDownload(post['image_path'])}  # Create a dictionary for the post.
        timeline_posts.append(post_data)  # Add the post to the list.
    return timeline_posts  # Return the list of timeline posts.


@app.route('/')  # The root route.
def root():  # The root page.
    id_token = request.cookies.get("token")  # Get the id token from the request.
    error_message = None  # Create an empty error message.
    claims = None  # Create an empty claims.
    user_info = None  # Create an empty user info.
    post = []  # Create an empty list to store the posts.
    followers_email = []  # Create an empty list to store the followers_email.
    following_email = []  # Create an empty list to store the following.
    if id_token:  # Check if the id token exists.
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)  # Retrieve the user info.
            if user_info is None:
                createUserInfo(claims)  # Create a new user if they don't exist.
                user_info = retrieveUserInfo(claims)  # Retrieve the user info.
            blob_list = blobList(None)  # List all the blobs in the storage bucket.
            for i in blob_list:
                if i.name[len(i.name) - 1] == '/':  # Check if the blob is a directory.
                    add_post_handler()  # Add the post to the database.
                    post.append(i)  # Add the file to the post list.
                else:
                    post.append(i)  # Add the file to the post list.
            followers_email = get_followers_list(user_info)  # Get the list of followers_email.
            following_email = get_following_list(user_info)  # Get the list of following.
            get_timeline_posts(user_info)  # Get the list of posts from the users the current user is following.
        except ValueError as exc:
            error_message = str(exc)
    return render_template('index.html', user_data=claims, error_message=error_message, user_info=user_info, post=post,
                           followers_email=followers_email, following_email=following_email)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Allowed image file extensions.


def allowed_file(filename):  # Check if the file extension is allowed for upload.
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add_comment/<post_id>', methods=['GET', 'POST'])  # The add comment route.
def add_comment_handler(post_id):  # The add comment page.
    id_token = request.cookies.get("token")  # Get the id token from the request.
    error_message = None  # Create an empty error message.
    content = None  # Create an empty content.
    if request.method == 'POST':  # Check if the request method is POST.
        if id_token:  # Check if the id token exists.
            try:  # Try to add the comment to the post.
                content = request.form.get('content')  # Get the content from the request.
                if len(content) > 200:  # Check if the content is more than 200 characters.
                    error_message = "Comment should be no more than 200 characters."
                else:
                    success = addCommentToPost(post_id)  # Add the comment to the post.
                    if not success:
                        error_message = "Failed to add the comment."
            except ValueError as exc:
                error_message = str(exc)
        else:
            error_message = "You must be logged in to comment."
    post_entity_key = datastore_client.key('post_id', int(post_id))  # Get the post entity key.
    post = datastore_client.get(post_entity_key)  # Get the post from the database.
    if not post:
        abort(404)
    comments = post.get('comments', [])  # Get the comments from the post.
    return render_template('comment.html', post=post, error_message=error_message, comments=comments, content=content)


@app.route('/add_post', methods=['GET', 'POST'])  # Add a new post to the database and storage bucket.
def add_post_handler():  # This function is called when the user submits the add post form.
    id_token = request.cookies.get("token")  # Get the Firebase ID token from the request.
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)  # Get the user info from the database.
            caption = request.form.get('caption')  # Get the post description from the form.
            description = request.form.get('description')  # Get the post full_name from the form.
            tags = request.form.get('tags')  # Get the post tags from the form.
            image_file = request.files.get('image_file')  # Get the image file from the form.
            if image_file and allowed_file(image_file.filename):  # Check if the file is valid.
                filename = secure_filename(image_file.filename)  # Get the filename.
                storage_client = storage.Client(project=local_constants.PROJECT_NAME)  # Create a storage client.
                bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
                blob = bucket.blob(user_info['email'] + '/' + filename)  # Create a blob in the bucket.
                blob.upload_from_string(image_file.read(), content_type=image_file.content_type)  # Upload the file.
                post_entity_key = datastore_client.key('post_id')  # Create a user key.
                entity = datastore.Entity(key=post_entity_key)  # Create a new entity.
                entity.update({
                    'caption': caption,  # Create a new post description.
                    'description': description,  # Create a new post full_name.
                    'tags': tags,  # Create a new post tags.
                    'image_url': blob.public_url,  # Create a new post image_url.
                    'user_email': user_info['email'],  # Create a new post user_email.
                })  # Update the entity.
                datastore_client.put(entity)  # Add the post to the datastore.
            else:
                "Invalid file format or no file provided."
        except ValueError as exc:
            str(exc)
    return render_template('post.html')  # Redirect to the post page.


@app.route('/delete', methods=['POST'])  # Delete a post from the database and storage bucket.
def delete_post():
    id_token = request.cookies.get("token")
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            post_id = request.form.get('post_id')
            deletePost(post_id, claims)
        except ValueError as exc:
            return str(exc)
    return render_template('index.html')


@app.route('/download_file/<string:filename>', methods=['GET'])  # Download a file from the storage bucket.
def download_file(filename):
    file_bytes = blobDownload(filename)
    response = make_response(file_bytes)
    response.headers.set('Content-Type', 'application/octet-stream')
    response.headers.set('Content-Disposition', f'attachment; filename={filename}')
    return response


@app.route('/add_follower', methods=['POST'])  # Add a follower to the database.
def add_follower_handler():
    id_token = request.cookies.get("token")  # Get the Firebase ID token from the request.
    error_message = None  # Create an empty error message.
    followers_list = None  # Create an empty followers list.
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)  # Get the user info from the database.
            follower_email = request.form.get('follower_email')  # Get the follower email from the form.
            follower_name = request.form.get('follower_name')  # Get the follower name from the form.
            follower_entity_key = datastore_client.key('Follower', follower_email)  # Create a follower key.
            follower_entity = datastore.Entity(key=follower_entity_key)  # Create a new follower entity.
            follower_entity.update({
                'name': follower_name,
                'email': follower_email
            })  # Update the follower entity.
            datastore_client.put(follower_entity)  # Add the follower to the datastore.
            add_follower(user_info, follower_email)  # Add the follower to the user's list of followers.
            followers_list = get_followers_list(user_info)  # Get the updated list of followers.
        except ValueError as exc:
            error_message = str(exc)  # Display an error message.
    return render_template('index.html', error_message=error_message, followers_list=followers_list)  # Redirect
    # to the index page.


@app.route('/add_following', methods=['POST'])  # Add a new following to the database.
def add_following():
    id_token = request.cookies.get("token")  # Get the Firebase ID token from the request.
    error_message = None  # Create an empty error message.
    following_list = None  # Create an empty followers list.
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)  # Get the user info from the database.
            following_email = request.form.get('following_email')  # Get the following email from the form.
            following_name = request.form.get('following_name')  # Get the following name from the form.
            following_entity_key = datastore_client.key('Following', following_email)  # Create a following key.
            following_entity = datastore.Entity(key=following_entity_key)  # Create a new following entity.
            following_entity.update({
                'name': following_name,
                'email': following_email
            })  # Update the following entity.
            datastore_client.put(following_entity)  # Add the following to the datastore.
            add_follower(user_info, following_email)  # Add the following to the user's list of followers.
            following_list = get_following_list(user_info)  # Get the updated list of following people.
        except ValueError as exc:
            error_message = str(exc)  # Display an error message.
    return render_template('index.html', error_message=error_message, following_list=following_list)  # Redirect
    # to the index page.


@app.route('/search', methods=['GET', 'POST'])  # Search for users by profile name.
def search_profiles():  # This function is called when the user submits the search form.
    users = []  # Create an empty list to store the users.
    if request.method == 'POST':  # Check if the request method is POST.
        search_query = request.form.get('search_query')  # Get the search query from the form.
        users = search_users_by_profile_name(search_query)  # Search for users by profile name.
        for user in users:
            user['image_bytes'] = blobDownload(user['image_path'])
    return render_template('search.html', users=users)  # Redirect to the search page.


@app.route('/timeline', methods=['GET', 'POST'])  # Display the user's timeline.
def timeline():  # This function is called when the user submits the search form.
    id_token = request.cookies.get("token")
    error_message = None
    get_post = []  # Create an empty list to store the users.
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            get_post = get_timeline_posts(user_info)  # Get the user's timeline posts.
        except ValueError as exc:
            error_message = str(exc)
    return render_template('timeline.html', error_message=error_message, get_post=get_post)


@app.route('/remove', methods=['POST'])  # Remove a follower or following from the database.
def remove_handler():
    id_token = request.cookies.get("token")
    message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)  # Get the user info from the database.
            remove_email = request.form.get('remove_email')
            remove_type = request.form.get('remove_type')
            if remove_type == 'follower':
                remove_follower(user_info, remove_email)
            elif remove_type == 'following':
                remove_following(user_info, remove_email)
            message = f"Successfully removed {remove_type}: {remove_email}"
        except ValueError as exc:
            message = str(exc)
    return render_template('post.html', message=message)


@app.route('/retrieve_list', methods=['GET'])
def retrieve_list_handler():
    id_token = request.cookies.get("token")
    list_type = request.args.get('list_type')  # Get the list type from the request arguments.
    error_message = None
    entity_list = []
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if list_type == 'followers':
                entity_list = get_followers_list(user_info)
            elif list_type == 'following':
                entity_list = get_following_list(user_info)
            else:
                error_message = "Invalid list type"
        except ValueError as exc:
            error_message = str(exc)
    return render_template('post.html', error_message=error_message, entity_list=entity_list)


if __name__ == '__main__':  # Run the app.
    app.run(host='127.0.0.1', port=8080, debug=True)
