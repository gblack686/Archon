import os
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from supabase import create_client, Client as SupabaseClient

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
TOP_RESULTS = 50  # Number of top similar jobs to retrieve

async def init_supabase_client() -> Optional[SupabaseClient]:
    """Initialize and return a Supabase client."""
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

async def get_starred_jobs(supabase_client: SupabaseClient) -> List[Dict[str, Any]]:
    """
    Get all jobs from job_descriptions_metadata where star_send_skip = 'star' or 'Star'.
    
    Args:
        supabase_client: The Supabase client
        
    Returns:
        List[Dict[str, Any]]: List of starred jobs
    """
    try:
        # Try with "Star" (capital S) first
        result = supabase_client.table("job_descriptions_metadata") \
            .select("*") \
            .eq("star_send_skip", "Star") \
            .execute()
        
        starred_jobs = result.data
        
        # If no results, try with lowercase "star"
        if not starred_jobs:
            result = supabase_client.table("job_descriptions_metadata") \
                .select("*") \
                .eq("star_send_skip", "star") \
                .execute()
            
            starred_jobs = result.data
        
        print(f"Found {len(starred_jobs)} starred jobs")
        
        if len(starred_jobs) == 0:
            print("No starred jobs found. Please star some jobs first.")
            print("Note: The script checks for both 'star' and 'Star' values in the star_send_skip column.")
        
        return starred_jobs
    except Exception as e:
        print(f"Error getting starred jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

async def get_embeddings_for_jobs(supabase_client: SupabaseClient, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get embeddings for starred jobs from job_descriptions_vector_store.
    
    Args:
        supabase_client: The Supabase client
        jobs: List of starred jobs
        
    Returns:
        List[Dict[str, Any]]: List of job embeddings
    """
    job_embeddings = []
    
    for job in jobs:
        job_url = job.get("job_url")
        if not job_url:
            print(f"Skipping job {job.get('id')}: No job_url")
            continue
            
        try:
            # Query the vector store for this job URL
            result = supabase_client.table("job_descriptions_vector_store") \
                .select("id, content, metadata, embedding") \
                .filter("metadata->>jobUrl", "eq", job_url) \
                .execute()
            
            if result.data and len(result.data) > 0:
                embedding_record = result.data[0]
                
                # Ensure embedding is a numeric array and not a string
                embedding_data = embedding_record.get("embedding", [])
                
                # Debug the embedding data type
                print(f"Embedding type: {type(embedding_data)}")
                if isinstance(embedding_data, str):
                    print("Warning: embedding is stored as string, attempting to convert...")
                    try:
                        import json
                        embedding_data = json.loads(embedding_data)
                    except Exception as e:
                        print(f"Failed to parse embedding string: {str(e)}")
                        continue
                
                # Further validation
                if not embedding_data or not isinstance(embedding_data, (list, np.ndarray)):
                    print(f"Invalid embedding format for job {job.get('id')}, skipping")
                    continue
                
                # Ensure all elements are numeric
                try:
                    # Convert to numpy array to validate
                    embedding_array = np.array(embedding_data, dtype=np.float64)
                    
                    job_embeddings.append({
                        "id": embedding_record["id"],
                        "job_id": job["id"],
                        "job_url": job_url,
                        "title": job.get("title", ""),
                        "company": job.get("company_name", ""),
                        "embedding": embedding_array
                    })
                    print(f"Found embedding for job: {job.get('title')} at {job.get('company_name')}")
                except (ValueError, TypeError) as e:
                    print(f"Error converting embedding to numeric array: {str(e)}")
                    print(f"Embedding sample (first 5 elements): {str(embedding_data[:5] if isinstance(embedding_data, list) and len(embedding_data) > 5 else embedding_data)}")
                    continue
            else:
                print(f"No embedding found for job URL: {job_url}")
        except Exception as e:
            print(f"Error getting embedding for job {job.get('id')}: {str(e)}")
    
    print(f"Found embeddings for {len(job_embeddings)} out of {len(jobs)} starred jobs")
    return job_embeddings

def average_embeddings(job_embeddings: List[Dict[str, Any]]) -> List[float]:
    """
    Calculate the average embedding vector from multiple job embeddings.
    
    Args:
        job_embeddings: List of job embeddings
        
    Returns:
        List[float]: The averaged embedding vector
    """
    if not job_embeddings:
        return []
        
    # Extract embedding arrays from the job embeddings
    embedding_arrays = []
    for job in job_embeddings:
        if "embedding" in job:
            # Ensure embedding is a numpy array with float64 data type
            if isinstance(job["embedding"], np.ndarray):
                embedding_arrays.append(job["embedding"])
            else:
                # Convert to numpy array if it's not already
                try:
                    embedding_arrays.append(np.array(job["embedding"], dtype=np.float64))
                except Exception as e:
                    print(f"Skipping embedding that couldn't be converted to numeric array: {str(e)}")
    
    if not embedding_arrays or len(embedding_arrays) == 0:
        print("No valid embedding arrays found")
        return []
        
    # Print debugging information
    print(f"Number of valid embedding arrays: {len(embedding_arrays)}")
    print(f"Shape of first embedding array: {embedding_arrays[0].shape}")
    
    try:
        # Calculate the average embedding
        average_embedding = np.mean(embedding_arrays, axis=0)
        
        # Normalize the average embedding (for cosine similarity)
        norm = np.linalg.norm(average_embedding)
        if norm > 0:
            average_embedding = average_embedding / norm
            
        return average_embedding.tolist()
    except Exception as e:
        print(f"Error calculating average embedding: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

async def run_similarity_search(supabase_client: SupabaseClient, target_embedding: List[float], top_n: int = 50) -> List[Dict[str, Any]]:
    """
    Run a similarity search against the vector store using the target embedding.
    
    Args:
        supabase_client: The Supabase client
        target_embedding: The target embedding vector to search against
        top_n: Number of top results to return
        
    Returns:
        List[Dict[str, Any]]: List of similar jobs
    """
    if not target_embedding:
        print("Error: Target embedding is empty")
        return []
        
    try:
        # Run the similarity search with a custom RPC call
        # We need to use RPC because the pgvector similarity search needs to be done on the server
        result = supabase_client.rpc(
            "match_job_descriptions", 
            {
                "query_embedding": target_embedding,
                "match_count": top_n
            },
            # Add HTTP options with a longer timeout similar to n8n config
            options={
                "headers": {
                    "Content-Profile": "public",
                    "Prefer": "count=exact"
                },
                "timeout": 1000000  # Set a long timeout (in milliseconds)
            }
        ).execute()
        
        similar_jobs = result.data
        print(f"Found {len(similar_jobs)} similar jobs")
        return similar_jobs
    except Exception as e:
        print(f"Error running similarity search: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

async def create_similar_jobs_view(supabase_client: SupabaseClient, similar_jobs: List[Dict[str, Any]]) -> bool:
    """
    Create a view of similar jobs by inserting them into a results table.
    
    Args:
        supabase_client: The Supabase client
        similar_jobs: List of similar jobs
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not similar_jobs:
        print("No similar jobs to create view")
        return False
        
    try:
        # Create a fresh table for results - first delete existing data
        print("Clearing existing similar jobs results...")
        result = supabase_client.table("similar_jobs_results").delete().gte("id", 0).execute()
        
        # Insert the similar jobs
        print(f"Inserting {len(similar_jobs)} similar jobs into results table...")
        
        # Prepare the data for insertion
        insert_data = []
        for i, job in enumerate(similar_jobs):
            # Extract the metadata for easier access
            metadata = job.get("metadata", {})
            
            insert_data.append({
                "rank": i + 1,
                "similarity_score": job.get("similarity", 0),
                "job_title": metadata.get("title", ""),
                "job_location": metadata.get("location", ""),
                "job_url": metadata.get("jobUrl", ""),
                "job_type": metadata.get("employment_type", ""),
                "candidate_email": metadata.get("candidate_email", ""),
                "content": job.get("content", ""),
                "vector_id": job.get("id", None)
            })
        
        # Insert in batches to avoid hitting limits
        batch_size = 50
        for i in range(0, len(insert_data), batch_size):
            batch = insert_data[i:i+batch_size]
            result = supabase_client.table("similar_jobs_results").insert(batch).execute()
            
        print(f"Successfully created view of {len(similar_jobs)} similar jobs")
        return True
    except Exception as e:
        print(f"Error creating similar jobs view: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function to run the similarity search and create a view."""
    print("== Job Similarity Search Tool ==")
    
    # Initialize Supabase client
    supabase_client = await init_supabase_client()
    if not supabase_client:
        print("Failed to initialize Supabase client. Exiting.")
        return
    
    # Step 1: Get starred jobs
    starred_jobs = await get_starred_jobs(supabase_client)
    if not starred_jobs:
        return
    
    # Step 2: Get embeddings for starred jobs
    job_embeddings = await get_embeddings_for_jobs(supabase_client, starred_jobs)
    if not job_embeddings:
        print("No embeddings found for starred jobs. Please ensure jobs are properly indexed in the vector store.")
        return
    
    # Step 3: Calculate the average embedding
    average_embedding = average_embeddings(job_embeddings)
    if not average_embedding:
        print("Failed to calculate average embedding. Exiting.")
        return
    
    print(f"Successfully calculated average embedding from {len(job_embeddings)} starred jobs")
    
    # Step 4: Run similarity search
    similar_jobs = await run_similarity_search(supabase_client, average_embedding, TOP_RESULTS)
    if not similar_jobs:
        print("No similar jobs found. Exiting.")
        return
    
    # Step 5: Create a view of similar jobs
    success = await create_similar_jobs_view(supabase_client, similar_jobs)
    
    if success:
        print("\n== Success ==")
        print(f"Successfully found {len(similar_jobs)} similar jobs based on {len(job_embeddings)} starred jobs.")
        print("The results are available in the 'similar_jobs_results' table.")
    else:
        print("\n== Error ==")
        print("Failed to create view of similar jobs.")

if __name__ == "__main__":
    asyncio.run(main()) 