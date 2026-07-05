"""Création et gestion des dossiers projet horodatés."""

import re
from datetime import datetime
from pathlib import Path
from core.config import PROJECTS_DIR


def create_project(demande: str) -> Path:
    """Crée un dossier projet horodaté avec structure minimale."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    words = re.findall(r'\b\w{4,}\b', demande.lower())
    slug = "-".join(words[:3]) if words else "projet"
    safe_slug = re.sub(r'[^a-z0-9\-]', '', slug)[:30]
    
    project_dir = PROJECTS_DIR / f"T-{timestamp}-{safe_slug}"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Sous-dossiers
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "docs").mkdir(exist_ok=True)
    (project_dir / ".ralph" / "snapshots").mkdir(parents=True, exist_ok=True)
        
    return project_dir