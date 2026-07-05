"""Gestion des guides de décomposition."""

from pathlib import Path
from core.config import GUIDES_DIR


def list_guides() -> list[dict]:
    """Liste les guides disponibles dans le dossier guides/."""
    guides_dir = Path(__file__).parent.parent / GUIDES_DIR
    if not guides_dir.exists():
        return []

    guides = []
    for f in sorted(guides_dir.glob("*.md")):
        title = _extract_title(f)
        guides.append({
            "name": f.stem,
            "title": title or f.stem,
            "path": str(f)
        })
    return guides


def read_guide(path: str) -> str:
    """Lit le contenu d'un guide."""
    return Path(path).read_text(encoding="utf-8")


def _extract_title(path: Path) -> str | None:
    """Extrait le titre depuis le premier # du fichier."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                return stripped[2:].strip()
    except Exception:
        pass
    return None
