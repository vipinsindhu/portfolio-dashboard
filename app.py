"""
Portfolio Dashboard - Main Application
Entry point for Azure App Service deployment
"""

import sys
import os

# Add backend directory to Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.api import create_app

# Create Flask app instance for Azure App Service
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
