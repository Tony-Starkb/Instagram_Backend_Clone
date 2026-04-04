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
    def __init__(self, user_id):
        detail = f"User with id {user_id} not found."
        super().__init__(status_code=404, detail=detail)
        self.user_id = user_id

class NotAuthorized(HTTPException):
    """Exception raised when a user is not authorized to perform an action."""
    def __init__(self, user_id=None):
        if user_id:
            detail = f"User with id {user_id} is not authorized."
        else:
            detail = "Not authorized to perform this action."
        super().__init__(status_code=403, detail=detail)
        self.user_id = user_id

