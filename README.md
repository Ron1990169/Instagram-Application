This document is an academic report submitted by Rohin Mehra for Assignment 3 at Griffith College Dublin, as part of the Big Data Analysis and Management department. 
The report details the development and operations of a Flask-based Instagram-like web application, focusing on the functions and operations implemented in the application's code. 
Below is a summary of the key components and functionalities described in the report:

Libraries and Imports:
The report begins by explaining the purpose of each imported library used in the application

datetime: Used for handling dates and times within the application.
flask: Utilized to create the web application framework.
google.oauth2.id_token: Facilitates user authentication via Firebase ID tokens.
Flask, render_template, request, session: Components for managing the Flask app's operations.
abort, make_response: Used to manage HTTP responses and abort requests.
google.auth.transport.requests: Supports user authentication procedures.
google.cloud.datastore, storage: Handle data storage in Google Cloud Datastore and file storage in Google Cloud Storage.
secure_filename: Ensures the security of file names when handling uploads.
local_constants: Contains application-specific constants.

User Management:
createUserInfo(claims): Creates a new user entity in the datastore, storing user details such as email, name, post IDs, and follower lists.
retrieveUserInfo(claims): Retrieves user information from the datastore based on the claims dictionary.

Storage Management:
blobList(prefix): Lists all files (blobs) in the storage bucket that match a given prefix.
blobUpload(image_file, file_path): Uploads an image file to the storage bucket.
blobDownload(filename): Downloads an image file from the storage bucket.
blobDelete(image_path): Deletes an image file from the storage bucket.
blobPublicURL(filename): Retrieves the public URL of a file stored in the storage bucket.

Post and Comment Management:
addCommentToPost(content): Adds a comment to a post in the datastore, recording the comment's content and timestamp.
deletePost(post_id, claims): Deletes a post from the datastore after verifying the user's authentication and ownership of the post.
Follower and Following Management
add_follower(user_info, follower_email): Adds a follower to the user's datastore record.
add_following(user_info, following_email): Adds a following to the user's datastore record.
remove_follower(user_info, follower_email): Removes a follower from the user's datastore record.
remove_following(user_info, following_email): Removes a following from the user's datastore record.

Retrieval and Search Functions:
get_followers_list(user_info): Retrieves the list of followers for a user from the datastore.
get_following_list(user_info): Retrieves the list of users that the user is following.
search_users_by_profile_name(search_query): Searches for users in the datastore whose profile name matches the search query.
get_timeline_posts(user_info): Retrieves a list of posts from the users that the current user is following, including their own posts, in descending order by timestamp.

Flask Route Handlers:
root(): Serves as the root page of the Flask app, handling user authentication, retrieving user data, and rendering the main interface.
allowed_file(filename): Checks if a file's extension is allowed for upload.
add_comment_handler(post_id): Handles user comments on posts, verifying authentication and updating the datastore.
add_post_handler(): Manages the process of adding a new post, including image upload and datastore entry.
delete_post(): Handles the deletion of a post by an authenticated user.
download_file(filename): Facilitates the download of files from the storage bucket.
add_follower_handler(): Manages adding a follower to the user's account.
add_following(): Handles the process of following another user.
search_profiles(): Facilitates user searches by profile name.
timeline(): Renders the user's timeline, displaying posts from the users they follow.
remove_handler(): Manages the removal of followers or followings.
retrieve_list_handler(): Retrieves and displays the list of followers or following when the user navigates to those sections.

Key Features:

User Authentication: The application securely manages user sessions and access using Firebase authentication.
Data and File Management: The application integrates with Google Cloud Datastore and Storage to handle user data, posts, and images efficiently.
Social Features: Users can follow others, manage followers, and interact with posts through comments and likes.
