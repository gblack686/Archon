#!/usr/bin/env python3
"""
Script to demonstrate batch uploading of job descriptions to Supabase.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path if importing from same directory
current_dir = Path(__file__).parent
if current_dir not in sys.path:
    sys.path.append(str(current_dir))

from upload_job_descriptions import upload_job_descriptions_from_file, init_supabase_client

def main():
    """
    Main function to demonstrate batch job upload.
    """
    print("Job Descriptions Batch Upload Utility")
    print("====================================")
    
    # Check if sample file exists
    sample_file = current_dir / "sample_batch_job_descriptions.json"
    if not sample_file.exists():
        print(f"Error: Sample file not found at {sample_file}")
        print("Please make sure the sample_batch_job_descriptions.json file exists.")
        sys.exit(1)
    
    # Initialize Supabase client
    client = init_supabase_client()
    if not client:
        print("Failed to initialize Supabase client. Please check your environment variables.")
        sys.exit(1)
    
    # Log start time for benchmarking
    start_time = datetime.now()
    print(f"Starting upload at {start_time.strftime('%H:%M:%S')}")
    
    # Upload job descriptions
    result = upload_job_descriptions_from_file(str(sample_file))
    
    # Log end time and calculate duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Print summary
    print("\nUpload Summary:")
    print(f"  Total job descriptions: {result['results']['total']}")
    print(f"  Successfully uploaded: {result['results']['successful']}")
    print(f"  Failed uploads: {result['results']['failed']}")
    print(f"  Time taken: {duration:.2f} seconds")
    
    # Print job IDs if available
    if result['results']['job_ids']:
        print("\nUploaded Job IDs:")
        for job_id in result['results']['job_ids']:
            print(f"  - {job_id}")
    
    # Return exit code based on success
    return 0 if result["success"] else 1

if __name__ == "__main__":
    sys.exit(main()) 