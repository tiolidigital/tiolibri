from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routerów
from app.routers import projects, generate, chapters, snapshots, export_import

# Inicjalizacja FastAPI
app = FastAPI(
    title="TIOLIBRI API",
    description="Backend do generowania EPUB/PDF z HTML",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:5174",  # Vite alternate
        "http://localhost:3000",  # Legacy
        "http://localhost:3001",  # Vite alternate 2
        "https://tiolibri.vercel.app",  # Production frontend
        "https://app.tiolibri.com",  # Custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Podłącz routery
# export_import and snapshots before projects: their literal paths (/import,
# /snapshots, /export) must not be shadowed by projects' /{project_id} param.
app.include_router(export_import.router)
app.include_router(snapshots.router)
app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(generate.router)

# Hello World endpoint
@app.get("/")
async def read_root():
    return {
        "message": "TIOLIBRI API is running! 🚀",
        "version": "0.1.0",
        "status": "ok"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
