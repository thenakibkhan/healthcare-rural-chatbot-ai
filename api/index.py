import sys
import os

# Add both the project root and the backend folder to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
backend_dir = os.path.join(project_root, 'backend')

sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

from backend.app import app

# This is the entry point for Vercel
# Vercel looks for a variable named 'app' in api/index.py

if __name__ == "__main__":
    app.run()
