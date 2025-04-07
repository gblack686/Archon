#!/usr/bin/env python3
# run_onboarding.py - Script to run the entire onboarding flow from LinkedIn profile to Notion workspace

import os
import sys
import json
import argparse
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import the necessary modules
from workflows.leadmagic_adapter import LeadMagicAdapter
from workflows.notion_workspace_manager import NotionWorkspaceManager
from workflows.supabase_adapter import SupabaseAdapter
from workflows.google_drive import CandidateDocumentManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize console
console = Console()

def parse_linkedin_url(url: str) -> str:
    """
    Parse and validate LinkedIn URL
    
    Args:
        url: LinkedIn profile URL
        
    Returns:
        Cleaned LinkedIn URL
    """
    # Convert to lowercase
    url = url.lower()
    
    # Ensure URL has https:// prefix
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Ensure the URL is a LinkedIn profile
    if not 'linkedin.com/in/' in url:
        raise ValueError("Invalid LinkedIn URL. Must be a profile URL (linkedin.com/in/...)")
    
    return url

def extract_profile_data(linkedin_url: str) -> Dict[str, Any]:
    """
    Extract profile data from LinkedIn URL using LeadMagic
    
    Args:
        linkedin_url: LinkedIn profile URL
        
    Returns:
        Dictionary with profile data
    """
    console.print(Panel("[bold blue]Step 1: Extracting LinkedIn Profile Data[/]", 
                        expand=False, 
                        border_style="blue"))
    
    # Create the LeadMagic adapter
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Fetching LinkedIn profile...", total=None)
        
        # Initialize LeadMagic adapter
        leadmagic = LeadMagicAdapter(use_mock=False)
        
        # Extract profile data
        profile_data = leadmagic.get_profile_data(linkedin_url)
        
        progress.update(task, completed=True, description="[green]✓ LinkedIn profile data retrieved successfully")
    
    # Parse the username from URL
    username = linkedin_url.split('linkedin.com/in/')[1].rstrip('/')
    name = profile_data.get('name', 'Unknown')
    
    if name == 'Unknown' and 'personalInfo' in profile_data:
        name = profile_data.get('personalInfo', {}).get('name', username)
    
    console.print(f"[green]✓ Extracted profile data for:[/] [bold]{name}[/]")
    console.print(f"  [blue]LinkedIn:[/] {linkedin_url}")
    
    return profile_data

def enrich_profile_data(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich profile data with additional information using LeadMagic
    
    Args:
        profile_data: Raw profile data from LeadMagic
        
    Returns:
        Enriched profile data
    """
    console.print(Panel("[bold blue]Step 2: Enriching Profile Data[/]", 
                        expand=False, 
                        border_style="blue"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Enriching profile data...", total=None)
        
        # Initialize LeadMagic adapter
        leadmagic = LeadMagicAdapter(use_mock=False)
        
        # Enrich profile data
        enriched_data = leadmagic.enrich_profile(profile_data)
        
        progress.update(task, completed=True, description="[green]✓ Profile data enriched successfully")
    
    console.print(f"[green]✓ Enhanced profile with additional data[/]")
    
    # Print summary of enriched data
    if 'experience' in enriched_data:
        console.print(f"  [blue]Experience entries:[/] {len(enriched_data['experience'])}")
    if 'education' in enriched_data:
        console.print(f"  [blue]Education entries:[/] {len(enriched_data['education'])}")
    if 'skills' in enriched_data:
        console.print(f"  [blue]Skills:[/] {len(enriched_data['skills'])}")
    
    return enriched_data

def setup_notion_workspace(profile_data: Dict[str, Any], enriched_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set up Notion workspace for candidate
    
    Args:
        profile_data: Raw profile data
        enriched_data: Enriched profile data
        
    Returns:
        Dictionary with workspace information
    """
    console.print(Panel("[bold blue]Step 3: Setting Up Notion Workspace[/]", 
                        expand=False, 
                        border_style="blue"))
    
    # Get candidate name and URL
    name = profile_data.get('name', 'Unknown')
    if name == 'Unknown' and 'personalInfo' in enriched_data:
        name = enriched_data.get('personalInfo', {}).get('name', 'Candidate')
    
    linkedin_url = enriched_data.get('personalInfo', {}).get('profileUrl', '')
    
    candidate_info = {
        'name': name,
        'linkedin_url': linkedin_url
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Creating Notion workspace...", total=None)
        
        # Initialize Notion manager
        notion_manager = NotionWorkspaceManager(use_mock=False)
        
        # Set up workspace
        campaigns_db_id = os.getenv('NOTION_DATABASE_ID', '17b9e1785265802c8599c6d75810c77e')
        
        # Create campaign page
        campaign_title = f"{name}'s Job Search Campaign"
        campaign_page = notion_manager.create_campaign_page(
            title=campaign_title,
            description=f"Job search campaign for {name}. Created on {datetime.now().strftime('%Y-%m-%d')}",
            candidate_info=candidate_info
        )
        
        campaign_page_id = campaign_page['id']
        
        # Create databases
        progress.update(task, description="[cyan]Creating Jobs database...")
        jobs_db = notion_manager.create_jobs_database(campaign_page_id)
        
        progress.update(task, description="[cyan]Creating Companies database...")
        companies_db = notion_manager.create_companies_database(campaign_page_id)
        
        progress.update(task, description="[cyan]Creating Contacts database...")
        contacts_db = notion_manager.create_contacts_database(campaign_page_id)
        
        progress.update(task, description="[cyan]Creating Touchpoints database...")
        touchpoints_db = notion_manager.create_touchpoints_database(campaign_page_id)
        
        progress.update(task, description="[cyan]Creating Workflow database...")
        workflow_db = notion_manager.create_workflow_database(campaign_page_id)
        
        progress.update(task, description="[cyan]Creating Gmail Threads database...")
        threads_db = notion_manager.create_threads_database(campaign_page_id)
        
        # Establish database relations
        progress.update(task, description="[cyan]Setting up database relations...")
        notion_manager.establish_database_relations(
            jobs_db_id=jobs_db['id'],
            companies_db_id=companies_db['id'],
            contacts_db_id=contacts_db['id'],
            touchpoints_db_id=touchpoints_db['id']
        )
        
        # Create workspace result
        workspace = {
            'campaign_page': campaign_page,
            'databases': {
                'jobs': jobs_db,
                'companies': companies_db,
                'contacts': contacts_db,
                'touchpoints': touchpoints_db,
                'workflow': workflow_db,
                'threads': threads_db
            }
        }
        
        progress.update(task, completed=True, description="[green]✓ Notion workspace created successfully")
    
    console.print(f"[green]✓ Created Notion workspace for:[/] [bold]{name}[/]")
    console.print(f"  [blue]Campaign page:[/] {campaign_page.get('url', 'N/A')}")
    
    return workspace

def populate_initial_data(workspace: Dict[str, Any], profile_data: Dict[str, Any], enriched_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Populate initial data in the Notion workspace
    
    Args:
        workspace: Workspace information
        profile_data: Raw profile data
        enriched_data: Enriched profile data
        
    Returns:
        Dictionary with population results
    """
    # This would be implemented to add initial data to databases
    console.print(Panel("[bold blue]Step 4: Initial Data Population[/]", 
                        expand=False, 
                        border_style="blue"))
    
    console.print("[yellow]Note:[/] Initial data population is not yet implemented.")
    console.print("Would populate contacts from the candidate's network, and add sample jobs and companies.")
    
    # For now, just return an empty result
    return {
        'status': 'not_implemented',
        'message': 'Initial data population is not yet implemented'
    }

def setup_google_drive(profile_data: Dict[str, Any], enriched_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set up Google Drive folder and documents for candidate
    
    Args:
        profile_data: Raw profile data
        enriched_data: Enriched profile data
        
    Returns:
        Dictionary with Google Drive information
    """
    console.print(Panel("[bold blue]Step 3: Setting Up Google Drive Documents[/]", 
                        expand=False, 
                        border_style="blue"))
    
    # Get candidate name and email
    name = profile_data.get('name', 'Unknown')
    if name == 'Unknown' and 'personalInfo' in enriched_data:
        name = enriched_data.get('personalInfo', {}).get('name', 'Candidate')
    
    email = enriched_data.get('personalInfo', {}).get('email', '')
    
    candidate_info = {
        'name': name,
        'email': email
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Creating Google Drive documents...", total=None)
        
        # Initialize Google Drive document manager
        use_mock = os.getenv("MOCK_API_RESPONSES", "false").lower() == "true"
        doc_manager = CandidateDocumentManager(use_mock=use_mock)
        
        # Set up Google Drive documents
        drive_results = doc_manager.setup_candidate_drive(
            candidate_info,
            enriched_data
        )
        
        progress.update(task, completed=True, description="[green]✓ Google Drive documents created successfully")
    
    console.print(f"[green]✓ Created Google Drive folder for:[/] [bold]{name}[/]")
    console.print(f"  [blue]Drive folder:[/] {drive_results['folder']['webViewLink']}")
    console.print("  [blue]Documents created:[/]")
    
    for doc_type, doc_info in drive_results['documents'].items():
        console.print(f"    - {doc_info['name']}: {doc_info['webViewLink']}")
    
    return drive_results

def save_metadata(profile_data: Dict[str, Any], enriched_data: Dict[str, Any], workspace: Dict[str, Any], drive_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save metadata about the onboarding process to local file, Supabase campaigns table,
    and the referral_buddy_candidate_info table
    
    Args:
        profile_data: Raw profile data
        enriched_data: Enriched profile data
        workspace: Workspace information
        drive_results: Google Drive information
        
    Returns:
        Dictionary with metadata and storage information
    """
    console.print(Panel("[bold blue]Step 5: Saving Metadata[/]", 
                        expand=False, 
                        border_style="blue"))
    
    # Create candidate info
    candidate_name = profile_data.get('name', enriched_data.get('personalInfo', {}).get('name', 'Unknown'))
    linkedin_url = enriched_data.get('personalInfo', {}).get('profileUrl', '')
    
    # Extract email from profile data
    candidate_email = enriched_data.get('personalInfo', {}).get('email', '')
    
    # Extract target job titles
    target_job_titles = enriched_data.get('personalInfo', {}).get('targetJobTitles', '')
    
    # Extract education info if available
    education_schools = []
    if 'education' in enriched_data:
        education_schools = [edu.get('school', '') for edu in enriched_data.get('education', []) if edu.get('school')]
    
    # Extract location if available
    metropolitan_area = enriched_data.get('personalInfo', {}).get('location', 'Unknown Location')
    
    # Create candidate info object
    candidate_info = {
        'name': candidate_name,
        'linkedin_url': linkedin_url,
        'email': candidate_email,
        'target_job_titles': target_job_titles
    }
    
    # Create local metadata file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    candidate_name_safe = candidate_name.lower().replace(' ', '_')
    
    # Create filename
    filename = f"onboarding_{candidate_name_safe}_{timestamp}.json"
    
    # Create metadata for file
    file_metadata = {
        'timestamp': datetime.now().isoformat(),
        'candidate': candidate_info,
        'workspace': {
            'campaign_page_id': workspace['campaign_page']['id'],
            'campaign_page_url': workspace['campaign_page'].get('url', 'N/A'),
            'databases': {
                'jobs': workspace['databases']['jobs']['id'],
                'companies': workspace['databases']['companies']['id'],
                'contacts': workspace['databases']['contacts']['id'],
                'touchpoints': workspace['databases']['touchpoints']['id'],
                'workflow': workspace['databases']['workflow']['id'],
                'threads': workspace['databases']['threads']['id']
            }
        }
    }
    
    # Save to local file
    with open(filename, 'w') as f:
        json.dump(file_metadata, f, indent=2, default=str)
    
    console.print(f"[green]✓ Saved metadata to local file:[/] {filename}")
    
    # Save to Supabase
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Storing metadata in Supabase...", total=None)
        
        # Initialize Supabase adapter
        supabase_adapter = SupabaseAdapter(use_mock=os.getenv("MOCK_API_RESPONSES", "false").lower() == "true")
        
        # Store campaign metadata
        db_metadata = supabase_adapter.store_campaign_metadata(
            candidate_info=candidate_info,
            profile_data=enriched_data,
            workspace_info=workspace
        )
        
        # Create drive info from the actual Google Drive results
        drive_info = {
            'folder_id': drive_results['folder']['webViewLink'],
            'job_preferences_id': drive_results['documents'].get('job_preferences', {}).get('webViewLink', ''),
            'work_experience_id': drive_results['documents'].get('work_experience', {}).get('webViewLink', ''),
            'writing_samples_id': drive_results['documents'].get('writing_samples', {}).get('webViewLink', ''),
            'testimonials_id': drive_results['documents'].get('testimonials', {}).get('webViewLink', ''),
            'value_prop_id': drive_results['documents'].get('about_me', {}).get('webViewLink', '')
        }
        
        # Enhanced candidate info for referral_buddy_candidate_info table
        enhanced_candidate_info = {
            'name': candidate_name,
            'linkedin_url': linkedin_url,
            'email': candidate_email,
            'target_job_titles': target_job_titles,
            # Add education and location
            'education_school_names': education_schools,
            'metropolitan_area': metropolitan_area,
            # Default settings
            'pause_job_scrapes': False,
            'resume_auto_send': False,
            'gmail_oauth': False
        }
        
        # Store candidate info in referral_buddy_candidate_info table
        progress.update(task, description="[cyan]Storing candidate info record...")
        candidate_record = supabase_adapter.store_candidate_info(
            candidate_info=enhanced_candidate_info,
            workspace_info=workspace,
            drive_info=drive_info
        )
        
        progress.update(task, completed=True, description="[green]✓ Metadata stored in Supabase")
    
    # Output information about stored data
    if 'campaign_id' in db_metadata:
        console.print(f"[green]✓ Campaign ID in Supabase:[/] {db_metadata['campaign_id']}")
    
    if 'id' in candidate_record:
        console.print(f"[green]✓ Candidate Info record ID in Supabase:[/] {candidate_record['id']}")
    
    # Combine metadata
    result = {
        'file': filename,
        'file_metadata': file_metadata,
        'db_metadata': db_metadata,
        'candidate_record': candidate_record
    }
    
    return result

def run_onboarding(linkedin_url: str, email: str, target_job_titles: str) -> Dict[str, Any]:
    """
    Run the complete onboarding flow
    
    Args:
        linkedin_url: LinkedIn profile URL
        email: Candidate's email address
        target_job_titles: Comma-separated list of target job titles
        
    Returns:
        Dictionary with onboarding results
    """
    # Parse LinkedIn URL
    linkedin_url = parse_linkedin_url(linkedin_url)
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold green]ReferralBuddy Onboarding[/]\n\n"
        f"Starting onboarding process for LinkedIn profile:\n"
        f"[blue]{linkedin_url}[/]\n"
        f"Email: [blue]{email}[/]\n"
        f"Target Job Titles: [blue]{target_job_titles}[/]",
        border_style="green"
    ))
    
    # Run each step of the onboarding flow
    try:
        # Extract profile data
        profile_data = extract_profile_data(linkedin_url)
        
        # Enrich profile data
        enriched_data = enrich_profile_data(profile_data)
        
        # Add email and target job titles to profile data
        if 'personalInfo' not in enriched_data:
            enriched_data['personalInfo'] = {}
            
        enriched_data['personalInfo']['email'] = email
        enriched_data['personalInfo']['targetJobTitles'] = target_job_titles
        
        # Set up Google Drive documents
        drive_results = setup_google_drive(profile_data, enriched_data)
        
        # Set up Notion workspace
        workspace = setup_notion_workspace(profile_data, enriched_data)
        
        # Populate initial data in the workspace
        initial_data = populate_initial_data(workspace, profile_data, enriched_data)
        
        # Save metadata
        metadata_result = save_metadata(profile_data, enriched_data, workspace, drive_results)
        
        # Display completion message
        name = profile_data.get('name', enriched_data.get('personalInfo', {}).get('name', 'Candidate'))
        
        supabase_id = metadata_result.get('db_metadata', {}).get('campaign_id', 'N/A')
        candidate_record_id = metadata_result.get('candidate_record', {}).get('id', 'N/A')
        
        console.print(Panel.fit(
            f"[bold green]Onboarding Complete for {name}![/]\n\n"
            f"[blue]Notion Campaign:[/] {workspace['campaign_page'].get('url', 'N/A')}\n"
            f"[blue]Metadata File:[/] {metadata_result['file']}\n"
            f"[blue]Supabase Campaign ID:[/] {supabase_id}\n"
            f"[blue]Supabase Candidate Record ID:[/] {candidate_record_id}",
            title="Success",
            border_style="green"
        ))
        
        return {
            'profile_data': profile_data,
            'enriched_data': enriched_data,
            'workspace': workspace,
            'initial_data': initial_data,
            'drive_results': drive_results,
            'metadata_result': metadata_result
        }
        
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Error during onboarding:[/]\n\n{str(e)}",
            title="Error",
            border_style="red"
        ))
        
        # Print stack trace for debugging
        import traceback
        console.print(traceback.format_exc())
        
        raise e

def main():
    """Main entry point for the script"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='ReferralBuddy Onboarding Flow')
    parser.add_argument('linkedin_url', help='LinkedIn profile URL for the candidate')
    parser.add_argument('--email', required=True, help='Email address of the candidate')
    parser.add_argument('--target-job-titles', required=True, help='Comma-separated list of target job titles')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of real APIs')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set mock mode if requested
    if args.mock:
        os.environ['MOCK_API_RESPONSES'] = 'true'
    
    # Run onboarding
    run_onboarding(args.linkedin_url, args.email, args.target_job_titles)

if __name__ == '__main__':
    main() 