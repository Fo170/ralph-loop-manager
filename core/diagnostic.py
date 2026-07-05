"""Diagnostic automatique au lancement — vérifie les prérequis."""

import sys
import importlib
from pathlib import Path


def _check_python() -> list[str]:
    errs = []
    if sys.version_info < (3, 8):
        errs.append("Python 3.8 ou supérieur requis (version actuelle: {}.{})".format(
            sys.version_info.major, sys.version_info.minor))
    return errs


def _check_modules() -> list[str]:
    errs = []
    required = {
        "requests": "pip install requests",
        "PyQt6": "pip install PyQt6",
    }
    for mod, install_cmd in required.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            errs.append(f"Module manquant : {mod} → {install_cmd}")
    return errs


def _check_project_files() -> list[str]:
    errs = []
    root = Path(__file__).parent.parent

    required = [
        "main.py",
        "core/__init__.py",
        "core/config.py",
        "core/lmstudio_client.py",
        "core/ticket_manager.py",
        "core/task_decomposer.py",
        "core/file_extractor.py",
        "core/ralph_loop.py",
        "core/guides_manager.py",
        "gui/__init__.py",
        "gui/main_window.py",
        "templates/task_prompt.md",
    ]
    for path in required:
        if not (root / path).exists():
            errs.append(f"Fichier projet manquant : {path}")

    return errs


def _check_dirs() -> list[str]:
    errs = []
    root = Path(__file__).parent.parent
    dirs = ["projects", "guides", "templates"]
    for d in dirs:
        p = root / d
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errs.append(f"Impossible de créer le dossier {d} : {e}")
    return errs


def _check_lmstudio() -> list[str]:
    errs = []
    try:
        import requests as req
        from core.config import LM_STUDIO_URL
        resp = req.get(f"{LM_STUDIO_URL}/models", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", [])
            if not models:
                errs.append("Aucun modèle chargé dans LM Studio (ouvre LM Studio et charge un modèle)")
        else:
            errs.append(f"LM Studio répond avec le code {resp.status_code} sur {LM_STUDIO_URL}")
    except ImportError:
        errs.append("Module 'requests' manquant → impossible de vérifier LM Studio")
    except req.ConnectionError:
        errs.append("LM Studio non accessible sur localhost:1234 → vérifie que le serveur est lancé")
    except req.Timeout:
        errs.append("LM Studio ne répond pas (timeout) → vérifie que le serveur est bien démarré")
    except Exception as e:
        errs.append(f"Erreur connexion LM Studio : {e}")
    return errs


def run() -> list[str]:
    """Exécute tous les tests de diagnostic.

    Retourne la liste des erreurs (vide = tout va bien).
    """
    errors = []
    errors.extend(_check_python())
    errors.extend(_check_modules())
    errors.extend(_check_project_files())
    errors.extend(_check_dirs())
    errors.extend(_check_lmstudio())
    return errors


def show(errors: list[str]):
    """Affiche les erreurs dans la console."""
    if not errors:
        return

    sep = "=" * 58
    print()
    print(sep)
    print("  DIAGNOSTIC — Problèmes détectés")
    print(sep)
    for i, err in enumerate(errors, 1):
        print(f"  {i}. {err}")
    print(sep)
    print("  Corrige les problèmes ci-dessus puis relance le programme.")
    print(sep)
    print()


if __name__ == "__main__":
    errs = run()
    if errs:
        show(errs)
        sys.exit(1)
    else:
        print("✔ Diagnostic : tout est OK")
        sys.exit(0)
