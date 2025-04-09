# Job Processing and Outreach Automation

An automated workflow for job searching, analysis, and personalized outreach using AI-powered tools and Supabase for data storage.

## Overview

This project automates the process of:
1. Finding relevant job postings
2. Filtering for US-based remote positions
3. Analyzing job fit using AI
4. Generating personalized outreach messages
5. Tracking the entire process in Supabase

## Prerequisites

- Python 3.8+
- Supabase account
- Anthropic API key (for Claude)
- Scrapfly API key (for job eligibility checking)

## Environment Setup

Set the following environment variables:

```powershell
# PowerShell
$env:SUPABASE_URL="your_supabase_url"
$env:SUPABASE_KEY="your_supabase_key"
$env:ANTHROPIC_API_KEY="your_anthropic_key"
$env:SCRAPFLY_API_KEY="your_scrapfly_key"
```

```bash
# Bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
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
├── utils/
│   ├── job_similarity_search.py    # Job matching and filtering
│   └── upload_job_descriptions.py  # Job data upload utilities
├── job_processing_workflow.py      # Main workflow orchestrator
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

Run the complete workflow:
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
