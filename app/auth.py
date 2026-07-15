import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import APIKeyCookie, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Constants
SECRET_KEY = "tester_super_secret_key_123!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# APIRouter for Auth
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Dummy user database
USERS_DB = {
    "admin": {"username": "admin", "password": "password123", "role": "admin", "email": "admin@example.com"},
    "tester": {"username": "tester", "password": "testpass", "role": "tester", "email": "tester@example.com"},
    "user": {"username": "user", "password": "userpass", "role": "user", "email": "user@example.com"},
}

# Schemas
class LoginRequest(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "admin"})
    password: str = Field(..., json_schema_extra={"example": "password123"})

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    message: str

class UserProfile(BaseModel):
    username: str
    role: str
    email: str

# Helpers to extract token from Header or Cookie
security_bearer = HTTPBearer(auto_error=False)
security_cookie = APIKeyCookie(name="access_token", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    cookie: Optional[str] = Depends(security_cookie)
) -> UserProfile:
    token = None
    if bearer:
        token = bearer.credentials
    elif cookie:
        token = cookie
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide 'Authorization: Bearer <token>' header or 'access_token' cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or user not found.",
            )
        user_info = USERS_DB[username]
        return UserProfile(
            username=user_info["username"],
            role=user_info["role"],
            email=user_info["email"]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT, # Custom response code to challenge testers!
            detail="Invalid signature or malformed token.",
        )

# Routes
@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, response: Response):
    user = USERS_DB.get(login_data.username)
    if not user or user["password"] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
        
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    
    # Set cookie (useful for testing cookie auth)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        message="Login successful. Cookie 'access_token' has also been set."
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out. Cookie 'access_token' has been cleared."}

@router.get("/me", response_model=UserProfile)
def get_me(current_user: UserProfile = Depends(get_current_user)):
    return current_user
