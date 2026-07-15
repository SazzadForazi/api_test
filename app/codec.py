import base64
import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any

from app.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/v1/codec", tags=["Codec & Utilities"])

# Schemas
class EncodeRequest(BaseModel):
    text: str = Field(..., json_schema_extra={"example": "Hello World"})

class EncodeResponse(BaseModel):
    original: str
    encoded: str

class DecodeRequest(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "SGVsbG8gV29ybGQ="})

class DecodeResponse(BaseModel):
    encoded: str
    decoded: str

class JwtDecodeRequest(BaseModel):
    token: str = Field(..., description="JWT token to inspect")

class JwtDecodeResponse(BaseModel):
    header: Dict[str, Any]
    payload: Dict[str, Any]
    signature_verified_with_app_key: bool
    error_message: str = ""

@router.post("/base64/encode", response_model=EncodeResponse)
def base64_encode(data: EncodeRequest):
    try:
        text_bytes = data.text.encode("utf-8")
        encoded_bytes = base64.b64encode(text_bytes)
        encoded_str = encoded_bytes.decode("utf-8")
        return EncodeResponse(original=data.text, encoded=encoded_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Encoding failed: {str(e)}"
        )

@router.post("/base64/decode", response_model=DecodeResponse)
def base64_decode(data: DecodeRequest):
    try:
        # Check padding
        padding_needed = len(data.code) % 4
        code = data.code
        if padding_needed:
            code += "=" * (4 - padding_needed)
            
        decoded_bytes = base64.b64decode(code, validate=True)
        decoded_str = decoded_bytes.decode("utf-8")
        return DecodeResponse(encoded=data.code, decoded=decoded_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decoding failed. The string is not valid Base64: {str(e)}"
        )

@router.post("/jwt/decode", response_model=JwtDecodeResponse)
def jwt_decode(data: JwtDecodeRequest):
    try:
        # Extract headers first
        header = jwt.get_unverified_header(data.token)
        # Decode payload without verifying signature
        payload = jwt.decode(data.token, options={"verify_signature": False})
        
        # Test signature with our application's key
        signature_verified = False
        error_msg = ""
        try:
            jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
            signature_verified = True
        except jwt.ExpiredSignatureError:
            error_msg = "Signature verified but token has expired."
            signature_verified = True  # Signature was valid, just expired
        except jwt.InvalidTokenError as e:
            error_msg = f"Signature verification failed for this app's key: {str(e)}"
            
        return JwtDecodeResponse(
            header=header,
            payload=payload,
            signature_verified_with_app_key=signature_verified,
            error_message=error_msg
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JWT parsing failed: {str(e)}"
        )
