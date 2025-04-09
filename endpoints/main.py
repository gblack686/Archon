from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Import routers
from .job_upload_routes import router as job_upload_router
from .job_similarity_routes import router as similarity_router
from .apify_routes import router as apify_router
from .workflow_routes import router as workflow_router

# Create FastAPI app
app = FastAPI(
    title="Job Management API",
    description="API for managing job descriptions, uploads, and similarity searches",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_upload_router, prefix="/api/jobs", tags=["Job Uploads"])
app.include_router(similarity_router, prefix="/api/similarity", tags=["Job Similarity"])
app.include_router(apify_router, prefix="/api/apify", tags=["Apify Integration"])
app.include_router(workflow_router, prefix="/api/workflows", tags=["Deterministic Workflows"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Job Management API",
        "version": "1.0.0",
        "documentation": "/docs",
    }

if __name__ == "__main__":
    # Run the server when script is executed directly
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("endpoints.main:app", host="0.0.0.0", port=port, reload=True) 