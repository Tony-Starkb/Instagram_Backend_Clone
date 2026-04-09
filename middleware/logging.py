"""
In this module, we define a middleware that will logging the request for each and 
everyincoming HTTP request and will log these as mentioned: method, path, status code, header. 
This logging will be used for debugging and tracing purposes throughout the 
application. The middleware will log the request details before processing the request 
and log the response details after processing the request. This will help in 
identifying the issues and debugging the application effectively.

"""


import time
import logging
from fastapi import Request


logger = logging.getLogger(__name__)


async def log_request(request: Request, call_next):
    # Before call_next: start timer
    start_time = time.perf_counter()
    # request.state.request_id is already available
    
    response = await call_next(request)
    
    # After call_next: stop timer
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    
    # Read status_code
    status_code = response.status_code
    
    # Log required information
    method = request.method
    path = request.url.path
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"req_id={request_id} | {method} {path} | {status_code} | {int(duration_ms)}ms")
    
    return response