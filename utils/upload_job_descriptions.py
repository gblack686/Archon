#!/usr/bin/env python3
"""
Utility for uploading job descriptions to the job_descriptions_metadata Supabase table.
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

def init_supabase_client() -> Optional[Client]:
    """
    Initialize and return a Supabase client.
    
    Returns:
        Optional[Client]: Supabase client or None if initialization fails
    """
    if not SUPABASE_AVAILABLE:
        print("Error: Supabase package not installed. Run: pip install supabase")
        return None
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY/SUPABASE_KEY not found in environment variables.")
        return None
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Connected to Supabase")
        return client
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return None

def get_referral_info_from_supabase(client: Client, job_url: str = None) -> Dict[str, str]:
    """
    Query the referral buddy job board urls table to get candidate_email and scrape_keyword.
    
    Args:
        client: Supabase client
        job_url: URL of the job posting (optional)
        
    Returns:
        Dict[str, str]: Dictionary containing candidate_email and scrape_keyword
    """
    if not client:
        print("Error: Supabase client not initialized")
        return {"candidate_email": None, "scrape_keyword": None}
    
    try:
        # Query the referral buddy job board urls table
        query = client.table("referral_buddy_job_board_urls").select("candidate_email, scrape_keyword")
        
        # If job_url is provided, try to match it
        if job_url:
            query = query.eq("job_url", job_url)
        
        # Execute the query and get the most recent entry if multiple exist
        result = query.order("created_at", desc=True).limit(1).execute()
        
        if hasattr(result, 'data') and result.data:
            candidate_email = result.data[0].get("candidate_email")
            scrape_keyword = result.data[0].get("scrape_keyword")
            
            print(f"Found referral info: Email: {candidate_email}, Keyword: {scrape_keyword}")
            return {
                "candidate_email": candidate_email,
                "scrape_keyword": scrape_keyword
            }
        else:
            print("No referral info found in the database")
            return {"candidate_email": None, "scrape_keyword": None}
    
    except Exception as e:
        print(f"Error getting referral info: {str(e)}")
        return {"candidate_email": None, "scrape_keyword": None}

def clean_job_url(url: str) -> str:
    """
    Clean a job URL by removing the question mark and all characters after it.
    
    Args:
        url: The URL to clean
        
    Returns:
        str: The cleaned URL
    """
    if not url:
        return ""
    
    # Remove question mark and everything after it
    cleaned_url = url.split('?')[0]
    return cleaned_url

def upload_job_description(
    client: Client, 
    job_data: Dict[str, Any],
    candidate_email: str = None,
    scrape_keyword: str = None
) -> Dict[str, Any]:
    """
    Upload a job description to the job_descriptions_metadata table.
    
    Args:
        client: Supabase client
        job_data: Job description data
        candidate_email: Email of the candidate associated with this job search
        scrape_keyword: Keyword used to scrape/find this job
        
    Returns:
        Dict[str, Any]: Response data or error information
    """
    if not client:
        return {"success": False, "message": "Supabase client not initialized"}
    
    # Clean the job URL by removing query parameters
    job_url = job_data.get("job_url")
    if job_url:
        original_url = job_url
        job_url = clean_job_url(job_url)
        
        if original_url != job_url:
            print(f"Cleaned job URL: {original_url} -> {job_url}")
            job_data["job_url"] = job_url
    
    # If job_url is in the data, try to get referral info from the database
    if job_url:
        referral_info = get_referral_info_from_supabase(client, job_url)
        
        # Use database values if available and no override values provided
        if referral_info["candidate_email"] and not candidate_email:
            candidate_email = referral_info["candidate_email"]
        
        if referral_info["scrape_keyword"] and not scrape_keyword:
            scrape_keyword = referral_info["scrape_keyword"]
    
    # Clean company URL if present
    company_url = job_data.get("company_url")
    if company_url:
        job_data["company_url"] = clean_job_url(company_url)
    
    # Set default values and timestamps
    now = datetime.now().isoformat()
    
    # Default values for required fields
    default_data = {
        "created_at": now,
        "has_been_scored": False,
        "has_been_added_to_notion": False,
        "has_been_skipped": False
    }
    
    # Add candidate_email and scrape_keyword if provided
    if candidate_email:
        default_data["candidate_email"] = candidate_email
    
    if scrape_keyword:
        default_data["scrape_keyword"] = scrape_keyword
    
    # Merge provided data with defaults
    merged_data = {**default_data, **job_data}
    
    try:
        print(f"Uploading job description: {merged_data.get('title', 'Untitled')}")
        print(f"Candidate email: {merged_data.get('candidate_email', 'Not provided')}")
        print(f"Scrape keyword: {merged_data.get('scrape_keyword', 'Not provided')}")
        print(f"Job URL: {merged_data.get('job_url', 'Not provided')}")
        
        # Insert data into job_descriptions_metadata table
        result = client.table("job_descriptions_metadata").insert(merged_data).execute()
        
        # Process result
        if hasattr(result, 'data') and result.data:
            print(f"✓ Successfully uploaded job with ID: {result.data[0].get('id')}")
            return {
                "success": True,
                "message": "Job description uploaded successfully",
                "data": result.data[0]
            }
        else:
            print("✗ Upload may have failed")
            return {
                "success": False,
                "message": "Upload may have failed, no data returned",
                "data": result
            }
    
    except Exception as e:
        error_msg = f"Error uploading job description: {str(e)}"
        print(f"✗ {error_msg}")
        
        # Additional error details if available
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response details: {e.response.text}")
        
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }

def upload_job_descriptions_from_file(
    file_path: str, 
    candidate_email: str = None,
    scrape_keyword: str = None
) -> Dict[str, Any]:
    """
    Upload job descriptions from a JSON file.
    
    Args:
        file_path: Path to JSON file containing job descriptions
        candidate_email: Email of the candidate associated with this job search
        scrape_keyword: Keyword used to scrape/find these jobs
        
    Returns:
        Dict[str, Any]: Summary of upload results
    """
    client = init_supabase_client()
    if not client:
        return {"success": False, "message": "Failed to initialize Supabase client"}
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle both single job (dict) and multiple jobs (list)
        jobs = data if isinstance(data, list) else [data]
        
        results = {
            "total": len(jobs),
            "successful": 0,
            "failed": 0,
            "job_ids": []
        }
        
        for job in jobs:
            # Check if the job data already includes candidate_email/scrape_keyword
            job_candidate_email = job.get("candidate_email", candidate_email)
            job_scrape_keyword = job.get("scrape_keyword", scrape_keyword)
            
            result = upload_job_description(
                client, 
                job,
                candidate_email=job_candidate_email,
                scrape_keyword=job_scrape_keyword
            )
            
            if result["success"]:
                results["successful"] += 1
                if "data" in result and "id" in result["data"]:
                    results["job_ids"].append(result["data"]["id"])
            else:
                results["failed"] += 1
        
        return {
            "success": results["failed"] == 0,
            "message": f"Uploaded {results['successful']} of {results['total']} job descriptions",
            "results": results
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing file: {str(e)}",
            "error": str(e)
        }

def main():
    """Command line interface for job description upload."""
    parser = argparse.ArgumentParser(description="Upload job descriptions to Supabase")
    parser.add_argument("file", help="JSON file containing job description data")
    parser.add_argument("--email", help="Candidate email to associate with job descriptions")
    parser.add_argument("--keyword", help="Scrape keyword used to find these jobs")
    args = parser.parse_args()
    
    result = upload_job_descriptions_from_file(
        args.file,
        candidate_email=args.email,
        scrape_keyword=args.keyword
    )
    
    print(f"\nSummary: {result['message']}")
    
    if not result["success"]:
        exit(1)

if __name__ == "__main__":
    main() 