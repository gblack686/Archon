# Job Processing and Outreach Automation

An automated workflow for job searching, analysis, and personalized outreach using AI-powered tools and Supabase for data storage.

## Overview

This project automates the process of:
1. Finding relevant job postings
2. Filtering for US-based remote positions
3. Analyzing job fit using AI
4. Generating personalized outreach messages
5. Tracking the entire process in Supabase

## API Endpoints

The project now includes a FastAPI server with the following endpoints:

### Apify Routes (`/api/apify`)
- `POST /upload-runs`: Upload job listings from Apify runs to Supabase
  - Parameters:
    - `num_runs`: Number of recent runs to process (default: 20)
    - `items_per_run`: Maximum items per run (default: 100)
    - `candidate_email`: Email to associate with listings (optional)
    - `scrape_keyword`: Keyword used for job search (optional)
    - `apify_api_token`: Apify API token (optional)

- `GET /clean-url`: Clean a job URL by removing query parameters
  - Parameters:
    - `url`: The URL to clean

### Workflow Routes (`/api/workflows`)
- `POST /daily-scrape`: Run the daily scrape workflow
  - Parameters:
    - `num_apify_runs`: Number of runs to process (default: 20)
    - `apify_items_per_run`: Items per run (default: 100)
    - `apify_api_token`: Apify API token (optional)

## Next Tasks

1. Job Similarity Search Improvements:
   - Debug and optimize job eligibility checks
   - Add more detailed logging for filtering process
   - Fine-tune remote work and US location detection
   - Implement caching for Scrapfly API calls

2. Outreach Functionality:
   - Complete Claude integration for message generation
   - Add templates for different outreach scenarios
   - Implement tracking for outreach attempts
   - Add rate limiting for API calls

3. Data Management:
   - Implement company information enrichment
   - Add job status tracking workflow
   - Create dashboard views for job processing status
   - Add automated cleanup for outdated job listings

4. Future Enhancements:
   - Move secrets to Google Secret Manager
   - Add more job sources and platforms
   - Implement batch processing for large job sets
   - Add error recovery and retry mechanisms

## Prerequisites

- Python 3.8+
- Supabase account
- Apify API token
- OpenAI API key
- Anthropic API key (for Claude)
- Scrapfly API key (for job eligibility checking)

## Environment Setup

Create a `.env` file with the following variables:

```env
APIFY_TOKEN=your_apify_token_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key
SCRAPFLY_API_KEY=your_scrapfly_key
```

Or set them in your shell:

```powershell
# PowerShell
$env:APIFY_TOKEN="your_apify_token"
$env:SUPABASE_URL="your_supabase_url"
$env:SUPABASE_KEY="your_supabase_key"
$env:OPENAI_API_KEY="your_openai_api_key"
$env:ANTHROPIC_API_KEY="your_anthropic_key"
$env:SCRAPFLY_API_KEY="your_scrapfly_key"
```

```bash
# Bash
export APIFY_TOKEN="your_apify_token"
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
export SCRAPFLY_API_KEY="your_scrapfly_key"
```

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
├── endpoints/
│   ├── apify_routes.py            # Apify API endpoints
│   └── workflow_routes.py         # Workflow API endpoints
├── utils/
│   ├── job_similarity_search.py   # Job matching and filtering
│   └── upload_job_descriptions.py # Job data upload utilities
├── main.py                        # FastAPI application
├── job_processing_workflow.py     # Main workflow orchestrator
└── README.md
```

## Workflow Components

### 1. Job Data Collection
- Scrapes job postings from various sources
- Uploads to Supabase with metadata
- Generates embeddings for similarity matching

### 2. Job Matching
- Uses starred jobs as templates
- Performs similarity search using embeddings
- Filters for US-based remote positions using Scrapfly

### 3. Job Analysis
- Analyzes job fit using Claude AI
- Generates personalized outreach messages
- Saves analysis results to Supabase

### 4. Data Storage
- `job_descriptions_metadata`: Main job data table
- `job_analysis_results`: Analysis and outreach tracking
- `processed_jobs_view`: View of processed jobs

## Usage

### Running the API Server
```bash
uvicorn main:app --reload
```

The API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running the Complete Workflow
```bash
python job_processing_workflow.py
```

The script will:
1. Fetch starred jobs as templates
2. Get embeddings and find similar jobs
3. Check job eligibility (US + remote)
4. Analyze jobs and generate outreach content
5. Save results to Supabase
6. Create a view of processed jobs

## Monitoring and Results

1. Check the job analysis results:
   - Table: `job_analysis_results`
   - Status tracking for each processed job

2. View processed jobs:
   - View: `processed_jobs_view`
   - Contains all eligible jobs with analysis

3. Console output provides:
   - Step-by-step progress updates
   - Summary of processed jobs
   - Next steps for outreach

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your chosen license]
