"""
Exceptions for the application.
Here i am going to implement custom exceptions for the application, 
such as PostNotFound, UserNotFound, and NotAuthorized, and etc if needed in future

"""


# PostNotFound
# UserNotFound
#NotAuthorized
from fastapi import HTTPException


class PostNotFound(HTTPException):
    """Exception raised when a post is not found."""
    def __init__(self, post_id):
        detail = f"Post with id {post_id} not found."
        super().__init__(status_code=404, detail=detail)
        self.post_id = post_id

class UserNotFound(HTTPException):
    """Exception raised when a user is not found."""
    def __init__(self, username):
        detail = f"User with username {username} not found."
        super().__init__(status_code=404, detail=detail)
        self.username = username

class NotAuthorized(HTTPException):
    """Exception raised when a user is not authorized to perform an action."""
    def __init__(self, username=None):
        if username:
            detail = f"User with username {username} is not authorized."
        else:
            detail = "Not authorized to perform this action."
        super().__init__(status_code=403, detail=detail)
        self.username = username

