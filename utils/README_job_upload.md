# Job Descriptions Upload Utility

This utility allows you to upload job descriptions to the `job_descriptions_metadata` table in Supabase.

## Prerequisites

1. Python 3.7+
2. Supabase client library (`pip install supabase`)
3. Environment variables:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_KEY` or `SUPABASE_KEY`: Your Supabase service or anon key

## Candidate Email and Scrape Keyword Sources

The utilities now automatically retrieve `candidate_email` and `scrape_keyword` values from the `referral_buddy_job_board_urls` table in Supabase. This ensures values are consistently sourced from the database rather than requiring manual input.

The process works as follows:

1. When uploading a job, the utility first checks if a job URL matches any entry in the `referral_buddy_job_board_urls` table
2. If a match is found, the associated `candidate_email` and `scrape_keyword` values are used
3. If no match is found, it uses the most recent entry in the table as a default
4. Manual values can still be provided as parameters to override database values if needed

## URL Cleaning

All job URLs and company URLs are automatically cleaned to remove query parameters:

1. Any URL that contains a question mark (`?`) will have the question mark and everything after it removed
2. This ensures consistent URL formats for matching against the `referral_buddy_job_board_urls` table
3. The cleaning happens automatically when you upload a job, whether through the command line or API

For example:
- Original URL: `https://example.com/jobs/123?source=linkedin&campaign=summer`
- Cleaned URL: `https://example.com/jobs/123`

This cleaning ensures more reliable matching when looking up referral information and prevents duplicate job entries with slightly different URLs.

## Usage

### Single File Upload

You can upload job descriptions from a JSON file using the command-line interface:

```bash
python upload_job_descriptions.py your_job_data.json
```

The JSON file can contain either a single job description object or an array of job descriptions. The system will automatically retrieve `candidate_email` and `scrape_keyword` from the database.

You can still manually specify these values if needed:

```bash
python upload_job_descriptions.py your_job_data.json --email user@example.com --keyword "python developer"
```

### Upload with Required Candidate Email and Scrape Keyword

For workflows where you need to explicitly provide these values:

```bash
python upload_jobs_with_email_keyword.py your_job_data.json --email user@example.com --keyword "data science"
```

This script makes both parameters required to ensure proper job tracking.

### Batch Upload Example

The `upload_batch_jobs.py` script demonstrates how to upload multiple job descriptions at once:

```bash
python upload_batch_jobs.py
```

This script uses the sample data in `sample_batch_job_descriptions.json` by default.

## API Usage

You can also use the provided functions in your own code:

```python
from upload_job_descriptions import upload_job_description, init_supabase_client, get_referral_info_from_supabase, clean_job_url

# Initialize Supabase client
client = init_supabase_client()

# Prepare job data
job_data = {
    "title": "Software Engineer",
    "company_name": "Tech Company",
    "description": "Job description here...",
    "job_url": "https://example.com/jobs/123?source=linkedin"  # URL will be automatically cleaned
}

# Upload the job description - candidate_email and scrape_keyword will be 
# automatically retrieved from the referral_buddy_job_board_urls table
result = upload_job_description(client, job_data)

# You can also manually provide values to override database values
result = upload_job_description(
    client, 
    job_data,
    candidate_email="candidate@example.com",
    scrape_keyword="software engineer"
)

# Check the result
if result["success"]:
    print(f"Successfully uploaded job with ID: {result['data']['id']}")
else:
    print(f"Failed to upload job: {result['message']}")

# If you need to clean URLs manually
clean_url = clean_job_url("https://example.com/jobs/123?param=value")
# Returns: "https://example.com/jobs/123"
```

## Job Description Schema

The `job_descriptions_metadata` table schema includes the following fields (partial list):

- `id` (bigint) - Primary key
- `company_id` (bigint)
- `created_at` (timestamp with time zone)
- `resume` (boolean)
- `has_been_scored` (boolean)
- `has_been_added_to_notion` (boolean)
- `has_been_skipped` (boolean)
- `job_preference_score` (numeric)
- `work_experience_score` (numeric)
- `domain_research` (jsonb)
- `similarity_score` (numeric)
- `remote` (boolean)
- `candidate_email` (text) - Email of the candidate associated with this job
- `scrape_keyword` (text) - The search keyword used to find this job
- `title` (text)
- `company_name` (text)
- `job_url` (text) - Cleaned URL with query parameters removed
- `company_url` (text) - Cleaned URL with query parameters removed
- `description` (text)
- And many more...

See the full schema for a complete list of fields.

### Important Fields for Job Tracking

- `candidate_email`: Associates the job with a specific candidate. This is important for filtering and personalization.
- `scrape_keyword`: Tracks what search term was used to find the job. Useful for analyzing search effectiveness.

## Referral Buddy Job Board URLs Table

The `referral_buddy_job_board_urls` table contains information about job scraping operations:

- `candidate_email`: Email of the candidate associated with the job scraping
- `scrape_keyword`: The keyword or search term used to find jobs
- `job_url`: URL of the specific job posting (optional)
- `created_at`: When the record was created

The system uses this table to maintain consistent mapping between job URLs, candidates, and search terms.

## Sample Files

1. `sample_job_description.json` - Example of a single job description
2. `sample_batch_job_descriptions.json` - Example of multiple job descriptions for batch upload

## Apify Integration

The Apify jobs agent includes functionality to automatically upload job listings from Apify runs to the Supabase database. This integration now:

1. Cleans all job URLs and company URLs by removing query parameters
2. Checks if each job URL matches an entry in the `referral_buddy_job_board_urls` table
3. Uses the matched `candidate_email` and `scrape_keyword` if found
4. Falls back to default values from the most recent entry in the table if no match is found
5. Can still use values extracted from the Apify run input as a fallback

## Notes

- The utility will automatically set defaults for required fields like `created_at` if not provided.
- The `domain_research` field accepts a JSON object with details about the company.
- Error handling includes detailed information about any failures during upload.
- When manually provided, values in the JSON data take precedence over command-line parameters. 