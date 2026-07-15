import asyncio
import time
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/simulate", tags=["Simulator & Edge Cases"])

# Store IP request times for rate limit simulator
# IP -> list of timestamps
RATE_LIMIT_DB: Dict[str, List[float]] = {}
LIMIT_WINDOW = 30  # seconds
LIMIT_REQUESTS = 5

@router.get("/delay/{seconds}")
async def delayed_response(seconds: int):
    if seconds < 1 or seconds > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delay must be between 1 and 10 seconds."
        )
    await asyncio.sleep(seconds)
    return {
        "slept_seconds": seconds,
        "message": f"Successfully delayed response by {seconds} seconds."
    }

@router.get("/status/{code}")
def status_code_response(code: int):
    if code < 100 or code > 599:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HTTP Status Code must be between 100 and 599."
        )
    
    # Custom message based on standard HTTP status codes
    status_meanings = {
        200: "OK",
        201: "Created",
        204: "No Content",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    
    meaning = status_meanings.get(code, "Custom Status")
    
    # 204 does not permit response body, return raw Response
    if code == 204:
        return Response(status_code=code)
        
    return JSONResponse(
        status_code=code,
        content={
            "status_code": code,
            "message": f"Simulated HTTP Status Code {code} ({meaning})"
        }
    )

@router.get("/headers")
def echo_headers(request: Request):
    headers_dict = dict(request.headers)
    return {
        "headers": headers_dict,
        "count": len(headers_dict),
        "message": "These are the headers received by the server."
    }

@router.get("/rate-limit")
def rate_limit_endpoint(request: Request):
    client_ip = request.client.host if request.client else "unknown_ip"
    current_time = time.time()
    
    # Initialize list if first request
    if client_ip not in RATE_LIMIT_DB:
        RATE_LIMIT_DB[client_ip] = []
        
    # Clean up timestamps older than the window
    timestamps = [t for t in RATE_LIMIT_DB[client_ip] if current_time - t < LIMIT_WINDOW]
    RATE_LIMIT_DB[client_ip] = timestamps
    
    if len(timestamps) >= LIMIT_REQUESTS:
        # Calculate retry after
        oldest_request = timestamps[0]
        retry_after = int(LIMIT_WINDOW - (current_time - oldest_request)) + 1
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Max {LIMIT_REQUESTS} requests per {LIMIT_WINDOW} seconds.",
                "retry_after_seconds": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )
        
    # Record current request
    RATE_LIMIT_DB[client_ip].append(current_time)
    
    return {
        "client_ip": client_ip,
        "requests_in_window": len(RATE_LIMIT_DB[client_ip]),
        "max_requests": LIMIT_REQUESTS,
        "window_seconds": LIMIT_WINDOW,
        "message": "Request allowed. Under the rate limit."
    }
