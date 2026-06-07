"""
Portfolio Dashboard - Main Application
Entry point for Railway deployment
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import and create the Flask app
from backend.api import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
