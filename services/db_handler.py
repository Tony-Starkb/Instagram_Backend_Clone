import json
from pathlib import Path 


BASE_DIR = Path(__file__).resolve().parent.parent

USERS_FILE = BASE_DIR / "database" / "users.json"
POSTS_FILE = BASE_DIR / "database" / "posts.json"


def read_json(file_path):
    
    with open(file_path, "r") as file:
        return json.load(file)
    


def write_json(file_path, data):
    
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    


# Users
def get_all_users():
	return read_json(USERS_FILE)

def get_user_by_id(user_id):
	users = read_json(USERS_FILE)
	for user in users:
		if user["id"] == user_id:
			return user
	return None

def get_user_by_username(username):
	users = read_json(USERS_FILE)
	for user in users:
		if user["username"] == username:
			return user
	return None
	

def add_user(user):
	users = read_json(USERS_FILE)
	users.append(user)
	write_json(USERS_FILE, users)


# Posts
def get_all_posts():
	return read_json(POSTS_FILE)

def get_post_by_id(post_id):
	posts = read_json(POSTS_FILE)
	for post in posts:
		if post["id"] == post_id:
			return post
	return None

def get_user_posts(username):
	posts = read_json(POSTS_FILE)
	user_posts = [post for post in posts if post["username"] == username]
	return user_posts

def add_post(post):
	posts = read_json(POSTS_FILE)
	posts.append(post)
	write_json(POSTS_FILE, posts)
