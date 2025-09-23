"""
Bilka Price Monitor - Streamlit Cloud App
Main entry point for Streamlit Cloud deployment
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the dashboard
from src.ui.dashboard import main

if __name__ == "__main__":
    main()