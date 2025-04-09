from __future__ import annotations as _annotations

import asyncio
import os
import json
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
import copy
import time
import httpx

import logfire
from httpx import AsyncClient
from dotenv import load_dotenv

from openai import AsyncOpenAI, OpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, ModelRetry, RunContext

from supabase import create_client, Client as SupabaseClient
import numpy as np

load_dotenv()
llm = os.getenv('LLM_MODEL', 'gpt-4o')

client = AsyncOpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama'
)

model = OpenAIModel(llm) if llm.lower().startswith("gpt") else OpenAIModel(llm, openai_client=client)

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')

# Simple debug function
def debug_print(obj):
    print(f"DEBUG: {obj}")


# Add Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

# Add OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

@dataclass
class Deps:
    client: AsyncClient
    apify_api_token: str | None = None
    supabase_client: SupabaseClient | None = None
    openai_client: AsyncOpenAI | None = None


# Actor ID for LinkedIn Jobs Scraper - Note the tilde instead of hyphen
LINKEDIN_JOBS_SCRAPER_ID = "bebity~linkedin-jobs-scraper"


apify_agent = Agent(
    model,
    system_prompt=f'You are an expert at scraping LinkedIn job listings using Apify. The current date is: {datetime.now().strftime("%Y-%m-%d")}',
    deps_type=Deps,
    retries=2
)


@apify_agent.tool
async def run_actor(
    ctx: RunContext[Deps], 
    input_data: Optional[Dict[str, Any]] = None
) -> str:
    """Run the LinkedIn Jobs Scraper actor asynchronously.
    
    Args:
        ctx: The context.
        input_data: Optional input data for the actor.
        
    Returns:
        str: The response from Apify as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}"
    
    try:
        print(f"Running LinkedIn Jobs Scraper actor asynchronously...")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = input_data if input_data else {}
        
        response = await ctx.deps.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return f"Actor run started successfully. Run ID: {data.get('id', 'Unknown')}"
        
    except Exception as e:
        print(f"Error running actor: {e}")
        return f"Error running actor: {str(e)}"


@apify_agent.tool
async def run_actor_sync(
    ctx: RunContext[Deps], 
    input_data: Optional[Dict[str, Any]] = None
) -> str:
    """Run the LinkedIn Jobs Scraper actor synchronously (wait for completion).
    
    Args:
        ctx: The context.
        input_data: Optional input data for the actor.
        
    Returns:
        str: The response from Apify as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/run-sync?token={ctx.deps.apify_api_token}"
    
    try:
        print(f"Running LinkedIn Jobs Scraper actor synchronously (this may take a while)...")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = input_data if input_data else {}
        
        response = await ctx.deps.client.post(url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        data = response.json()
        
        return f"Actor run completed successfully. Run ID: {data.get('id', 'Unknown')}"
        
    except Exception as e:
        print(f"Error running actor synchronously: {e}")
        return f"Error running actor synchronously: {str(e)}"


@apify_agent.tool
async def run_actor_sync_get_items(
    ctx: RunContext[Deps], 
    search_terms: str, 
    location: str,
    limit: int = 50,
    timeout_seconds: int = 120
) -> str:
    """Run the LinkedIn Jobs Scraper actor synchronously and get dataset items.
    
    Args:
        ctx: The context.
        search_terms: Job search terms or keywords.
        location: Location to search for jobs.
        limit: Maximum number of items to retrieve (default: 50).
        timeout_seconds: Maximum time to wait for the run to complete (default: 120).
        
    Returns:
        str: Job listings from the actor run.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    try:
        # Start the run
        print(f"Starting synchronous run with search terms '{search_terms}' in location '{location}'...")
        run_id = await run_actor(ctx, search_terms, location)
        
        # Check if run_id is None or contains an error message
        if run_id is None or run_id.startswith("Error:"):
            return f"Failed to start actor run: {run_id}"
        
        print(f"Run started with ID: {run_id}")
        
        # Wait for the run to complete with timeout
        start_time = time.time()
        run_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={ctx.deps.apify_api_token}"
        
        while True:
            # Check if we've exceeded the timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                return f"Timeout after {timeout_seconds} seconds. The run may still be in progress. Run ID: {run_id}"
            
            # Check run status
            response = await ctx.deps.client.get(run_url)
            response.raise_for_status()
            run_data = response.json()
            
            status = run_data.get("status")
            print(f"Current run status: {status}")
            
            if status == "SUCCEEDED":
                # Get the dataset ID from the run
                dataset_id = run_data.get("defaultDatasetId")
                if not dataset_id:
                    return "Error: No dataset ID found in the successful run."
                
                print(f"Run completed successfully. Dataset ID: {dataset_id}")
                break
            
            if status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                return f"Run failed with status: {status}"
            
            # Wait before checking again
            await asyncio.sleep(5)
        
        # Get dataset items using the dataset_id from the run
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}&limit={limit}"
        
        print(f"Getting job listings from dataset {dataset_id}...")
        response = await ctx.deps.client.get(dataset_url)
        response.raise_for_status()
        job_listings = response.json()
        
        if not job_listings:
            return f"No job listings found in dataset {dataset_id} from run {run_id}."
        
        # Format job listings nicely
        result = f"Found {len(job_listings)} job listings for '{search_terms}' in '{location}':\n\n"
        
        for i, job in enumerate(job_listings):
            title = job.get("title", "Untitled")
            company = job.get("companyName", "Unknown Company")
            location = job.get("location", "Unknown Location")
            salary = job.get("salary", "Salary not specified")
            url = job.get("jobUrl", "No URL available")
            posted = job.get("postedTime", "Unknown posting time")
            contract = job.get("contractType", "Unknown contract type")
            work_type = job.get("workType", "Unknown work type")
            
            result += f"{i+1}. {title} at {company} ({location})\n"
            result += f"   Salary: {salary}\n"
            result += f"   Posted: {posted}\n"
            result += f"   Contract: {contract}, Type: {work_type}\n"
            result += f"   URL: {url}\n\n"
        
        # Add a link to view all results
        result += f"View all results in the Apify dataset: https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}"
        
        return result
        
    except Exception as e:
        print(f"Error in run_actor_sync_get_items: {e}")
        return f"Error running actor and getting items: {str(e)}"


@apify_agent.tool
async def get_actor(ctx: RunContext[Deps]) -> str:
    """Get LinkedIn Jobs Scraper actor details.
    
    Args:
        ctx: The context.
        
    Returns:
        str: The actor details as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}?token={ctx.deps.apify_api_token}"
    
    try:
        print(f"Getting LinkedIn Jobs Scraper actor details...")
        
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Format the actor details
        name = data.get("name", "Unknown")
        version = data.get("version", "Unknown")
        username = data.get("username", "Unknown")
        created_at = data.get("createdAt", "Unknown")
        
        return f"Actor Details:\nName: {name}\nVersion: {version}\nCreated by: {username}\nCreated at: {created_at}"
        
    except Exception as e:
        print(f"Error getting actor details: {e}")
        return f"Error getting actor details: {str(e)}"


@apify_agent.tool
async def get_actor_versions(ctx: RunContext[Deps]) -> str:
    """Get LinkedIn Jobs Scraper actor versions.
    
    Args:
        ctx: The context.
        
    Returns:
        str: The actor versions as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/versions?token={ctx.deps.apify_api_token}"
    
    try:
        print(f"Getting LinkedIn Jobs Scraper actor versions...")
        
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        versions = data.get("data", [])
        if not versions:
            return "No versions found."
        
        # Format the versions
        results = []
        for version in versions[:5]:  # Limit to 5 versions for readability
            version_number = version.get("versionNumber", "Unknown")
            created_at = version.get("createdAt", "Unknown")
            
            results.append(f"Version: {version_number}\nCreated at: {created_at}\n")
        
        summary = f"Found {len(versions)} versions. Showing latest {min(5, len(versions))}:\n\n"
        return summary + "\n".join(results)
        
    except Exception as e:
        print(f"Error getting actor versions: {e}")
        return f"Error getting actor versions: {str(e)}"


@apify_agent.tool
async def get_actor_webhooks(ctx: RunContext[Deps]) -> str:
    """Get LinkedIn Jobs Scraper actor webhooks.
    
    Args:
        ctx: The context.
        
    Returns:
        str: The actor webhooks as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/webhooks?token={ctx.deps.apify_api_token}"
    
    try:
        print(f"Getting LinkedIn Jobs Scraper actor webhooks...")
        
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        webhooks = data.get("data", [])
        if not webhooks:
            return "No webhooks found."
        
        # Format the webhooks
        results = []
        for webhook in webhooks:
            webhook_id = webhook.get("id", "Unknown")
            url = webhook.get("url", "Unknown")
            event_types = ", ".join(webhook.get("eventTypes", []))
            
            results.append(f"Webhook ID: {webhook_id}\nURL: {url}\nEvent types: {event_types}\n")
        
        summary = f"Found {len(webhooks)} webhooks:\n\n"
        return summary + "\n".join(results)
        
    except Exception as e:
        print(f"Error getting actor webhooks: {e}")
        return f"Error getting actor webhooks: {str(e)}"


@apify_agent.tool
async def get_list_of_runs(ctx: RunContext[Deps], limit: int = 10) -> str:
    """Get list of LinkedIn Jobs Scraper actor runs.
    
    Args:
        ctx: The context.
        limit: Maximum number of runs to return (default: 10).
        
    Returns:
        str: The actor runs as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}&limit={limit}"
    
    try:
        print(f"Getting LinkedIn Jobs Scraper actor runs...")
        
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        runs = data.get("data", {}).get("items", [])
        if not runs:
            return "No runs found."
        
        # Format the runs
        results = []
        for run in runs:
            run_id = run.get("id", "Unknown")
            status = run.get("status", "Unknown")
            started_at = run.get("startedAt", "Unknown")
            finished_at = run.get("finishedAt", "Unknown")
            
            results.append(f"Run ID: {run_id}\nStatus: {status}\nStarted: {started_at}\nFinished: {finished_at}\n")
        
        total = data.get("data", {}).get("total", 0)
        summary = f"Found {total} runs in total. Showing {len(runs)} most recent runs:\n\n"
        return summary + "\n".join(results)
        
    except Exception as e:
        print(f"Error getting actor runs: {e}")
        return f"Error getting actor runs: {str(e)}"


@apify_agent.tool
async def get_last_run(ctx: RunContext[Deps], status: Optional[str] = None) -> str:
    """Get last run of LinkedIn Jobs Scraper actor.
    
    Args:
        ctx: The context.
        status: Optional filter for run status (e.g., "SUCCEEDED").
        
    Returns:
        str: The last run details as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    # For the last run, we'll use the runs endpoint with limit=1 and sort by startedAt
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}&limit=1&desc=true"
    if status:
        url += f"&status={status}"
    
    try:
        print(f"Getting last run of LinkedIn Jobs Scraper actor...")
        
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        runs = data.get("data", {}).get("items", [])
        if not runs:
            return "No last run found."
        
        # Get the first (most recent) run
        run = runs[0]
        
        # Format the run details
        run_id = run.get("id", "Unknown")
        status = run.get("status", "Unknown")
        started_at = run.get("startedAt", "Unknown")
        finished_at = run.get("finishedAt", "Unknown")
        
        details = f"Last Run Details:\nRun ID: {run_id}\nStatus: {status}\nStarted: {started_at}\nFinished: {finished_at}"
        
        if run.get("stats"):
            stats = run.get("stats", {})
            input_body_size = stats.get("inputBodySize", "Unknown")
            output_body_size = stats.get("outputBodySize", "Unknown")
            details += f"\n\nStats:\nInput size: {input_body_size}\nOutput size: {output_body_size}"
        
        return details
        
    except Exception as e:
        print(f"Error getting last run: {e}")
        return f"Error getting last run: {str(e)}"


@apify_agent.tool
async def get_last_run_dataset_items(ctx: RunContext[Deps], limit: int = 10, status: Optional[str] = None) -> str:
    """Get dataset items from the last run of LinkedIn Jobs Scraper actor.
    
    Args:
        ctx: The context.
        limit: Maximum number of items to return (default: 10).
        status: Optional filter for run status (e.g., "SUCCEEDED").
        
    Returns:
        str: The job listings from the last run as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    # First, get the last run ID
    runs_url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}&limit=1&desc=true"
    if status:
        runs_url += f"&status={status}"
    
    try:
        print(f"Getting last run to find dataset ID...")
        
        runs_response = await ctx.deps.client.get(runs_url)
        runs_response.raise_for_status()
        runs_data = runs_response.json()
        
        runs = runs_data.get("data", {}).get("items", [])
        if not runs:
            return "No last run found."
        
        # Get the first (most recent) run
        run = runs[0]
        run_id = run.get("id", "Unknown")
        dataset_id = run.get("defaultDatasetId", "Unknown")
        
        if dataset_id == "Unknown":
            return f"No dataset found for run {run_id}."
        
        # Now get the dataset items
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}&limit={limit}"
        
        print(f"Getting job listings from dataset {dataset_id}...")
        
        items_response = await ctx.deps.client.get(dataset_url)
        items_response.raise_for_status()
        job_listings = items_response.json()
        
        if not job_listings:
            return f"No job listings found in the dataset {dataset_id} for run {run_id}."
        
        # Format the job listings results
        results = []
        for i, job in enumerate(job_listings):
            title = job.get("title", "Unknown Title")
            company = job.get("company", "Unknown Company")
            location = job.get("location", "Unknown Location")
            url = job.get("url", "No URL")
            
            results.append(f"Job {i+1}:\nTitle: {title}\nCompany: {company}\nLocation: {location}\nURL: {url}\n")
        
        summary = f"Found {len(job_listings)} job listings in dataset {dataset_id} for run {run_id}. Showing {len(job_listings)}:\n\n"
        return summary + "\n".join(results)
        
    except Exception as e:
        print(f"Error getting job listings from last run: {e}")
        return f"Error getting job listings from last run: {str(e)}"


@apify_agent.tool
async def get_openapi_definition(ctx: RunContext[Deps]) -> str:
    """Get OpenAPI definition for the LinkedIn Jobs Scraper actor.
    
    Args:
        ctx: The context.
        
    Returns:
        str: The OpenAPI definition summary.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/builds/default/openapi.json"
    
    try:
        print(f"Getting OpenAPI definition for LinkedIn Jobs Scraper actor...")
        
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Return summary of the OpenAPI definition
        title = data.get("info", {}).get("title", "Unknown")
        description = data.get("info", {}).get("description", "No description")
        version = data.get("info", {}).get("version", "Unknown")
        
        paths = list(data.get("paths", {}).keys())
        paths_summary = "\n".join([f"- {path}" for path in paths[:10]])
        
        return f"OpenAPI Definition:\nTitle: {title}\nVersion: {version}\nDescription: {description}\n\nAvailable Paths:\n{paths_summary}"
        
    except Exception as e:
        print(f"Error getting OpenAPI definition: {e}")
        return f"Error getting OpenAPI definition: {str(e)}"


@apify_agent.tool
async def search_linkedin_jobs(
    ctx: RunContext[Deps], 
    search_terms: str,
    location: Optional[str] = None,
    remote: bool = True,
    limit: int = 10
) -> str:
    """Search for jobs on LinkedIn using specific search terms and location.
    
    Args:
        ctx: The context.
        search_terms: The job search query (e.g., "Software Engineer", "Data Scientist").
        location: Optional location for job search (e.g., "New York", "San Francisco").
        remote: Whether to include remote jobs (default: True).
        limit: Maximum number of jobs to return (default: 10).
        
    Returns:
        str: The job listings as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    # Prepare the input for the LinkedIn Jobs Scraper actor
    input_data = {
        "queries": search_terms,
        "maxItems": limit,
        "includeLocation": True
    }
    
    if location:
        input_data["locationQuery"] = location
    
    if remote:
        input_data["remoteFilter"] = "REMOTE"
    
    # Run the actor synchronously and get dataset items
    url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/run-sync-get-dataset-items?token={ctx.deps.apify_api_token}"
    
    try:
        print(f"Searching for '{search_terms}' jobs{' in ' + location if location else ''}{' (remote)' if remote else ''}...")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = await ctx.deps.client.post(url, json=input_data, headers=headers, timeout=300)
        response.raise_for_status()
        job_listings = response.json()
        
        if not job_listings:
            return f"No job listings found for '{search_terms}'{' in ' + location if location else ''}{' (remote)' if remote else ''}."
        
        # Format the job listings results
        results = []
        for i, job in enumerate(job_listings[:limit]):
            title = job.get("title", "Unknown Title")
            company = job.get("company", "Unknown Company")
            job_location = job.get("location", "Unknown Location")
            url = job.get("url", "No URL")
            description = job.get("description", "No description available")
            
            # Truncate description if too long
            if description and len(description) > 200:
                description = description[:200] + "..."
            
            results.append(f"Job {i+1}:\nTitle: {title}\nCompany: {company}\nLocation: {job_location}\nURL: {url}\nDescription: {description}\n")
        
        summary = f"Found {len(job_listings)} job listings for '{search_terms}'{' in ' + location if location else ''}{' (remote)' if remote else ''}. Showing {min(limit, len(job_listings))}:\n\n"
        return summary + "\n".join(results)
        
    except Exception as e:
        print(f"Error searching for jobs: {e}")
        return f"Error searching for jobs: {str(e)}"


@apify_agent.tool
async def save_run_items_to_csv(
    ctx: RunContext[Deps], 
    run_id: Optional[str] = None,
    limit: int = 100,
    output_path: Optional[str] = None
) -> str:
    """Save job listings from a specific run (or last run if not specified) to a CSV file.
    
    Args:
        ctx: The context.
        run_id: Optional specific run ID (defaults to last run if not provided).
        limit: Maximum number of items to save (default: 100).
        output_path: Optional custom output path for the CSV file.
        
    Returns:
        str: Information about the saved CSV file.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    try:
        dataset_id = None
        
        # If no run_id is provided, get the last run ID
        if not run_id:
            print("No run ID provided, getting last run...")
            runs_url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}&limit=1&desc=true"
            
            response = await ctx.deps.client.get(runs_url)
            response.raise_for_status()
            runs_data = response.json()
            
            runs = runs_data.get("data", {}).get("items", [])
            if not runs:
                return "No last run found."
            
            # Get the first (most recent) run
            run = runs[0]
            run_id = run.get("id", "Unknown")
            dataset_id = run.get("defaultDatasetId", "Unknown")
            
            print(f"Using last run ID: {run_id}, dataset ID: {dataset_id}")
        
        # If we have a run_id but no dataset_id, get the run details to find the dataset_id
        if run_id and not dataset_id:
            run_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={ctx.deps.apify_api_token}"
            
            response = await ctx.deps.client.get(run_url)
            response.raise_for_status()
            run_data = response.json()
            
            dataset_id = run_data.get("defaultDatasetId")
            
            if not dataset_id:
                return f"No dataset found for run {run_id}."
        
        # Get dataset items using the dataset_id
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}&limit={limit}"
        
        print(f"Getting job listings from dataset {dataset_id}...")
        response = await ctx.deps.client.get(dataset_url)
        response.raise_for_status()
        job_listings = response.json()
        
        if not job_listings:
            return f"No job listings found in dataset {dataset_id} for run {run_id}."
        
        # Create output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_dir = Path("./apify_data")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"linkedin_jobs_{run_id}_{timestamp}.csv"
        else:
            output_path = Path(output_path)
            # Ensure directory exists
            output_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Define CSV fields - using a comprehensive list of possible fields
        fieldnames = [
            "title", "company", "location", "url", "description", 
            "postedAt", "salary", "jobId", "companyUrl", "workplaceType", 
            "seniorityLevel", "jobFunction", "employmentType", "industries"
        ]
        
        # Default values for fields to ensure all columns have data
        default_values = {
            "title": "No Title Provided",
            "company": "Unknown Company",
            "location": "Unknown Location",
            "url": "No URL Provided",
            "description": "No Description Available",
            "postedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "salary": "Salary Not Specified",
            "jobId": f"unknown-{datetime.now().timestamp()}",
            "companyUrl": "No Company URL",
            "workplaceType": "Not Specified",
            "seniorityLevel": "Not Specified",
            "jobFunction": "Not Specified",
            "employmentType": "Not Specified",
            "industries": "Not Specified"
        }
        
        # Write to CSV
        job_count = 0
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in job_listings:
                # Create job data with default values, then update with actual data
                job_data = default_values.copy()
                for field in fieldnames:
                    if field in job and job[field]:
                        job_data[field] = job[field]
                
                writer.writerow(job_data)
                job_count += 1
        
        return f"Successfully saved {job_count} job listings from run {run_id} (dataset {dataset_id}) to {output_path} with all columns populated"
        
    except Exception as e:
        print(f"Error saving job listings to CSV: {e}")
        return f"Error saving job listings to CSV: {str(e)}"


@apify_agent.tool
async def save_multiple_runs_to_csv(
    ctx: RunContext[Deps], 
    num_runs: int = 20,
    items_per_run: int = 100,
    output_dir: Optional[str] = None
) -> str:
    """Save job listings from multiple recent runs to CSV files.
    
    Args:
        ctx: The context.
        num_runs: Number of recent runs to process (default: 20).
        items_per_run: Maximum number of items to save per run (default: 100).
        output_dir: Optional custom output directory for the CSV files.
        
    Returns:
        str: Information about the saved CSV files.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    try:
        # Get list of recent runs
        url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}&limit={num_runs}"
        
        print(f"Getting list of {num_runs} recent runs...")
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        runs = data.get("data", {}).get("items", [])
        if not runs:
            return "No runs found."
        
        # Create output directory if not provided
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = Path(f"./apify_data/batch_{timestamp}")
        else:
            output_path = Path(output_dir)
        
        output_path.mkdir(exist_ok=True, parents=True)
        print(f"Saving data to directory: {output_path}")
        
        # Define CSV fields - using a comprehensive list of possible fields
        fieldnames = [
            "title", "company", "location", "url", "description", 
            "postedAt", "salary", "jobId", "companyUrl", "workplaceType", 
            "seniorityLevel", "jobFunction", "employmentType", "industries"
        ]
        
        # Default values for fields to ensure all columns have data
        default_values = {
            "title": "No Title Provided",
            "company": "Unknown Company",
            "location": "Unknown Location",
            "url": "No URL Provided",
            "description": "No Description Available",
            "postedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "salary": "Salary Not Specified",
            "jobId": f"unknown-{datetime.now().timestamp()}",
            "companyUrl": "No Company URL",
            "workplaceType": "Not Specified",
            "seniorityLevel": "Not Specified",
            "jobFunction": "Not Specified",
            "employmentType": "Not Specified",
            "industries": "Not Specified"
        }
        
        # Process each run
        successful_saves = 0
        run_details = []
        
        for run in runs:
            run_id = run.get("id")
            status = run.get("status")
            dataset_id = run.get("defaultDatasetId")
            
            if not run_id or status != "SUCCEEDED" or not dataset_id:
                run_details.append(f"Run {run_id}: Skipped (status={status}, dataset_id={dataset_id})")
                continue
                
            try:
                # Get dataset items for this run
                items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}&limit={items_per_run}"
                
                print(f"Getting job listings from dataset {dataset_id} for run {run_id}...")
                items_response = await ctx.deps.client.get(items_url)
                items_response.raise_for_status()
                job_listings = items_response.json()
                
                if not job_listings:
                    run_details.append(f"Run {run_id}: No job listings found in dataset {dataset_id}")
                    continue
                
                # Define the output file path
                csv_path = output_path / f"linkedin_jobs_{run_id}.csv"
                
                # Write to CSV
                job_count = 0
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for job in job_listings:
                        # Create job data with default values, then update with actual data
                        job_data = default_values.copy()
                        for field in fieldnames:
                            if field in job and job[field]:
                                job_data[field] = job[field]
                        
                        writer.writerow(job_data)
                        job_count += 1
                
                run_details.append(f"Run {run_id}: Saved {job_count} job listings to {csv_path} with all columns populated")
                successful_saves += 1
                
            except Exception as e:
                run_details.append(f"Run {run_id}: Error - {str(e)}")
        
        total_runs = data.get("data", {}).get("total", 0)
        summary = f"Found {total_runs} total runs, processed {len(runs)} runs, successfully saved data from {successful_saves} runs to {output_path}\n\n"
        details = "\n".join(run_details)
        return summary + details
        
    except Exception as e:
        print(f"Error saving multiple runs to CSV: {e}")
        return f"Error saving multiple runs to CSV: {str(e)}"


@apify_agent.tool
async def list_actors(ctx: RunContext[Deps], limit: int = 10) -> str:
    """List available Apify actors in your account.
    
    Args:
        ctx: The context.
        limit: Maximum number of actors to return (default: 10).
        
    Returns:
        str: The available actors as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts?token={ctx.deps.apify_api_token}&limit={limit}"
    
    try:
        print(f"Getting available Apify actors...")
        
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        actors = data.get("data", [])
        if not actors:
            return "No actors found in your account."
        
        # Format the actors
        results = []
        for actor in actors:
            actor_id = actor.get("id", "Unknown")
            name = actor.get("name", "Unknown")
            username = actor.get("username", "Unknown")
            
            results.append(f"Actor ID: {actor_id}\nName: {name}\nUsername: {username}\n")
        
        summary = f"Found {len(actors)} actors in your account. Showing first {min(limit, len(actors))}:\n\n"
        return summary + "\n".join(results)
        
    except Exception as e:
        print(f"Error listing actors: {e}")
        return f"Error listing actors: {str(e)}"


@apify_agent.tool
async def run_actor_by_id(
    ctx: RunContext[Deps], 
    actor_id: str,
    input_data: Optional[Dict[str, Any]] = None
) -> str:
    """Run any Apify actor by its ID.
    
    Args:
        ctx: The context.
        actor_id: The ID of the actor to run.
        input_data: Optional input data for the actor.
        
    Returns:
        str: The response from Apify as a formatted string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={ctx.deps.apify_api_token}"
    
    try:
        print(f"Running actor {actor_id} asynchronously...")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = input_data if input_data else {}
        
        response = await ctx.deps.client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return f"Actor run started successfully. Run ID: {data.get('id', 'Unknown')}"
        
    except Exception as e:
        print(f"Error running actor: {e}")
        return f"Error running actor: {str(e)}"


@apify_agent.tool
async def get_dataset_items(
    ctx: RunContext[Deps],
    dataset_id: Optional[str] = None,
    run_id: Optional[str] = None,
    limit: int = 100
) -> str:
    """Get items from a specific dataset or from the last run's dataset.
    
    Args:
        ctx: The context.
        dataset_id: Optional specific dataset ID. If not provided, will use the dataset from run_id or last run.
        run_id: Optional run ID to get its dataset. If not provided and dataset_id not provided, will use last run.
        limit: Maximum number of items to retrieve (default: 100).
        
    Returns:
        str: Dataset items formatted as a readable string.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    try:
        # Get dataset ID - either directly or from run
        if not dataset_id and not run_id:
            # Get the last run to find its dataset ID
            print("No dataset ID or run ID provided, getting last run...")
            runs_url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}&limit=1&desc=true"
            
            response = await ctx.deps.client.get(runs_url)
            response.raise_for_status()
            runs_data = response.json()
            
            runs = runs_data.get("data", {}).get("items", [])
            if not runs:
                return "No last run found."
            
            # Get the first (most recent) run
            run = runs[0]
            run_id = run.get("id", "Unknown")
            dataset_id = run.get("defaultDatasetId", None)
            
            if not dataset_id:
                return f"No dataset found for last run (ID: {run_id})."
            
            print(f"Using dataset ID {dataset_id} from last run (ID: {run_id})")
        
        # If we have run_id but no dataset_id, get the run details to find its dataset_id
        elif run_id and not dataset_id:
            run_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={ctx.deps.apify_api_token}"
            
            response = await ctx.deps.client.get(run_url)
            response.raise_for_status()
            run_data = response.json()
            
            dataset_id = run_data.get("defaultDatasetId")
            
            if not dataset_id:
                return f"No dataset found for run {run_id}."
            
            print(f"Using dataset ID {dataset_id} from run ID {run_id}")
        
        # Get items from the dataset
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}&limit={limit}"
        
        print(f"Getting items from dataset {dataset_id}...")
        response = await ctx.deps.client.get(dataset_url)
        response.raise_for_status()
        items = response.json()
        
        if not items:
            return f"No items found in dataset {dataset_id}."
        
        # Format items nicely
        result = f"Found {len(items)} items in dataset {dataset_id}:\n\n"
        
        for i, item in enumerate(items):
            # For LinkedIn jobs, format accordingly
            if "title" in item and "companyName" in item:
                title = item.get("title", "Untitled")
                company = item.get("companyName", "Unknown Company")
                location = item.get("location", "Unknown Location")
                salary = item.get("salary", "Salary not specified")
                url = item.get("jobUrl", "No URL available")
                
                result += f"{i+1}. {title} at {company} ({location})\n"
                result += f"   Salary: {salary}\n"
                result += f"   URL: {url}\n\n"
            else:
                # Generic item formatting for non-job datasets
                result += f"{i+1}. {json.dumps(item, indent=2)}\n\n"
        
        # Add a link to view all results
        result += f"View all results: https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}"
        
        return result
        
    except Exception as e:
        print(f"Error getting dataset items: {e}")
        return f"Error getting dataset items: {str(e)}"


@apify_agent.tool
async def get_dataset_items_direct(
    ctx: RunContext[Deps],
    dataset_id: str = "Qn5etT6dwP9NkXgAJ",
    limit: int = 100
) -> str:
    """Get items directly from a specific Apify dataset using its ID.
    
    Args:
        ctx: The context.
        dataset_id: The dataset ID to fetch (default: Qn5etT6dwP9NkXgAJ).
        limit: Maximum number of items to retrieve (default: 100).
        
    Returns:
        str: Dataset items formatted as a readable string.
    """
    try:
        # Use direct URL construction that's known to work
        if dataset_id == "Qn5etT6dwP9NkXgAJ":
            # Use the exact URL for this specific dataset
            dataset_url = "https://api.apify.com/v2/datasets/Qn5etT6dwP9NkXgAJ/items?token=apify_api_0wk0jQUT9aO2LC2XlyKiucdyY0XoGH4hpV53"
        else:
            # For other datasets, construct URL with the token
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token=apify_api_0wk0jQUT9aO2LC2XlyKiucdyY0XoGH4hpV53&limit={limit}"
        
        print(f"Getting items directly from dataset {dataset_id}...")
        response = await ctx.deps.client.get(dataset_url)
        response.raise_for_status()
        items = response.json()
        
        if not items:
            return f"No items found in dataset {dataset_id}."
        
        # Format items nicely
        result = f"Found {len(items)} items in dataset {dataset_id}:\n\n"
        
        for i, item in enumerate(items):
            # For LinkedIn jobs, format accordingly
            if "title" in item and "companyName" in item:
                title = item.get("title", "Untitled")
                company = item.get("companyName", "Unknown Company")
                location = item.get("location", "Unknown Location")
                salary = item.get("salary", "Salary not specified")
                url = item.get("jobUrl", "No URL available")
                
                result += f"{i+1}. {title} at {company} ({location})\n"
                result += f"   Salary: {salary}\n"
                result += f"   URL: {url}\n\n"
            else:
                # Generic item formatting for non-job datasets
                result += f"{i+1}. {json.dumps(item, indent=2)}\n\n"
        
        # Add a link to view all results
        result += f"View all results: {dataset_url}"
        
        return result
        
    except Exception as e:
        print(f"Error getting dataset items directly: {e}")
        return f"Error getting dataset items directly: {str(e)}"


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

async def init_openai_client() -> Optional[AsyncOpenAI]:
    """Initialize and return an OpenAI client."""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        return None
    
    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        print("✓ Connected to OpenAI")
        return client
    except Exception as e:
        print(f"Error connecting to OpenAI: {str(e)}")
        return None

async def extract_job_responsibilities(description: str, openai_client: AsyncOpenAI) -> str:
    """
    Extract just the job responsibilities section from a job description using regex.
    If regex fails, return the full description as fallback.
    
    Args:
        description: The full job description text
        openai_client: The OpenAI client (only needed for embeddings, not for extraction)
        
    Returns:
        str: The extracted job responsibilities section or full description
    """
    if not description:
        return ""
    
    # If description is too short, it might not have distinct sections
    if len(description) < 100:
        return description
    
    try:
        # Try regex patterns to identify responsibility sections
        responsibility_headers = [
            r'Responsibilities',
            r'Key Responsibilities',
            r'Job Responsibilities',
            r'Duties',
            r'Key Duties',
            r'What you\'ll do',
            r'About the role',
            r'Job Description',
            r'The Role',
            r'In this role'
        ]
        
        # Try to find sections that start with responsibility headers
        for header in responsibility_headers:
            pattern = rf'(?i){header}[\s:]*\n(.*?)(?:\n\n|\n[A-Z]|\Z)'
            matches = re.search(pattern, description, re.DOTALL)
            if matches:
                responsibilities = matches.group(1).strip()
                if len(responsibilities) > 50:  # Ensure we got a meaningful section
                    return responsibilities
        
        # Try splitting by headers to find the responsibility section
        sections = re.split(r'\n\s*(?:Responsibilities|Requirements|Qualifications|About the role|Job Description|What you\'ll do|Duties|Key Responsibilities)[\s:]*\n', description)
        if len(sections) > 1:
            # Take the section after "Responsibilities" or similar header
            section = sections[1].strip()
            # Try to find where the next section begins (like Requirements or Qualifications)
            end_markers = re.search(r'\n\s*(?:Requirements|Qualifications|Benefits|About you|About us|Company|Who you are)', section)
            if end_markers:
                return section[:end_markers.start()].strip()
            return section
        
        # Return the full description as fallback (no OpenAI API call)
        print("Regex extraction failed, using full description as fallback")
        return description
        
    except Exception as e:
        print(f"Error extracting job responsibilities: {str(e)}")
        # Return original description on error
        return description

async def generate_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """
    Generate an embedding vector for text using OpenAI.
    
    Args:
        text: The text to embed
        openai_client: The OpenAI client
        
    Returns:
        List[float]: The embedding vector
    """
    if not openai_client:
        print("Error: OpenAI client not initialized.")
        return []
    
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return []

async def upload_to_vector_store(
    supabase_client: SupabaseClient,
    content: str,
    metadata: Dict[str, Any],
    embedding: List[float]
) -> Dict[str, Any]:
    """
    Upload a document to the job_descriptions_vector_store table.
    
    Args:
        supabase_client: The Supabase client
        content: The job description content (responsibilities)
        metadata: The metadata for the job
        embedding: The embedding vector
        
    Returns:
        Dict[str, Any]: The response from Supabase
    """
    try:
        # Convert embedding to PostgreSQL array format - convert from list to numpy array to get correct datatype
        embedding_array = np.array(embedding)
        
        # Prepare data for insertion
        vector_store_data = {
            "content": content,
            "metadata": metadata,
            "embedding": embedding_array.tolist()
        }
        
        # Insert into vector store table
        result = supabase_client.table("job_descriptions_vector_store").insert(vector_store_data).execute()
        
        return result.data[0] if result.data else {"id": None}
    except Exception as e:
        print(f"Error uploading to vector store: {str(e)}")
        return {"error": str(e)}

async def get_referral_info_from_supabase(
    supabase_client: SupabaseClient, 
    job_url: str = None
) -> Dict[str, Any]:
    """
    Query the referral buddy job board urls table to get candidate_email and scrape_keyword.
    
    Args:
        supabase_client: Supabase client
        job_url: URL of the job posting (optional)
        
    Returns:
        Dict[str, Any]: Dictionary containing candidate_email and scrape_keyword
    """
    if not supabase_client:
        print("Error: Supabase client not initialized")
        return {"candidate_email": None, "scrape_keyword": None}
    
    try:
        # Query the referral buddy job board urls table
        query = supabase_client.table("referral_buddy_job_board_urls").select("candidate_email, scrape_keyword")
        
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

@apify_agent.tool
async def upload_apify_runs_to_supabase(
    ctx: RunContext[Deps],
    num_runs: int = 20,
    items_per_run: int = 100,
    candidate_email: str = None,
    scrape_keyword: str = None
) -> str:
    """Fetch the last N runs from Apify, get their dataset items, and upload to job_descriptions_metadata table.
    
    Args:
        ctx: The context.
        num_runs: Number of recent runs to process (default: 20).
        items_per_run: Maximum number of items to fetch per run (default: 100).
        candidate_email: Email to associate with the job listings (default: None).
        scrape_keyword: Keyword used to scrape/find these jobs (default: None).
        
    Returns:
        str: Summary of the upload operation.
    """
    if ctx.deps.apify_api_token is None:
        return "API token is required. Please provide an Apify API token."
    
    # Initialize Supabase client if not provided in deps
    supabase_client = ctx.deps.supabase_client
    if supabase_client is None:
        supabase_client = await init_supabase_client()
        if not supabase_client:
            return "Failed to initialize Supabase client. Check your environment variables."
    
    # Initialize OpenAI client for embeddings
    openai_client = ctx.deps.openai_client
    if openai_client is None:
        openai_client = await init_openai_client()
        if not openai_client:
            print("Warning: OpenAI client initialization failed. Vector store uploads will be skipped.")
    
    try:
        # Get list of recent runs
        url = f"https://api.apify.com/v2/acts/{LINKEDIN_JOBS_SCRAPER_ID}/runs?token={ctx.deps.apify_api_token}&limit={num_runs}"
        
        print(f"Getting list of {num_runs} recent runs...")
        response = await ctx.deps.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        runs = data.get("data", {}).get("items", [])
        if not runs:
            return "No runs found."
        
        # If no default candidate_email provided, try to get from database
        if not candidate_email:
            default_referral = await get_referral_info_from_supabase(supabase_client)
            candidate_email = default_referral.get("candidate_email", "system@upload.com")
            if not scrape_keyword:
                scrape_keyword = default_referral.get("scrape_keyword")
            
            print(f"Using default values from database - Email: {candidate_email}, Keyword: {scrape_keyword or 'None'}")
        
        # Process each run
        total_runs = len(runs)
        successful_uploads = 0
        total_jobs_uploaded = 0
        total_vector_uploads = 0
        runs_results = []
        
        for i, run in enumerate(runs):
            run_id = run.get("id")
            status = run.get("status")
            dataset_id = run.get("defaultDatasetId")
            
            print(f"Processing run {i+1}/{total_runs}: {run_id} (status: {status})")
            
            if not run_id or status != "SUCCEEDED" or not dataset_id:
                runs_results.append(f"Run {run_id}: Skipped (status={status}, dataset_id={dataset_id})")
                continue
                
            try:
                # Get dataset items for this run
                items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={ctx.deps.apify_api_token}&limit={items_per_run}"
                
                print(f"Getting job listings from dataset {dataset_id} for run {run_id}...")
                items_response = await ctx.deps.client.get(items_url)
                items_response.raise_for_status()
                job_listings = items_response.json()
                
                if not job_listings:
                    runs_results.append(f"Run {run_id}: No job listings found in dataset {dataset_id}")
                    continue
                
                # Try to extract search keywords from the run input
                run_input_url = f"https://api.apify.com/v2/actor-runs/{run_id}/input?token={ctx.deps.apify_api_token}"
                run_keyword = scrape_keyword
                
                try:
                    input_response = await ctx.deps.client.get(run_input_url)
                    if input_response.status_code == 200:
                        run_input = input_response.json()
                        # Try to extract keywords from the input
                        if "keyword" in run_input:
                            run_keyword = run_input["keyword"]
                        elif "search" in run_input:
                            run_keyword = run_input["search"]
                        elif "searchTerms" in run_input:
                            run_keyword = run_input["searchTerms"]
                        elif "queries" in run_input:
                            run_keyword = run_input["queries"]
                        
                        print(f"Found search keyword from run: {run_keyword}")
                except Exception as e:
                    print(f"Could not retrieve run input: {str(e)}")
                
                # Upload jobs to Supabase
                jobs_uploaded = 0
                vector_uploads = 0
                current_timestamp = datetime.now().isoformat()
                
                for job in job_listings:
                    # Get the job URL and clean it by removing query parameters
                    original_job_url = job.get("jobUrl", "")
                    job_url = clean_job_url(original_job_url)
                    
                    if original_job_url != job_url:
                        print(f"Cleaned job URL: {original_job_url} -> {job_url}")
                    
                    # Try to get referral info for this specific job URL
                    job_referral_info = {"candidate_email": None, "scrape_keyword": None}
                    if job_url:
                        job_referral_info = await get_referral_info_from_supabase(supabase_client, job_url)
                    
                    # Use job-specific values if available, otherwise fall back to defaults
                    job_candidate_email = job_referral_info.get("candidate_email") or candidate_email
                    job_scrape_keyword = job_referral_info.get("scrape_keyword") or run_keyword
                    
                    # Map Apify job data to job_descriptions_metadata schema
                    job_data = {
                        "created_at": current_timestamp,
                        "candidate_email": job_candidate_email,
                        "scrape_keyword": job_scrape_keyword,
                        "title": job.get("title", ""),
                        "company_name": job.get("companyName", ""),
                        "company_url": clean_job_url(job.get("companySiteUrl", "")),
                        "job_url": job_url,  # Use the cleaned URL
                        "location": job.get("location", ""),
                        "work_type": job.get("workType", ""),
                        "contract_type": job.get("contractType", ""),
                        "salary": job.get("salary", ""),
                        "description": job.get("description", ""),
                        "benefits": job.get("benefits", ""),
                        "posted_time": job.get("postedTime", ""),
                        "published_at": job.get("postedAt", ""),
                        "remote": "remote" in job.get("location", "").lower(),
                        "has_been_scored": False,
                        "has_been_added_to_notion": False,
                        "has_been_skipped": False,
                        "domain_research": {}
                    }
                    
                    # Extract company domain from company URL
                    company_url = clean_job_url(job.get("companySiteUrl", ""))
                    if company_url:
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(company_url)
                            job_data["company_domain"] = parsed_url.netloc.replace("www.", "")
                        except Exception:
                            pass
                    
                    try:
                        # Insert data into job_descriptions_metadata table
                        print(f"Uploading job: {job_data['title']} at {job_data['company_name']}")
                        print(f"Candidate email: {job_data['candidate_email']}")
                        print(f"Scrape keyword: {job_data.get('scrape_keyword', 'Not provided')}")
                        print(f"Job URL: {job_data['job_url']}")
                        
                        result = supabase_client.table("job_descriptions_metadata").insert(job_data).execute()
                        
                        # Check if insert was successful
                        if hasattr(result, 'data') and result.data:
                            jobs_uploaded += 1
                            inserted_job_id = result.data[0].get('id')
                            print(f"Successfully uploaded job with ID: {inserted_job_id}")
                            
                            # Process for vector store if OpenAI client is available
                            if openai_client:
                                # Extract job responsibilities from the full description
                                full_description = job_data["description"]
                                responsibilities = await extract_job_responsibilities(full_description, openai_client)
                                
                                # Generate embedding for responsibilities
                                embedding = await generate_embedding(responsibilities, openai_client)
                                
                                if embedding:
                                    # Prepare metadata for vector store
                                    vector_metadata = {
                                        "title": job_data["title"],
                                        "posted_at": job_data["published_at"],
                                        "location": job_data["location"],
                                        "employment_type": job_data["contract_type"],
                                        "candidate_email": job_data["candidate_email"],
                                        "scrape_keyword": job_data.get("scrape_keyword"),
                                        "jobUrl": job_data["job_url"]  # Use the cleaned URL
                                    }
                                    
                                    # Upload to vector store
                                    vector_result = await upload_to_vector_store(
                                        supabase_client, 
                                        responsibilities, 
                                        vector_metadata, 
                                        embedding
                                    )
                                    
                                    if "id" in vector_result:
                                        vector_uploads += 1
                                        print(f"Successfully uploaded to vector store with ID: {vector_result['id']}")
                        
                    except Exception as e:
                        print(f"Error uploading job: {str(e)}")
                
                total_jobs_uploaded += jobs_uploaded
                total_vector_uploads += vector_uploads
                successful_uploads += 1 if jobs_uploaded > 0 else 0
                runs_results.append(f"Run {run_id}: Uploaded {jobs_uploaded} of {len(job_listings)} jobs, {vector_uploads} to vector store")
                
            except Exception as e:
                print(f"Error processing run {run_id}: {str(e)}")
                runs_results.append(f"Run {run_id}: Error - {str(e)}")
        
        # Generate summary
        summary = f"Processed {total_runs} runs, successfully uploaded jobs from {successful_uploads} runs.\n"
        summary += f"Total jobs uploaded: {total_jobs_uploaded}, Total vector store records: {total_vector_uploads}\n\n"
        summary += "Run Details:\n" + "\n".join(runs_results)
        
        return summary
        
    except Exception as e:
        print(f"Error in upload_apify_runs_to_supabase: {e}")
        return f"Error: {str(e)}"

async def main():
    """Run the example."""
    # Load environment variables for API keys
    apify_api_token = os.getenv('APIFY_API_TOKEN')
    if not apify_api_token:
        # If no environment token, use the hardcoded token that works
        apify_api_token = "apify_api_0wk0jQUT9aO2LC2XlyKiucdyY0XoGH4hpV53"
    
    print(f"Using API token: {apify_api_token[:4]}...{apify_api_token[-4:]}")
    
    # Initialize Supabase client
    supabase_client = await init_supabase_client()
    
    # Initialize OpenAI client
    openai_client = await init_openai_client()
    
    async with httpx.AsyncClient() as client:
        deps = Deps(
            client=client, 
            apify_api_token=apify_api_token,
            supabase_client=supabase_client,
            openai_client=openai_client
        )

        # Example: Use the agent to upload Apify runs to Supabase
        print("\n=== Upload Apify Runs to Supabase ===")
        
        # Get candidate_email and scrape_keyword from referral_buddy_job_board_urls table
        # Values will be fetched automatically in the upload_apify_runs_to_supabase function
        result = await apify_agent.run(
            'Upload the last 20 runs from Apify to the job_descriptions_metadata table in Supabase and also prepare and upload job responsibilities to the vector store', 
            deps=deps
        )
        print('Upload Response:', result.data)


if __name__ == "__main__":
    asyncio.run(main()) 