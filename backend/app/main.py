import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import auth, analysis
from app.database.mongodb import client


# -------------------------------
# 🔹 BASE PATH SETUP (FIXED)
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Correct frontend path
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

# Create uploads directory
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -------------------------------
# 🔹 FASTAPI APP
# -------------------------------
app = FastAPI(
    title="Autonomous Codebase Documenter API",
    description="AI-powered codebase documentation generator using Gemini",
    version="1.0.0"
)


# -------------------------------
# 🔹 CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# 🔹 ROUTES
# -------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])


# -------------------------------
# 🔹 STARTUP / SHUTDOWN
# -------------------------------
@app.on_event("startup")
async def startup():
    print("🚀 Server started successfully")
    print("📁 Frontend path:", FRONTEND_DIR)


@app.on_event("shutdown")
async def shutdown():
    client.close()
    print("🔌 MongoDB connection closed")


# -------------------------------
# 🔹 STATIC FRONTEND (SAFE MOUNT)
# -------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print("⚠️ Frontend folder not found at:", FRONTEND_DIR)


# -------------------------------
# 🔹 HEALTH CHECK
# -------------------------------
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Autonomous Codebase Documenter"
    }