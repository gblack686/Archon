#!/usr/bin/env python3
"""
Script to run the Job Management API server.
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Check if the port is already in use
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting Job Management API server on port {port}...")
    print("API documentation will be available at http://localhost:{port}/docs")
    print("Press Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run("endpoints.main:app", host="0.0.0.0", port=port, reload=True) 