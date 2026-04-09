"""
In this module we will create or define the functions that aregoing to be used in the
dependency injection of the routes.

"""

from fastapi import Depends
from fastapi.responses import JSONResponse


# first we as going to build a Depends() stub here
def get_current_users():
    # this is where we will implement the logic to get the current user
    # for now we will just return a dummy user
    return JSONResponse (
        {
            "user_id": "test_user_id",
            "username": "test_user"
        }
    )