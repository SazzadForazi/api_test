import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.crud import router as crud_router, products_db
from app.uploads import router as uploads_router
from app.codec import router as codec_router
from app.simulator import router as simulator_router

app = FastAPI(
    title="Mock Practice API for Testers",
    description="A comprehensive Mock API sandbox for testing practice (REST endpoints, CRUD, OAuth/JWT, uploads, rate limiting, and status codes).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Template setup
# Base directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Include routers
app.include_router(auth_router)
app.include_router(crud_router)
app.include_router(uploads_router)
app.include_router(codec_router)
app.include_router(simulator_router)

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "product_count": len(products_db),
            "status": "Online",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    )
