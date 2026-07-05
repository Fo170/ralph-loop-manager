# Ralph Loop Manager

Application desktop Python (PyQt6) qui orchestre un système de développement autonome par IA via LM Studio. Une demande texte → un projet fonctionnel avec code source, documentation et historique complet.

---

## 🎯 Objectif

Collez une demande, cliquez sur **🚀 Lancer Ralph**, et obtenez un projet complet :

1. **Décomposition** automatique en micro-tâches
2. **Génération** du code source par itérations (session fraîche à chaque tour)
3. **Extraction** automatique des fichiers depuis les réponses LLM
4. **Sauvegarde** snapshots horodatés
5. **Documentation** README.md généré automatiquement

---

## 🏗️ Architecture (minimaliste)

```
ralph-loop-manager/
├── main.py                      # Point d'entrée GUI
├── core/
│   ├── __init__.py
│   ├── config.py                # Configuration (URL LM Studio, modèle, chemins, timeout)
│   ├── diagnostic.py            # Diagnostic automatique au lancement
│   ├── lmstudio_client.py       # Client API LM Studio
│   ├── ticket_manager.py        # Création dossier projet horodaté
│   ├── task_decomposer.py       # Décomposition demande → tasks.json
│   ├── file_extractor.py        # Extraction fichiers depuis réponses LLM
│   ├── ralph_loop.py            # Moteur boucle Ralph complet
│   └── guides_manager.py        # Gestion des guides de décomposition
├── gui/
│   ├── __init__.py
│   └── main_window.py           # Interface unique (saisie + logs + progression + sélecteur guide)
├── guides/                      # Guides de décomposition (.md) ajoutés par l'utilisateur
│   ├── arduino.md               # Guide Arduino standard
│   ├── librairie_arduino.md     # Création de librairie Arduino
│   └── classe_python.md         # Création d'une classe Python
├── templates/
│   └── task_prompt.md           # Template de prompt pour chaque micro-tâche
├── projects/                    # Projets générés (créé automatiquement)
│   └── T-YYYYMMDD-HHMMSS-slug/
│       ├── README.md            # Documentation du projet
│       ├── tasks.json           # Graphe de tâches
│       ├── src/                 # Code source généré
│       │   └── *.ino            # Fichiers Arduino (ou autre langage)
│       ├── docs/                # Documentation technique
│       └── .ralph/
│           ├── snapshots/       # Snapshots horodatés
│           │   └── YYYYMMDD-HHMMSS/
│           │       ├── src/
│       │       ├── meta.json
│       │       └── ...
│           ├── guide.md         # Guide de décomposition utilisé (copie)
│           └── debug_response.txt  # Debug si extraction échoue
├── requirements.txt
└── README.md                    # Ce fichier
```

---

## 🔄 Flux de fonctionnement

### 1. Saisie de la demande
Collez votre demande dans la zone de texte, ex :
> *"Crée un voltmètre Arduino sur l'entrée A0 avec affichage LCD I2C et alarme si tension > 4.5V"*

### 2. Décomposition en micro-tâches
Le LLM génère un `tasks.json` avec 3 à 7 tâches ordonnées :
```json
{
  "tasks": [
    {
      "id": "T1",
      "title": "Setup structure et constantes",
      "description": "Définir les broches, constantes et setup de base",
      "priority_score": 10,
      "dependencies": [],
      "status": "pending"
    },
    {
      "id": "T2",
      "title": "Lecture ADC et conversion tension",
      "description": "Lire la valeur brute ADC et convertir en volts",
      "priority_score": 9,
      "dependencies": ["T1"],
      "status": "pending"
    }
  ]
}
```

### 3. Boucle Ralph — Itération par itération

```
🔄 Itération #1 — T1 : Analyser la demande + squelette setup/loop
   → Appel LLM (session fraîche)
   → Extraction fichier : t1_analyser_la_demande.ino (setup/loop + appels à t2_* t3_*)
   → Snapshot horodaté

🔄 Itération #2 — T2 : Configuration broches
   → Appel LLM avec contexte des fichiers précédents
   → Extraction fichier : t2_configuration.ino (fonctions t2_* uniquement)

🔄 Itération #3 — T3 : Lecture capteurs
   → Extraction fichier : t3_lecture.ino (fonctions t3_* uniquement)

...

🔄 Itération #6 — T6 : Test de vérification
   → Fichier de test autonome avec setup/loop (exclu de la fusion finale)

🔄 Itération #7 — T7 : Documentation
   → Commentaires uniquement

🔨 Consolidation → sketch_final.ino (fusion T1 à T5 uniquement)
🏁 Terminé !
```

**Principe clé :** Chaque itération utilise une **session fraîche**. Le LLM ne garde aucune mémoire entre les tâches. Tout le contexte passe par les fichiers (`tasks.json`, fichiers `src/` existants).  
**Construction incrémentale :** T1 produit le squelette (`setup()`/`loop()`) avec appels aux fonctions des étapes suivantes. T2→T5 produisent uniquement des fonctions préfixées (`t2_*`, `t3_*`). T6 produit un fichier de test autonome. T7 produit la documentation. La consolidation finale fusionne T1→T5 en un `sketch_final.ino` complet.

### 4. Extraction automatique des fichiers

Le système tente 3 méthodes d'extraction (dans l'ordre) :

| Méthode | Format attendu | Exemple |
|---------|---------------|---------|
| **1. Balises XML** | `<file name="nom.ino">...</file>` | Recommandé — le plus fiable |
| **2. Markdown** | ` ```ino ` ou ` ```cpp ` | Fallback si le LLM oublie les balises |
| **3. Heuristique** | Détection `void setup()` + `void loop()` | Dernier recours |

Si aucune méthode ne fonctionne, la réponse brute est sauvegardée dans `.ralph/debug_response.txt` pour analyse.

### 5. Sauvegarde par snapshots

| Type | Quand | Où |
|------|-------|-----|
| **Snapshot** | Après chaque itération | `.ralph/snapshots/YYYYMMDD-HHMMSS/` |

### 6. README final

Un `README.md` est généré automatiquement avec :
- La demande originale
- La liste des tâches et leur statut
- La structure du projet
- Instructions d'utilisation

---

## 📂 Guides de décomposition

Les guides permettent de **cadrer le LLM** sur la façon de morceler le travail selon le type de projet.

### Utilisation

1. Déposez un fichier `.md` dans `guides/` (ou utilisez les guides inclus)
2. Au lancement de l'application, le menu déroulant liste tous les guides disponibles
3. Sélectionnez celui qui correspond à votre projet, ou laissez `-- Aucun (LLM libre) --`
4. Ralph utilise le guide pour décomposer la demande et pour chaque tâche générée

### Créer vos propres guides

Créez un fichier `.md` dans `guides/` avec le format suivant :

```markdown
# Titre du guide

## Étapes

1. **T1 — Nom de l'étape**
   - Description de ce que fait cette étape

2. **T2 — Étape suivante**
   - ...

## Consignes
- Règles spécifiques que le LLM doit suivre
```

Tout fichier `.md` déposé dans `guides/` est automatiquement détecté au prochain démarrage.

### Guides inclus

| Guide | Description |
|-------|-------------|
| `arduino.md` | Projet Arduino standard (analyse → configuration → capteurs → logique → affichage → test → documentation) |
| `librairie_arduino.md` | Création d'une librairie Arduino (header, implémentation, exemple) |
| `classe_python.md` | Création d'une classe Python (structure, propriétés, méthodes, tests) |

---

## 🚀 Démarrage rapide

### Prérequis
- Python 3.8+
- LM Studio lancé avec le serveur API sur `localhost:1234`
- Un modèle code chargé (Qwen2.5-Coder, DeepSeek-Coder, etc.)

### Installation

```bash
# 1. Cloner
git clone https://github.com/Fo170/ralph-loop-manager.git
cd ralph-loop-manager

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer LM Studio
#    - Ouvrir LM Studio
#    - Onglet "Developer" → "Start Server" (port 1234)
#    - Charger un modèle code

# 4. Lancer Ralph
python main.py
```

### Utilisation

1. **Coller** votre demande dans la zone de texte
2. **Sélectionner** un guide de décomposition (ou laisser `-- Aucun --`)
3. **Cliquer** sur 🚀 **Lancer Ralph**
4. **Suivre** l'avancement en temps réel :
   - **Barre de progression** globale (tâches terminées / total)
   - **Tableau des tâches** avec statut (⏳ attente / 🔄 en cours / ✅ terminé / ❌ échec)
   - **Console** avec logs détaillés par étape
5. **Consulter** le projet dans `projects/T-.../`

### Lancement rapide Windows

Double-cliquez sur `ralph_loop_manager.bat` à la racine du projet.

---

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| GUI | PyQt6 (tableau de bord, logs temps réel) |
| API LLM | `requests` → API OpenAI-compatible LM Studio |
| Extraction fichiers | Regex (XML + Markdown + heuristique) |
| Snapshots | `shutil.copytree` + horodatage |
| Suivi tâches | Callbacks → tableau statuts colorés |
| Config | Python natif (`core/config.py`) |

---

## 📁 Structure d'un projet généré

```
projects/T-20260517-005816-essai-pour-creer/
├── README.md
├── tasks.json
├── src/
│   ├── sketch_final.ino
│   └── _intermediate/
│       └── t1_programme_arduino_co.ino
├── docs/
└── .ralph/
    ├── guide.md
    ├── snapshots/
    │   ├── 20260517-005816/
    │   │   ├── src/
    │   │   │   └── t1_programme_arduino_co.ino
    │   │   └── meta.json
    │   └── 20260517-005912/
    │       ├── src/
    │       │   └── t1_programme_arduino_co.ino
    │       └── meta.json
    └── debug_response.txt
```

---

## ⚙️ Configuration

Modifiez `core/config.py` pour adapter à votre environnement :

```python
LM_STUDIO_URL = "http://localhost:1234/v1"  # URL du serveur LM Studio
DEFAULT_MODEL = "qwen/qwen2.5-coder-14b"     # Modèle par défaut
PROJECTS_DIR = Path("projects")               # Dossier des projets générés
GUIDES_DIR = Path("guides")                   # Dossier des guides de décomposition
MAX_TASKS = 7                                 # Nombre max de micro-tâches
TEMPERATURE = 0.2                             # Température LLM (0 = déterministe)
MAX_TOKENS = 4096                             # Tokens max par réponse
REQUEST_TIMEOUT = 600                         # Timeout (s) par appel LLM
```

**`REQUEST_TIMEOUT`** : à ajuster selon le modèle et la machine. Un petit modèle rapide peut utiliser 60 s, un gros modèle sur machine modeste peut nécessiter 600 s ou plus.

---

## 🔍 Diagnostic automatique

Au lancement, `python main.py` exécute automatiquement un diagnostic qui vérifie :

- **Version Python** ≥ 3.8
- **Modules pip** : PyQt6, requests
- **Fichiers projet** : core/*.py, gui/*.py, templates/*.md
- **Connexion LM Studio** : serveur accessible sur `localhost:1234`
- **Modèle chargé** : au moins un modèle disponible

Si un problème est détecté, la console affiche clairement ce qui manque et comment le corriger.  
Tu peux aussi lancer le diagnostic seul : `python -m core.diagnostic`

---

## ⚠️ Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| `Aucun fichier détecté` | Le LLM n'a pas respecté le format | Vérifiez `.ralph/debug_response.txt` et ajustez le prompt dans `templates/task_prompt.md` |
| `ModuleNotFoundError` | Fichier manquant ou mauvais imports | Vérifiez que tous les fichiers `core/*.py` sont présents |
| `Read timed out` | Le modèle met plus de 300 s à répondre | Augmentez `REQUEST_TIMEOUT` dans `core/config.py` |
| LM Studio ne répond pas | Serveur non démarré | Vérifiez que LM Studio est ouvert et que le serveur est actif sur le port 1234 |
| Diagnostic affiche des erreurs | Prérequis manquants | Suivre les instructions affichées dans la console |

---

## 📝 Changelog

### v1.2.0 (2026-07-06)
- ✅ Construction incrémentale : T1 produit le squelette setup/loop, T2→T5 uniquement des fonctions préfixées
- ✅ Instructions conditionnelles par tâche dans `build_prompt()` (T1 setup/loop, T2→T5 fonctions, T6 test, T7 doc)
- ✅ Extraction JSON robuste avec `_extract_json()` dans `task_decomposer.py`
- ✅ Debug logs de la réponse brute LLM dans `.ralph/debug_decompose_*.txt`
- ✅ Contexte des fichiers précédents injecté dans le prompt de chaque tâche
- ✅ Consolidation améliorée : inclut la demande originale + liste des tâches
- ✅ Exclusion de T6/T7 de la consolidation finale (fichiers de test/doc)
- ✅ Guide Arduino réécrit : analyse → configuration → capteurs → logique → affichage → test → doc
- ✅ README.md généré : formatage corrigé, `{project_dir.name}` correctement substitué
- ✅ Diagnostic automatique au lancement (modules, fichiers, connexion LM Studio)

### v1.1.0 (2026-07-05)
- ✅ Guides de décomposition (.md dans `guides/`) — sélecteur dans l'interface
- ✅ Timeout configurable (`REQUEST_TIMEOUT` dans `config.py`)
- ✅ Affichage état connexion LM Studio (modèle chargé, statut)
- ✅ Barre de progression fonctionnelle
- ✅ Tableau de bord des tâches (statuts colorés en temps réel)
- ✅ Callback `tasks_callback` pour suivi détaillé des étapes
- ✅ Template `task_prompt.md` utilisé par `build_prompt()`
- ✅ `__init__.py` manquants ajoutés
- ✅ Correction bug `list.index()` dans l'extraction heuristique
- ✅ Correction chemin `debug_response.txt`
- ✅ Préfixe `fallback_prefix` pour éviter collisions fichiers intermédiaires
- ✅ Police emoji Windows (seguiemj.ttf)
- ✅ Fichier `ralph_loop_manager.bat` pour lancement Windows
- ✅ Code git supprimé (snapshots suffisent)

### v1.0.0 (2026-05-17)
- ✅ Interface GUI minimaliste (PyQt6)
- ✅ Décomposition automatique en micro-tâches
- ✅ Boucle Ralph avec session fraîche
- ✅ Extraction multi-méthodes (XML / Markdown / Heuristique)
- ✅ Snapshots horodatés + Git commits
- ✅ README.md auto-généré
- ✅ Gestion des erreurs et debug

---

## 📚 Références

- Vidéo sur la boucle Ralph : [YouTube](https://www.youtube.com/watch?v=2TLXsxkz0zI)
- Repo original pomodoro-workshop : [GitHub](https://github.com/chrismdp/pomodoro-workshop)

---

## 📝 License

GNU General Public License v3.0
