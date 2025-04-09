from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import sys
import json
import asyncio
from pathlib import Path

# Add the parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))

# Import utility functions
from utils.job_similarity_search import (
    init_supabase_client, 
    get_starred_jobs, 
    get_embeddings_for_jobs, 
    average_embeddings, 
    run_similarity_search,
    create_similar_jobs_view
)

router = APIRouter()

# Dependency to get Supabase client
async def get_supabase_client():
    client = await init_supabase_client()
    if not client:
        raise HTTPException(status_code=500, detail="Failed to initialize Supabase client")
    return client

@router.get("/similar-to-starred")
async def get_similar_to_starred(
    match_threshold: float = Query(0.5, ge=0.0, le=1.0),
    match_count: int = Query(50, ge=1, le=100),
    client = Depends(get_supabase_client)
):
    """
    Get jobs similar to starred jobs based on their embeddings
    
    - **match_threshold**: Similarity threshold (0-1, default: 0.5)
    - **match_count**: Maximum number of similar jobs to return (default: 50)
    """
    try:
        # Get starred jobs
        starred_jobs = await get_starred_jobs(client)
        if not starred_jobs:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "No starred jobs found"}
            )
        
        # Get embeddings for starred jobs
        job_embeddings = await get_embeddings_for_jobs(client, starred_jobs)
        if not job_embeddings:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "No embeddings found for starred jobs"}
            )
        
        # Calculate average embedding
        avg_embedding = average_embeddings(job_embeddings)
        if not avg_embedding:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Failed to calculate average embedding"}
            )
        
        # Run similarity search
        similar_jobs = await run_similarity_search(client, avg_embedding, match_count)
        
        return {
            "success": True,
            "message": f"Found {len(similar_jobs)} similar jobs",
            "starred_jobs_count": len(starred_jobs),
            "embeddings_found": len(job_embeddings),
            "similar_jobs": similar_jobs
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

@router.post("/create-view")
async def create_view_of_similar_jobs(
    job_ids: List[int] = Query(...),
    view_name: str = Query(...),
    client = Depends(get_supabase_client)
):
    """
    Create a view of similar jobs
    
    - **job_ids**: List of job IDs to include in the view
    - **view_name**: Name of the view to create
    """
    try:
        result = await create_similar_jobs_view(client, job_ids, view_name)
        
        if result.get("success"):
            return result
        else:
            return JSONResponse(
                status_code=400,
                content=result
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

@router.get("/embed-job/{job_id}")
async def get_embedding_for_job(
    job_id: int,
    client = Depends(get_supabase_client)
):
    """
    Get embedding for a specific job
    
    - **job_id**: ID of the job to get embedding for
    """
    try:
        # Get job details
        result = client.table("job_descriptions_metadata") \
            .select("*") \
            .eq("id", job_id) \
            .execute()
        
        if not result.data:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": f"Job with ID {job_id} not found"}
            )
        
        job = result.data[0]
        job_url = job.get("job_url")
        
        if not job_url:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Job has no URL to match with vector store"}
            )
        
        # Get embedding from vector store
        result = client.table("job_descriptions_vector_store") \
            .select("id, content, metadata") \
            .filter("metadata->>jobUrl", "eq", job_url) \
            .execute()
        
        if not result.data:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "No embedding found for this job"}
            )
        
        vector_data = result.data[0]
        
        return {
            "success": True,
            "job_id": job_id,
            "vector_id": vector_data["id"],
            "job_title": job.get("title"),
            "content": vector_data["content"],
            "metadata": vector_data["metadata"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        ) 