from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import json
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))

# Import utility functions
from utils.upload_job_descriptions import (
    init_supabase_client,
    upload_job_description,
    upload_job_descriptions_from_file,
    clean_job_url
)

router = APIRouter()

# Dependency to get Supabase client
async def get_supabase_client():
    client = init_supabase_client()
    if not client:
        raise HTTPException(status_code=500, detail="Failed to initialize Supabase client")
    return client

@router.post("/upload")
async def upload_job(
    job_data: Dict[str, Any] = Body(...),
    candidate_email: Optional[str] = Form(None),
    scrape_keyword: Optional[str] = Form(None),
    client = Depends(get_supabase_client)
):
    """
    Upload a single job description
    
    - **job_data**: Job description data (JSON)
    - **candidate_email**: Email of the candidate associated with this job search
    - **scrape_keyword**: Keyword used to scrape/find this job
    """
    try:
        result = upload_job_description(
            client, 
            job_data, 
            candidate_email=candidate_email, 
            scrape_keyword=scrape_keyword
        )
        
        if result.get("success"):
            return JSONResponse(
                status_code=201,
                content=result
            )
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

@router.post("/upload/batch")
async def upload_batch_jobs(
    jobs: List[Dict[str, Any]] = Body(...),
    candidate_email: Optional[str] = Form(None),
    scrape_keyword: Optional[str] = Form(None),
    client = Depends(get_supabase_client)
):
    """
    Upload multiple job descriptions in batch
    
    - **jobs**: Array of job description data (JSON)
    - **candidate_email**: Email of the candidate associated with this job search
    - **scrape_keyword**: Keyword used to scrape/find these jobs
    """
    try:
        results = {
            "total": len(jobs),
            "successful": 0,
            "failed": 0,
            "job_ids": []
        }
        
        for job in jobs:
            result = upload_job_description(
                client, 
                job, 
                candidate_email=candidate_email, 
                scrape_keyword=scrape_keyword
            )
            
            if result.get("success"):
                results["successful"] += 1
                if "data" in result and "id" in result["data"]:
                    results["job_ids"].append(result["data"]["id"])
            else:
                results["failed"] += 1
        
        return JSONResponse(
            status_code=200,
            content={
                "success": results["failed"] == 0,
                "message": f"Uploaded {results['successful']} of {results['total']} jobs",
                "results": results
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

@router.post("/upload/file")
async def upload_job_file(
    file: UploadFile = File(...),
    candidate_email: Optional[str] = Form(None),
    scrape_keyword: Optional[str] = Form(None)
):
    """
    Upload job descriptions from a JSON file
    
    - **file**: JSON file containing job description(s)
    - **candidate_email**: Email of the candidate associated with this job search
    - **scrape_keyword**: Keyword used to scrape/find these jobs
    """
    try:
        # Create a temporary file to store the uploaded content
        temp_file_path = f"temp_{file.filename}"
        
        # Write the uploaded file content to the temporary file
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Process the file
        result = upload_job_descriptions_from_file(
            temp_file_path,
            candidate_email=candidate_email,
            scrape_keyword=scrape_keyword
        )
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        if result.get("success"):
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            return JSONResponse(
                status_code=400,
                content=result
            )
    except Exception as e:
        # Make sure to clean up temporary file even if an error occurs
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
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