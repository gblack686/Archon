from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import sys
import asyncio
import os
import time
import json
from datetime import datetime
from pathlib import Path
import httpx

# Add the parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))

# Import utility functions and dependencies
from utils.upload_job_descriptions import init_supabase_client as init_upload_client
from utils.job_similarity_search import (
    init_supabase_client as init_similarity_client,
    get_starred_jobs,
    get_embeddings_for_jobs,
    average_embeddings,
    run_similarity_search,
    create_similar_jobs_view
)

# Import Apify functions
sys.path.append(str(Path(__file__).parent.parent / "iterations" / "v6-tool-library-integration" / "agent-resources" / "examples"))
try:
    from pydantic_apify_jobs_agent import (
        init_supabase_client as init_apify_client,
        init_openai_client,
        upload_apify_runs_to_supabase,
        Deps
    )
except ImportError as e:
    print(f"Error importing Apify agent functions: {e}")

router = APIRouter()

# ============================================================
# Helper functions
# ============================================================

async def get_supabase_client():
    """Initialize and return Supabase client."""
    client = init_upload_client()
    if not client:
        raise HTTPException(status_code=500, detail="Failed to initialize Supabase client")
    return client

async def log_workflow_execution(client, workflow_name, status, details=None):
    """Log workflow execution to a table in Supabase."""
    log_data = {
        "workflow_name": workflow_name,
        "status": status,
        "execution_time": datetime.now().isoformat(),
        "details": details or {}
    }
    
    try:
        result = client.table("workflow_execution_logs").insert(log_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error logging workflow execution: {str(e)}")
        return None

# ============================================================
# Workflow 1: Daily Scrape - Scrape job boards and Apify
# ============================================================

@router.post("/daily-scrape")
async def daily_scrape_workflow(
    background_tasks: BackgroundTasks,
    num_apify_runs: int = Query(20, ge=1, le=100),
    apify_items_per_run: int = Query(100, ge=1, le=500),
    apify_api_token: Optional[str] = Query(None)
):
    """
    Complete workflow to perform daily scraping of job sources:
    
    1. Scrape Referral Buddy job board URLs from Supabase
    2. Scrape LinkedIn jobs via Apify and store in Supabase
    
    This workflow is designed to run once per day.
    """
    # Start the workflow in the background so it doesn't timeout the request
    background_tasks.add_task(
        run_daily_scrape_workflow,
        num_apify_runs=num_apify_runs,
        apify_items_per_run=apify_items_per_run,
        apify_api_token=apify_api_token
    )
    
    return {
        "success": True,
        "message": "Daily scrape workflow started in the background",
        "status": "STARTED",
        "workflow_id": f"daily-scrape-{int(time.time())}"
    }

async def run_daily_scrape_workflow(
    num_apify_runs: int,
    apify_items_per_run: int,
    apify_api_token: Optional[str] = None
):
    """
    Run the daily scrape workflow (called by background task).
    """
    workflow_start_time = time.time()
    workflow_results = {
        "workflow_name": "daily-scrape",
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "total_jobs_found": 0
    }
    
    try:
        # Step 1: Get Supabase client
        supabase_client = await init_similarity_client()
        if not supabase_client:
            workflow_results["status"] = "FAILED"
            workflow_results["error"] = "Failed to initialize Supabase client"
            return workflow_results
        
        # Step 2: Scrape Referral Buddy job board URLs from Supabase
        step_start = time.time()
        try:
            query = supabase_client.table("referral_buddy_job_board_urls").select("*").execute()
            referral_urls = query.data if hasattr(query, 'data') else []
            
            step_result = {
                "step": "scrape-referral-buddy",
                "status": "COMPLETED",
                "duration_seconds": round(time.time() - step_start, 2),
                "urls_found": len(referral_urls)
            }
            workflow_results["steps"].append(step_result)
            
            # Log URLs found for debugging
            print(f"Found {len(referral_urls)} referral buddy URLs")
            
        except Exception as e:
            step_result = {
                "step": "scrape-referral-buddy",
                "status": "FAILED",
                "duration_seconds": round(time.time() - step_start, 2),
                "error": str(e)
            }
            workflow_results["steps"].append(step_result)
        
        # Step 3: Scrape LinkedIn jobs via Apify and store in Supabase
        step_start = time.time()
        try:
            # Use provided API token or get from environment
            if not apify_api_token:
                apify_api_token = os.getenv('APIFY_API_TOKEN')
            
            if not apify_api_token:
                raise ValueError("Apify API token is required but not provided")
            
            # Initialize clients
            supabase_client = await init_apify_client()
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
                    num_runs=num_apify_runs,
                    items_per_run=apify_items_per_run
                )
                
                # Parse result to extract job count
                import re
                job_count_match = re.search(r"Total jobs uploaded: (\d+)", result)
                job_count = int(job_count_match.group(1)) if job_count_match else 0
                
                step_result = {
                    "step": "scrape-apify-linkedin",
                    "status": "COMPLETED",
                    "duration_seconds": round(time.time() - step_start, 2),
                    "result_summary": result.split("\n")[0] if isinstance(result, str) else str(result),
                    "jobs_uploaded": job_count
                }
                workflow_results["total_jobs_found"] += job_count
                
            workflow_results["steps"].append(step_result)
            
        except Exception as e:
            step_result = {
                "step": "scrape-apify-linkedin",
                "status": "FAILED",
                "duration_seconds": round(time.time() - step_start, 2),
                "error": str(e)
            }
            workflow_results["steps"].append(step_result)
        
        # Set overall workflow status
        all_steps_completed = all(step["status"] == "COMPLETED" for step in workflow_results["steps"])
        workflow_results["status"] = "COMPLETED" if all_steps_completed else "PARTIAL"
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        
        # Log workflow completion
        await log_workflow_execution(
            supabase_client, 
            "daily-scrape", 
            workflow_results["status"], 
            workflow_results
        )
        
        return workflow_results
        
    except Exception as e:
        workflow_results["status"] = "FAILED"
        workflow_results["error"] = str(e)
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        
        # Try to log workflow failure
        try:
            await log_workflow_execution(
                supabase_client if 'supabase_client' in locals() else await init_similarity_client(), 
                "daily-scrape", 
                "FAILED", 
                workflow_results
            )
        except:
            pass
            
        return workflow_results

# ============================================================
# Workflow 2: Gmail Inbox Scanner (Hourly) - PLACEHOLDER
# ============================================================

@router.post("/scan-gmail-inbox")
async def scan_gmail_inbox_workflow(
    background_tasks: BackgroundTasks,
    hours_back: int = Query(1, ge=1, le=48),
    search_query: str = Query("label:inbox"),
):
    """
    Complete workflow to scan Gmail inbox for job-related emails:
    
    1. Connect to Gmail API
    2. Scan inbox for specified time period
    3. Process and store relevant emails
    
    This workflow is designed to run hourly.
    """
    # Start the workflow in the background
    background_tasks.add_task(
        run_scan_gmail_inbox_workflow,
        hours_back=hours_back,
        search_query=search_query
    )
    
    return {
        "success": True,
        "message": "Gmail inbox scanning workflow started in the background",
        "status": "STARTED",
        "workflow_id": f"gmail-inbox-{int(time.time())}"
    }

async def run_scan_gmail_inbox_workflow(
    hours_back: int,
    search_query: str
):
    """
    Run the Gmail inbox scanning workflow (placeholder implementation).
    """
    workflow_start_time = time.time()
    workflow_results = {
        "workflow_name": "scan-gmail-inbox",
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "total_emails_processed": 0
    }
    
    try:
        # PLACEHOLDER - This would be replaced with actual Gmail API integration
        await asyncio.sleep(2)  # Simulate some processing time
        
        step_result = {
            "step": "scan-gmail-inbox",
            "status": "COMPLETED",
            "duration_seconds": 2,
            "message": "PLACEHOLDER: This is a placeholder for Gmail inbox scanning"
        }
        workflow_results["steps"].append(step_result)
        
        # Set overall workflow status
        workflow_results["status"] = "COMPLETED"
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        
        return workflow_results
        
    except Exception as e:
        workflow_results["status"] = "FAILED"
        workflow_results["error"] = str(e)
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        return workflow_results

# ============================================================
# Workflow 3: Gmail Outbox Scanner (Hourly) - PLACEHOLDER
# ============================================================

@router.post("/scan-gmail-outbox")
async def scan_gmail_outbox_workflow(
    background_tasks: BackgroundTasks,
    hours_back: int = Query(1, ge=1, le=48),
    search_query: str = Query("label:sent"),
):
    """
    Complete workflow to scan Gmail outbox for job-related emails:
    
    1. Connect to Gmail API
    2. Scan outbox/sent mail for specified time period
    3. Process and store relevant emails
    
    This workflow is designed to run hourly.
    """
    # Start the workflow in the background
    background_tasks.add_task(
        run_scan_gmail_outbox_workflow,
        hours_back=hours_back,
        search_query=search_query
    )
    
    return {
        "success": True,
        "message": "Gmail outbox scanning workflow started in the background",
        "status": "STARTED",
        "workflow_id": f"gmail-outbox-{int(time.time())}"
    }

async def run_scan_gmail_outbox_workflow(
    hours_back: int,
    search_query: str
):
    """
    Run the Gmail outbox scanning workflow (placeholder implementation).
    """
    workflow_start_time = time.time()
    workflow_results = {
        "workflow_name": "scan-gmail-outbox",
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "total_emails_processed": 0
    }
    
    try:
        # PLACEHOLDER - This would be replaced with actual Gmail API integration
        await asyncio.sleep(2)  # Simulate some processing time
        
        step_result = {
            "step": "scan-gmail-outbox",
            "status": "COMPLETED",
            "duration_seconds": 2,
            "message": "PLACEHOLDER: This is a placeholder for Gmail outbox scanning"
        }
        workflow_results["steps"].append(step_result)
        
        # Set overall workflow status
        workflow_results["status"] = "COMPLETED"
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        
        return workflow_results
        
    except Exception as e:
        workflow_results["status"] = "FAILED"
        workflow_results["error"] = str(e)
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        return workflow_results

# ============================================================
# Workflow 4: Similarity Search
# ============================================================

@router.post("/similarity-search")
async def similarity_search_workflow(
    background_tasks: BackgroundTasks,
    match_threshold: float = Query(0.6, ge=0.0, le=1.0),
    match_count: int = Query(50, ge=1, le=100),
    create_view: bool = Query(True),
    view_name: Optional[str] = Query(None)
):
    """
    Complete workflow to perform similarity search on jobs:
    
    1. Get starred jobs
    2. Get embeddings for starred jobs
    3. Calculate average embedding
    4. Run similarity search
    5. Optionally create a view with the similar jobs
    
    This workflow is designed to run on demand or scheduled daily.
    """
    # Start the workflow in the background
    background_tasks.add_task(
        run_similarity_search_workflow,
        match_threshold=match_threshold,
        match_count=match_count,
        create_view=create_view,
        view_name=view_name or f"similar_jobs_{datetime.now().strftime('%Y%m%d')}"
    )
    
    return {
        "success": True,
        "message": "Similarity search workflow started in the background",
        "status": "STARTED",
        "workflow_id": f"similarity-search-{int(time.time())}"
    }

async def run_similarity_search_workflow(
    match_threshold: float,
    match_count: int,
    create_view: bool,
    view_name: str
):
    """
    Run the similarity search workflow (called by background task).
    """
    workflow_start_time = time.time()
    workflow_results = {
        "workflow_name": "similarity-search",
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "matching_jobs_found": 0
    }
    
    try:
        # Step 1: Get Supabase client
        supabase_client = await init_similarity_client()
        if not supabase_client:
            workflow_results["status"] = "FAILED"
            workflow_results["error"] = "Failed to initialize Supabase client"
            return workflow_results
            
        # Step 2: Get starred jobs
        step_start = time.time()
        try:
            starred_jobs = await get_starred_jobs(supabase_client)
            
            step_result = {
                "step": "get-starred-jobs",
                "status": "COMPLETED" if starred_jobs else "WARNING",
                "duration_seconds": round(time.time() - step_start, 2),
                "jobs_found": len(starred_jobs)
            }
            workflow_results["steps"].append(step_result)
            
            if not starred_jobs:
                workflow_results["status"] = "COMPLETED_NO_RESULTS"
                workflow_results["message"] = "No starred jobs found to use as basis for similarity search"
                workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
                workflow_results["end_time"] = datetime.now().isoformat()
                
                await log_workflow_execution(
                    supabase_client, 
                    "similarity-search", 
                    "COMPLETED_NO_RESULTS", 
                    workflow_results
                )
                
                return workflow_results
            
        except Exception as e:
            step_result = {
                "step": "get-starred-jobs",
                "status": "FAILED",
                "duration_seconds": round(time.time() - step_start, 2),
                "error": str(e)
            }
            workflow_results["steps"].append(step_result)
            raise e
        
        # Step 3: Get embeddings for starred jobs
        step_start = time.time()
        try:
            job_embeddings = await get_embeddings_for_jobs(supabase_client, starred_jobs)
            
            step_result = {
                "step": "get-embeddings",
                "status": "COMPLETED" if job_embeddings else "WARNING",
                "duration_seconds": round(time.time() - step_start, 2),
                "embeddings_found": len(job_embeddings)
            }
            workflow_results["steps"].append(step_result)
            
            if not job_embeddings:
                workflow_results["status"] = "COMPLETED_NO_RESULTS"
                workflow_results["message"] = "No embeddings found for starred jobs"
                workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
                workflow_results["end_time"] = datetime.now().isoformat()
                
                await log_workflow_execution(
                    supabase_client, 
                    "similarity-search", 
                    "COMPLETED_NO_RESULTS", 
                    workflow_results
                )
                
                return workflow_results
            
        except Exception as e:
            step_result = {
                "step": "get-embeddings",
                "status": "FAILED",
                "duration_seconds": round(time.time() - step_start, 2),
                "error": str(e)
            }
            workflow_results["steps"].append(step_result)
            raise e
        
        # Step 4: Calculate average embedding
        step_start = time.time()
        try:
            avg_embedding = average_embeddings(job_embeddings)
            
            step_result = {
                "step": "average-embeddings",
                "status": "COMPLETED" if avg_embedding else "FAILED",
                "duration_seconds": round(time.time() - step_start, 2)
            }
            workflow_results["steps"].append(step_result)
            
            if not avg_embedding:
                workflow_results["status"] = "FAILED"
                workflow_results["message"] = "Failed to calculate average embedding"
                workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
                workflow_results["end_time"] = datetime.now().isoformat()
                
                await log_workflow_execution(
                    supabase_client, 
                    "similarity-search", 
                    "FAILED", 
                    workflow_results
                )
                
                return workflow_results
            
        except Exception as e:
            step_result = {
                "step": "average-embeddings",
                "status": "FAILED",
                "duration_seconds": round(time.time() - step_start, 2),
                "error": str(e)
            }
            workflow_results["steps"].append(step_result)
            raise e
        
        # Step 5: Run similarity search
        step_start = time.time()
        try:
            similar_jobs = await run_similarity_search(
                supabase_client, 
                avg_embedding, 
                match_count=match_count
            )
            
            step_result = {
                "step": "similarity-search",
                "status": "COMPLETED",
                "duration_seconds": round(time.time() - step_start, 2),
                "jobs_found": len(similar_jobs)
            }
            workflow_results["steps"].append(step_result)
            workflow_results["matching_jobs_found"] = len(similar_jobs)
            
        except Exception as e:
            step_result = {
                "step": "similarity-search",
                "status": "FAILED",
                "duration_seconds": round(time.time() - step_start, 2),
                "error": str(e)
            }
            workflow_results["steps"].append(step_result)
            raise e
        
        # Step 6: Create view (if requested and if we found similar jobs)
        if create_view and similar_jobs:
            step_start = time.time()
            try:
                job_ids = [job.get('id') for job in similar_jobs if job.get('id')]
                
                if job_ids:
                    view_result = await create_similar_jobs_view(
                        supabase_client,
                        job_ids,
                        view_name
                    )
                    
                    step_result = {
                        "step": "create-view",
                        "status": "COMPLETED" if view_result.get('success') else "FAILED",
                        "duration_seconds": round(time.time() - step_start, 2),
                        "view_name": view_name if view_result.get('success') else None,
                        "jobs_in_view": len(job_ids)
                    }
                else:
                    step_result = {
                        "step": "create-view",
                        "status": "SKIPPED",
                        "duration_seconds": round(time.time() - step_start, 2),
                        "message": "No job IDs found to create view"
                    }
                
                workflow_results["steps"].append(step_result)
                
            except Exception as e:
                step_result = {
                    "step": "create-view",
                    "status": "FAILED",
                    "duration_seconds": round(time.time() - step_start, 2),
                    "error": str(e)
                }
                workflow_results["steps"].append(step_result)
                # Don't raise exception here - we still want to return the similarity results
        
        # Set overall workflow status
        all_steps_completed = all(
            step["status"] == "COMPLETED" for step in workflow_results["steps"] 
            if step["step"] != "create-view"  # Allow create-view to be skipped
        )
        workflow_results["status"] = "COMPLETED" if all_steps_completed else "PARTIAL"
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        
        # Store top similar jobs in the result (limited to avoid huge response)
        max_jobs_to_return = min(10, len(similar_jobs))
        workflow_results["top_similar_jobs"] = similar_jobs[:max_jobs_to_return]
        
        # Log workflow completion
        await log_workflow_execution(
            supabase_client, 
            "similarity-search", 
            workflow_results["status"], 
            {
                "starred_jobs": len(starred_jobs),
                "embeddings_found": len(job_embeddings),
                "similar_jobs_found": len(similar_jobs),
                "view_created": create_view and any(step["step"] == "create-view" and step["status"] == "COMPLETED" for step in workflow_results["steps"]),
                "view_name": view_name if create_view else None
            }
        )
        
        return workflow_results
        
    except Exception as e:
        workflow_results["status"] = "FAILED"
        workflow_results["error"] = str(e)
        workflow_results["duration_seconds"] = round(time.time() - workflow_start_time, 2)
        workflow_results["end_time"] = datetime.now().isoformat()
        
        # Try to log workflow failure
        try:
            await log_workflow_execution(
                supabase_client if 'supabase_client' in locals() else await init_similarity_client(), 
                "similarity-search", 
                "FAILED", 
                workflow_results
            )
        except:
            pass
            
        return workflow_results 