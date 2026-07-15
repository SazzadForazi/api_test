import io
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from PIL import Image

router = APIRouter(prefix="/api/v1/upload", tags=["File Uploads"])

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_TEXT_SIZE = 2 * 1024 * 1024   # 2MB

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    # Validate content type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Only image files are allowed."
        )
        
    # Read file content to check size
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size / (1024*1024):.2f}MB. Max allowed size is 5MB."
        )
        
    # Try reading with PIL to check validity and extract dimensions
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()  # Verify image integrity
        
        # Re-open because verify() closes the file pointer
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
        img_format = image.format
        img_mode = image.mode
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid or readable image."
        )
        
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": file_size,
        "dimensions": {
            "width": width,
            "height": height
        },
        "format": img_format,
        "mode": img_mode,
        "message": "Image uploaded and verified successfully."
    }

@router.post("/text")
async def upload_text(file: UploadFile = File(...)):
    # Validate filename extension or content type
    if not file.filename.endswith(".txt") and file.content_type != "text/plain":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only plain text files (.txt) are allowed."
        )
        
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_TEXT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size / (1024*1024):.2f}MB. Max allowed size is 2MB."
        )
        
    try:
        text_content = contents.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text_content = contents.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode file content as text."
            )
            
    # Text Analysis
    char_count_with_spaces = len(text_content)
    char_count_no_spaces = len(text_content.replace(" ", "").replace("\n", "").replace("\r", ""))
    word_count = len(text_content.split())
    line_count = len(text_content.splitlines())
    
    # 200 character preview
    preview = text_content[:200]
    if len(text_content) > 200:
        preview += "..."
        
    return {
        "filename": file.filename,
        "size_bytes": file_size,
        "character_count_raw": char_count_with_spaces,
        "character_count_no_spaces": char_count_no_spaces,
        "word_count": word_count,
        "line_count": line_count,
        "preview": preview,
        "message": "Text file analyzed successfully."
    }
