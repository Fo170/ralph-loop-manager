"""Décomposition de la demande en micro-tâches via LLM."""

import json
import re
from pathlib import Path
from core.lmstudio_client import LMStudioClient


def _debug_log(project_dir: Path, label: str, content: str):
    """Écrit un fichier de debug dans .ralph/"""
    debug_dir = project_dir / ".ralph"
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / f"debug_{label}.txt").write_text(content, encoding="utf-8")


def _extract_json(text: str) -> dict | None:
    """Extraction robuste du JSON depuis une réponse LLM."""
    # 1. Nettoyer les fences markdown
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\n```\s*$', '', text)

    # 2. Chercher le premier { et le dernier } correspondant
    start = text.find('{')
    if start == -1:
        return None
    # Compter les accolades pour trouver la fermeture
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return None

    json_str = text[start:end]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def decompose(demande: str, project_dir: Path, client: LMStudioClient, guide_content: str = None) -> list:
    """Génère tasks.json et retourne la liste des tâches."""

    system = (
        "Tu es un architecte de projet spécialisé dans la décomposition de tâches. "
        "Tu réponds STRICTEMENT en JSON valide, sans markdown, sans texte autour. "
        "Le JSON doit commencer par { et finir par }."
    )

    guide_section = ""
    if guide_content:
        guide_section = f"""
## GUIDE DE RÉFÉRENCE (à suivre impérativement)
{guide_content}
"""

    prompt = f"""Décompose cette demande en 3 à 7 micro-tâches.
Chaque micro-tâche doit produire UNIQUEMENT une partie du code, PAS le programme complet.
La dernière tâche est la finalisation/fusion.

DEMANDE : {demande}
{guide_section}
EXEMPLE DE SORTIE (JSON strict, sans markdown) :
{{
  "tasks": [
    {{
      "id": "T1",
      "title": "Configuration broches et constantes",
      "description": "Définir les entrées/sorties, constantes, setup série",
      "priority_score": 10,
      "dependencies": [],
      "acceptance_criteria": ["Pin mapping défini", "Serial configuré"]
    }},
    {{
      "id": "T2",
      "title": "Lecture des capteurs",
      "description": "Lire les valeurs analogiques/numériques",
      "priority_score": 9,
      "dependencies": ["T1"],
      "acceptance_criteria": ["Valeurs lues correctement"]
    }}
  ]
}}

RÈGLES IMPORTANTES :
- Les tâches produisent CHACUNE un morceau de code partiel, PAS le programme complet
- Elles sont ordonnées logiquement avec dépendances
- T1 est toujours la tâche de configuration initiale
- priority_score : 10 (critique) à 5 (optionnel)
- Si un guide est fourni, suis-le impérativement
- RÉPONDS UNIQUEMENT en JSON valide, pas de texte autour
"""
    
    response = client.chat(prompt, system)
    _debug_log(project_dir, "decompose_raw", response)
    
    data = _extract_json(response)
    if data:
        tasks = data.get("tasks", [])
    else:
        _debug_log(project_dir, "decompose_failed", f"Réponse brute :\n{response}")
        tasks = [{
            "id": "T1",
            "title": "Programme Arduino complet",
            "description": demande,
            "priority_score": 10,
            "dependencies": [],
            "status": "pending",
            "acceptance_criteria": ["Code compilable"]
        }]
        
    for t in tasks:
        t["status"] = "pending"
        
    (project_dir / "tasks.json").write_text(
        json.dumps({"tasks": tasks}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    return tasks