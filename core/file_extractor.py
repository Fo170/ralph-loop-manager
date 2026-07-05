"""Extraction de fichiers depuis les réponses LLM."""

import re
from pathlib import Path


def clean_code_content(content: str) -> str:
    """Nettoie le contenu du code : supprime fences Markdown et lignes vides parasites."""
    lines = content.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()
        # Supprimer les fences Markdown (```cpp, ```ino, ```c++, ```, etc.)
        if stripped.startswith("```"):
            continue
        # Supprimer les lignes vides au début
        if not cleaned and not stripped:
            continue
        cleaned.append(line)

    # Supprimer les lignes vides à la fin
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return "\n".join(cleaned)


def extract_files(response_text: str, dest_dir: Path, fallback_prefix: str = "") -> list[str]:
    """Extrait les fichiers et retourne la liste des chemins relatifs créés.
    
    fallback_prefix : préfixe ajouté aux noms de fichiers des méthodes 2/3/4
                      (utile pour éviter les collisions entre tâches).
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    files_created = []

    # 1. Balises XML <file name="...">
    xml_pattern = r'<file\s+name="([^"]+)">\s*(.*?)\s*</file>'
    for filename, content in re.findall(xml_pattern, response_text, re.DOTALL | re.IGNORECASE):
        filepath = dest_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        cleaned = clean_code_content(content)
        filepath.write_text(cleaned, encoding="utf-8")
        files_created.append(str(filepath))

    # 2. Markdown ```ino / ```cpp / ```c++ / ```arduino
    if not files_created:
        md_pattern = r'```(?:ino|cpp|c\+\+|arduino)\s*\n?(.*?)\n?```'
        md_matches = re.findall(md_pattern, response_text, re.DOTALL | re.IGNORECASE)
        for i, content in enumerate(md_matches):
            filename = f"{fallback_prefix}sketch.ino" if i == 0 else f"{fallback_prefix}sketch_{i+1}.ino"
            filepath = dest_dir / filename
            cleaned = clean_code_content(content)
            filepath.write_text(cleaned, encoding="utf-8")
            files_created.append(str(filepath))

    # 3. Markdown générique ``` (sans langage spécifié) contenant du code Arduino
    if not files_created:
        generic_md_pattern = r'```\s*\n?(.*?)\n?```'
        for i, content in enumerate(re.findall(generic_md_pattern, response_text, re.DOTALL)):
            if "void setup()" in content and "void loop()" in content:
                filename = f"{fallback_prefix}sketch.ino" if i == 0 else f"{fallback_prefix}sketch_{i+1}.ino"
                filepath = dest_dir / filename
                cleaned = clean_code_content(content)
                filepath.write_text(cleaned, encoding="utf-8")
                files_created.append(str(filepath))
                break  # Un seul bloc générique suffit

    # 4. Heuristique Arduino (setup + loop sans balises)
    if not files_created:
        if "void setup()" in response_text and "void loop()" in response_text:
            lines = response_text.split("\n")
            code_lines = []
            in_code = False
            for i, line in enumerate(lines):
                if any(m in line for m in ["#include", "const ", "void setup()", "#define", "int ", "float ", "#ifdef"]):
                    in_code = True
                if in_code:
                    if not line.strip() and len(code_lines) > 5:
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not any(c in next_line for c in ["void ", "int ", "{", "}", ";", "(", ")", "#", "/"]):
                                break
                    code_lines.append(line)

            if code_lines:
                content = "\n".join(code_lines)
                cleaned = clean_code_content(content)
                filepath = dest_dir / f"{fallback_prefix}sketch.ino"
                filepath.write_text(cleaned, encoding="utf-8")
                files_created.append(str(filepath))

    # Debug si échec
    if not files_created:
        debug_path = dest_dir.parent.parent / ".ralph" / "debug_response.txt"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(response_text, encoding="utf-8")

    return files_created
