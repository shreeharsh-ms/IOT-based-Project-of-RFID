import sys
import os

# Ensure backend/app is importable
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app import create_app

app = create_app()  # <-- Vercel looks for THIS
