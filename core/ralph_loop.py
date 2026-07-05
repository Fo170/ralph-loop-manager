"""Moteur principal de la boucle Ralph — Version avec séparation résultats intermédiaires / final."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from core.lmstudio_client import LMStudioClient
from core.ticket_manager import create_project
from core.task_decomposer import decompose
from core.file_extractor import extract_files
from core.guides_manager import read_guide


class RalphLoop:
    def __init__(self, model: str = None, log_callback=None, progress_callback=None, tasks_callback=None, guide_path: str = None):
        self.client = LMStudioClient(model) if model else LMStudioClient()
        self.log = log_callback or print
        self.progress = progress_callback
        self.tasks_callback = tasks_callback
        self.project_dir = None
        self._stop = False
        self.guide_path = guide_path
        self.guide_content = None

    def stop(self):
        self._stop = True

    def snapshot(self, label: str):
        """Snapshot horodaté du projet."""
        snap_dir = self.project_dir / ".ralph" / "snapshots" / datetime.now().strftime("%Y%m%d-%H%M%S")
        snap_dir.mkdir(parents=True, exist_ok=True)
        for item in ["src", "README.md"]:
            src = self.project_dir / item
            dst = snap_dir / item
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        (snap_dir / "meta.json").write_text(json.dumps({
            "label": label, "time": datetime.now().isoformat()
        }), encoding="utf-8")
        self.log(f"📸 Snapshot : {snap_dir.name}")

    def build_prompt(self, task: dict, demande: str, all_tasks: list) -> str:
        """Construit le prompt pour une tâche."""
        template_path = Path(__file__).parent.parent / "templates" / "task_prompt.md"
        if template_path.exists():
            template = template_path.read_text(encoding="utf-8")
        else:
            template = """## CONTEXTE
Tu es un développeur expert. Tu produis du code compilable et fonctionnel.

## TÂCHE
{{task_title}}
{{task_description}}

## FICHIERS EXISTANTS
{{existing_files}}
{{guide_section}}
## FORMAT DE SORTIE — OBLIGATOIRE
Encapsule le code COMPLET dans :

<file name="{{filename}}">
/*
 * {{task_title}}
 */

// Code ici

</file>

RÈGLES :
- AUCUN texte hors balises <file>
- Code complet et compilable"""

        done = [t for t in all_tasks if t["status"] == "done"]

        # Lister les fichiers des tâches précédentes (dans _intermediate/)
        intermediate_dir = self.project_dir / "src" / "_intermediate"
        intermediate_files = sorted(intermediate_dir.glob("*.ino")) if intermediate_dir.exists() else []
        # Lister aussi les fichiers dans src/ directement
        src_files = list((self.project_dir / "src").glob("*.ino")) if (self.project_dir / "src").exists() else []
        all_files = intermediate_files + src_files

        existing_lines = []
        for f in all_files:
            content = f.read_text(encoding="utf-8")
            # Tronquer si trop long (garder max 100 lignes par fichier)
            lines = content.split("\n")
            if len(lines) > 100:
                content = "\n".join(lines[:100]) + f"\n// ... ({len(lines) - 100} lignes supplémentaires)"
            existing_lines.append(f"### {f.name}\n```cpp\n{content}\n```")

        existing = "\n\n".join(existing_lines) if existing_lines else "Aucun fichier existant."

        guide_section = ""
        if self.guide_content:
            guide_section = f"\n## GUIDE DE RÉFÉRENCE\n{self.guide_content}\n"

        # Instruction selon le type de tâche
        tid = task["id"]
        if tid == "T1":
            task_instructions = (
                "## INSTRUCTION SPÉCIFIQUE — PREMIÈRE TÂCHE\n"
                "Tu es la TÂCHE N°1 (analyse + squelette).\n"
                "- Produis les `#include`, déclarations globales, `setup()` et `loop()`.\n"
                "- Dans `loop()`, prévois des APPELS aux fonctions des étapes suivantes, "
                "par exemple : `t2_lecture()`, `t3_traitement()`, `t4_affichage()`.\n"
                "- Utilise des noms de fonctions explicites avec le préfixe t2_, t3_, etc.\n"
            )
        elif tid == "T6":
            task_instructions = (
                "## INSTRUCTION SPÉCIFIQUE — TEST DE VÉRIFICATION\n"
                "Tu es la TÂCHE N°6 (test de vérification autonome).\n"
                "- Produis un fichier de test COMPLET avec son propre `setup()` et `loop()`.\n"
                "- Dans `setup()` : initialise la communication série.\n"
                "- Dans `loop()` : appelle les fonctions T2→T5 et affiche les résultats sur Serial "
                "(ex: `t3_lire_capteurs() OK`, `t4_verifier_seuil() = true`, ...).\n"
                "- Ne fais PAS de `#include \"...\"` d'autres fichiers.\n"
                "- Ce fichier est un TEST, il ne sera PAS fusionné dans le fichier final.\n"
            )
        elif tid == "T7":
            task_instructions = (
                "## INSTRUCTION SPÉCIFIQUE — FINALISATION\n"
                "Tu es la TÂCHE N°7 (finalisation et documentation).\n"
                "- Le code final est déjà complet et fonctionnel dans sketch_final.ino.\n"
                "- Ne produit PAS de nouveau code.\n"
                "- Si tu veux, ajoute un bloc de commentaires de documentation en français "
                "dans un fichier vide `t7_documentation.txt` (hors balises .ino).\n"
                "- Sinon, ne produis rien.\n"
            )
        else:
            task_instructions = (
                "## INSTRUCTION SPÉCIFIQUE — TÂCHE INTERMÉDIAIRE\n"
                f"Tu es la TÂCHE N°{tid} (étape partielle).\n"
                "- Tu N'ÉCRIS PAS `setup()` ni `loop()`.\n"
                f"- Écris UNIQUEMENT des fonctions nommées avec le préfixe `{tid.lower()}_` "
                f"(ex: `void {tid.lower()}_ma_fonction()`).\n"
                "- Ne fais PAS de `#include \"...\"` d'autres fichiers.\n"
                "- Ne répète PAS les déclarations globales déjà présentes dans T1.\n"
                "- N'écris PAS de commentaires superflus, privilégie le code.\n"
            )

        filename = f"{task['id'].lower()}_{task['title'].replace(' ', '_').lower()[:20]}.ino"

        return template \
            .replace("{{task_title}}", task["title"]) \
            .replace("{{task_description}}", task["description"]) \
            .replace("{{existing_files}}", existing) \
            .replace("{{guide_section}}", guide_section) \
            .replace("{{task_instructions}}", task_instructions) \
            .replace("{{filename}}", filename)

    def consolidate_final(self, demande: str, tasks: list):
        """Demande au LLM de consolider tous les fichiers intermédiaires en un projet final cohérent."""
        self.log("\n🔨 Consolidation du projet final...")

        # Lire les fichiers intermédiaires (exclure T6 et T7 : vérification + doc)
        intermediate_dir = self.project_dir / "src" / "_intermediate"
        all_intermediate = sorted(intermediate_dir.glob("*.ino")) if intermediate_dir.exists() else []
        intermediate_files = [
            f for f in all_intermediate
            if not f.name.startswith(("t6_", "t7_"))
        ]
        excluded = [f for f in all_intermediate if f.name.startswith(("t6_", "t7_"))]

        if len(intermediate_files) <= 1:
            self.log("ℹ️ Un seul fichier intermédiaire — pas de consolidation nécessaire")
            return

        if excluded:
            self.log(f"ℹ️ Fichiers exclus de la consolidation : {[f.name for f in excluded]}")

        # Construire le contexte avec la liste des tâches
        tasks_summary = "\n".join(
            f"- {t['id']} : {t['title']} — {t['description']}"
            for t in tasks
        )

        # Contexte avec les fichiers intermédiaires (sans T6/T7)
        context = "## FICHIERS INTERMÉDIAIRES À CONSOLIDER\n\n"
        for f in intermediate_files:
            context += f"### {f.name}\n"
            content = f.read_text(encoding='utf-8')
            context += f"```cpp\n{content}\n```\n\n"

        prompt = f"""## DEMANDE ORIGINALE
{demande}

## TÂCHES DÉCOMPOSÉES
{tasks_summary}

{context}

## CONSIGNE DE CONSOLIDATION
Tu dois créer UN SEUL fichier Arduino `sketch_final.ino` qui correspond EXACTEMENT à la demande originale.

Le projet a été décomposé en micro-tâches listées ci-dessus. Chaque fichier intermédiaire contient une partie du code.

RÈGLES STRICTES :
1. Le code final doit UNIQUEMENT faire ce qui est demandé dans la DEMANDE ORIGINALE — ignore les fonctionnalités non demandées
2. `setup()` et `loop()` ne doivent apparaître QU'UNE SEULE FOIS — fusionne le contenu de tous les `setup()` en un seul, idem pour `loop()`
3. Supprime les doublons et variables inutiles
4. Organise le code : d'abord les `#include`, puis les déclarations globales, puis `setup()`, puis `loop()`, puis les fonctions annexes
5. Le code doit être complet, compilable, et fonctionnel

## SORTIE — OBLIGATOIRE
<file name="sketch_final.ino">
// Code Arduino FINAL

</file>
AUCUN texte hors des balises.
"""
        try:
            response = self.client.chat(
                prompt,
                system="Tu es un développeur Arduino expert. Tu produis des programmes complets et fonctionnels. Tu suis la demande originale à la lettre. UNIQUEMENT du code encapsulé dans <file name=\"...\">...</file>."
            )
            files = extract_files(response, self.project_dir / "src")
            if files:
                self.log(f"✅ Projet final consolidé : {[Path(f).name for f in files]}")
            else:
                self.log("⚠️ Échec de la consolidation — fichiers intermédiaires conservés")
        except Exception as e:
            self.log(f"⚠️ Erreur consolidation : {e}")

    def generate_readme(self, demande: str, tasks: list, files: list):
        """Génère README.md final."""

        # Séparer fichiers intermédiaires et final
        intermediate_files = []
        final_files = []
        for f in files:
            p = Path(f)
            if "_intermediate" in str(p):
                intermediate_files.append(p)
            else:
                final_files.append(p)

        readme = f"""# {self.project_dir.name}

> {demande}

- **Date** : {datetime.now().strftime("%d/%m/%Y %H:%M")}
- **Modèle** : {self.client.model}
- **Tâches** : {sum(1 for t in tasks if t['status']=='done')}/{len(tasks)}

---

## 🚀 Utilisation (Résultat Final)

Le fichier à utiliser se trouve dans `src/` :

```
src/
"""

        # Lister d'abord les fichiers finaux
        src_dir = self.project_dir / "src"
        for f in sorted(src_dir.glob("*.ino")):
            readme += f"├── {f.name}          ← FICHIER FINAL\n"

        proj_name = self.project_dir.name
        readme += f"└── _intermediate/     ← Fichiers de travail (peuvent être ignorés)\n"
        readme += "```\n\n"
        readme += "### Arduino IDE\n"
        readme += "1. Ouvrir `src/sketch_final.ino` (ou le fichier `.ino` principal)\n"
        readme += "2. Sélectionner la carte **Arduino Uno**\n"
        readme += "3. Sélectionner le bon port COM\n"
        readme += "4. Téléverser\n\n"
        readme += "### PlatformIO (VS Code)\n"
        readme += "```bash\n"
        readme += f"cd {proj_name}/src\n"
        readme += "pio run --target upload\n"
        readme += "```\n\n"
        readme += "---\n\n"
        readme += f"## Structure complete du projet\n\n"
        readme += "```\n"
        readme += f"{proj_name}/\n"
        readme += "├── README.md              ← Ce fichier\n"
        readme += "├── tasks.json             ← Detail des taches\n"
        readme += "├── src/\n"
        readme += "│   ├── sketch_final.ino   ← RESULTAT FINAL\n"
        readme += "│   └── _intermediate/     ← Fichiers intermediaires par tache\n"

        # Lister les fichiers intermédiaires
        intermediate_dir = src_dir / "_intermediate"
        if intermediate_dir.exists():
            for f in sorted(intermediate_dir.glob("*.ino")):
                readme += f"│       ├── {f.name}\n"

        readme += "├── docs/                  ← Documentation technique\n"
        readme += "└── .ralph/\n"
        readme += "    └── snapshots/           ← Sauvegardes horodatees\n"
        readme += "```\n"
        readme += "\n---\n\n"
        readme += "## Detail des taches\n\n"
        readme += "| ID | Titre | Statut |\n"
        readme += "|---|---|---|\n"
        for t in tasks:
            icon = "✅" if t["status"] == "done" else "❌"
            readme += f"| {t['id']} | {t['title']} | {icon} |\n"

        readme += "\n---\n\n"
        readme += "## Fichiers intermediaires\n\n"
        readme += "Ces fichiers ont ete generes etape par etape lors de la boucle Ralph.\n"
        readme += "Ils sont conserves a titre de trace mais **ne sont pas necessaires** pour utiliser le projet.\n\n"
        if intermediate_files:
            for f in intermediate_files:
                readme += f"- `{f.name}` — Genere lors de l'iteration {f.stem[:2].upper()}\n"
        else:
            readme += "_Aucun fichier intermediaire (projet en une seule tache)_\n"

        readme += "\n---\n*Généré automatiquement par Ralph Loop Manager*"
        (self.project_dir / "README.md").write_text(readme, encoding="utf-8")

    def run(self, demande: str) -> Path:
        """Exécute la boucle Ralph complète."""
        # 1. Créer projet
        self.project_dir = create_project(demande)
        self.log(f"📁 Projet : {self.project_dir.name}")

        # 2. Décomposer
        self.guide_content = None
        if self.guide_path:
            try:
                self.guide_content = read_guide(self.guide_path)
                guide_name = Path(self.guide_path).stem
                self.log(f"📖 Guide chargé : {guide_name}")
            except Exception as e:
                self.log(f"⚠️ Impossible de charger le guide : {e}")

        self.log("🔨 Décomposition...")
        tasks = decompose(demande, self.project_dir, self.client, self.guide_content)
        self.log(f"✅ {len(tasks)} tâches")
        if self.tasks_callback:
            self.tasks_callback(tasks)

        # Sauvegarder le guide utilisé dans le projet
        if self.guide_content:
            guide_dst = self.project_dir / ".ralph" / "guide.md"
            guide_dst.parent.mkdir(parents=True, exist_ok=True)
            guide_dst.write_text(self.guide_content, encoding="utf-8")

        # 3. Boucle
        all_files = []
        total = len(tasks)
        done_count = 0

        # Créer le dossier pour les fichiers intermédiaires
        intermediate_dir = self.project_dir / "src" / "_intermediate"
        intermediate_dir.mkdir(parents=True, exist_ok=True)

        while not self._stop:
            # Tâches éligibles (dépendances satisfaites)
            eligible = [
                t for t in tasks
                if t["status"] == "pending"
                and all(next((tt for tt in tasks if tt["id"] == d), {}).get("status") == "done"
                        for d in t.get("dependencies", []))
            ]
            if not eligible:
                break

            task = max(eligible, key=lambda t: t.get("priority_score", 0))
            task["status"] = "running"
            self.log(f"\n🔄 {task['id']} : {task['title']}")

            # Appel LLM
            prompt = self.build_prompt(task, demande, tasks)
            try:
                response = self.client.chat(prompt, system='Tu es un développeur Arduino. UNIQUEMENT du code encapsulé dans <file name="...">...</file>. AUCUN texte hors balises.')

                # Extraire dans le dossier intermédiaire
                task_prefix = f"{task['id'].lower()}_"
                files = extract_files(response, intermediate_dir, fallback_prefix=task_prefix)
                all_files.extend(files)

                if files:
                    task["status"] = "done"
                    done_count += 1
                    if self.progress:
                        self.progress(int(done_count / total * 100))
                    self.log(f"✅ Fichier intermédiaire : {[Path(f).name for f in files]}")
                    self.snapshot(task["id"])
                else:
                    task["status"] = "failed"
                    task["error"] = "Aucun fichier extrait"
                    self.log("❌ Aucun fichier extrait")

            except Exception as e:
                task["status"] = "failed"
                task["error"] = str(e)
                self.log(f"❌ Erreur : {e}")

            if self.tasks_callback:
                self.tasks_callback(tasks)

            # Sauvegarder état
            (self.project_dir / "tasks.json").write_text(
                json.dumps({"tasks": tasks}, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

        # 4. Consolidation finale (si plusieurs tâches)
        if sum(1 for t in tasks if t["status"] == "done") > 1:
            self.consolidate_final(demande, tasks)
            # Ajouter les fichiers consolidés à all_files
            for f in (self.project_dir / "src").glob("sketch_final.ino"):
                all_files.append(str(f))
        elif intermediate_dir.exists() and any(intermediate_dir.glob("*.ino")):
            # Une seule tâche : copier le fichier intermédiaire comme final
            src_file = next(intermediate_dir.glob("*.ino"))
            dst_file = self.project_dir / "src" / "sketch_final.ino"
            shutil.copy2(src_file, dst_file)
            self.log(f"✅ Fichier final : {dst_file.name}")

        # 5. Finaliser
        self.generate_readme(demande, tasks, all_files)
        self.snapshot("FINAL")
        self.log(f"\n🏁 Terminé ! {self.project_dir}")
        return self.project_dir