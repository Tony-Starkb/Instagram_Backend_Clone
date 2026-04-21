"""
In this module, we will definethe functions to validate the user input for different typesof data
that we want to for some of the extra realworld working of real production level constraints or 
business logics

"""


# user password input validation
"""
The password should include these constraints:
- Minimum length of 8 characters
- use only letters[a-z, A-Z], numbers[0-9], special characters[!,@,#,$,%,&,*]

"""
from fastapi.exceptions import HTTPException


def validate_password(password: str):
    password = password.strip()
    if len(password) < 8:
        raise HTTPException (
            status_code = 422,
            detail = "Password must be at least 8 characters long."
        )
    if not any(char.isalpha() for char in password):
        raise HTTPException (
            status_code = 422,
            detail = "Password must contain at least one letter."
        )
    if not any(char.isdigit() for char in password):
        raise HTTPException (
            status_code = 422,
            detail = "Password must contain at least one number."
        )
    if not any(char in "!@#$%&*" for char in password):
        raise HTTPException (
            status_code = 422,
            detail = "Password must contain at least one special character (!, @, #, $, %, &, *)."
        )

    

# user username input validation
"""
The usrname should include these constraunts:
- Minimum length of 5 characters
- use only letters[a-z, A-Z], numbers[0-9], special characters[_, -, $, #, @], here the use of the special 
  characters is not compulsory but if used then it should not be at the start or end of the username 
  and also the username

"""
 
def validate_username(username: str):
    username = username.strip()
    if len(username) < 5:
        raise HTTPException (
            status_code = 422,
            detail = "Username must be at least 5 characters long."
        )
    if not all(char.isalnum() or char in "_-$@#" for char in username):
        raise HTTPException (
            status_code = 422,
            detail = "Username can only contain letters, numbers, and special characters (_, -, $, @, #)."
        )
    if not username[0].isalnum() or not username[-1].isalnum():
        raise HTTPException (
            status_code = 422,
            detail = "Username cannot start or end with special characters."
        )
    if not any (char.isalpha() for char in username):
        raise HTTPException (
            status_code = 422,
            detail = "Username must contain at least one letter."
        )
    if any (char in "!%^&*()+=|\\:;\"'<>,.?/" for char in username):
        raise HTTPException (
            status_code = 422,
            detail = "Username cannot contain special characters other than _, -, $, # and @."
        )
    
    
    
    
