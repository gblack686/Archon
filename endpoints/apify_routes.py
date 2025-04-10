from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import sys
import asyncio
import os
from pathlib import Path

# Add the parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))

# Import Apify functions from the agent file
sys.path.append(str(Path(__file__).parent.parent / "iterations" / "v6-tool-library-integration" / "agent-resources" / "examples"))
try:
    from pydantic_apify_jobs_agent import (
        init_supabase_client,
        init_openai_client,
        upload_apify_runs_to_supabase,
        Deps,
        clean_job_url
    )
    import httpx
except ImportError as e:
    print(f"Error importing Apify agent functions: {e}")

router = APIRouter()

@router.post("/upload-runs")
async def upload_apify_runs(
    num_runs: int = Query(20, ge=1, le=100),
    items_per_run: int = Query(100, ge=1, le=500),
    candidate_email: Optional[str] = Query(None),
    scrape_keyword: Optional[str] = Query(None),
    apify_api_token: Optional[str] = Query(None)
):
    """
    Upload job listings from Apify runs to Supabase
    
    - **num_runs**: Number of recent runs to process (default: 20)
    - **items_per_run**: Maximum number of items to fetch per run (default: 100)
    - **candidate_email**: Email to associate with the job listings
    - **scrape_keyword**: Keyword used to scrape/find these jobs
    - **apify_api_token**: Apify API token (optional, will use environment variable if not provided)
    """
    try:
        # Use provided API token or get from environment
        if not apify_api_token:
            apify_api_token = os.getenv('APIFY_TOKEN')
            if not apify_api_token:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Apify API token is required"}
                )
        
        # Initialize clients
        supabase_client = await init_supabase_client()
        if not supabase_client:
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": "Failed to initialize Supabase client"}
            )
        
        openai_client = await init_openai_client()
        
        # Create context with dependencies
        async with httpx.AsyncClient() as client:
            deps = Deps(
                client=client,
                apify_api_token=apify_api_token,
                supabase_client=supabase_client,
                openai_client=openai_client
            )
            
            # Create a simple RunContext-like object
            class RunContext:
                def __init__(self, deps):
                    self.deps = deps
            
            ctx = RunContext(deps)
            
            # Call the upload function
            result = await upload_apify_runs_to_supabase(
                ctx,
                num_runs=num_runs,
                items_per_run=items_per_run,
                candidate_email=candidate_email,
                scrape_keyword=scrape_keyword
            )
            
            return {
                "success": True,
                "message": "Apify runs upload completed",
                "result": result
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

@router.get("/clean-url")
async def clean_url(url: str):
    """
    Clean a job URL by removing query parameters
    
    - **url**: The URL to clean
    """
    cleaned_url = clean_job_url(url)
    return {"original_url": url, "cleaned_url": cleaned_url} 