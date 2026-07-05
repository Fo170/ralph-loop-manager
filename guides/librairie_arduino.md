# Arduino — Création d'une librairie

## Étapes de décomposition

1. **T1 — Définir l'interface publique (header)**
   - Créer le fichier `.h` avec la classe
   - Déclarer les méthodes publiques et privées
   - Définir les constantes et typedefs

2. **T2 — Implémenter le constructeur et la configuration**
   - Définir le constructeur avec paramètres
   - Implémenter `begin()` ou `init()`
   - Gérer l'allocation mémoire si nécessaire

3. **T3 — Implémenter les méthodes principales**
   - Lecture des capteurs / entrées
   - Traitement des données
   - Gestion des erreurs

4. **T4 — Implémenter les méthodes de sortie**
   - Affichage, communication, ou contrôle
   - Gestion des états et des flags

5. **T5 — Exemple d'utilisation et documentation**
   - Créer un fichier `examples/` de démo
   - Ajouter `keywords.txt`
   - Documenter l'API dans le header

## Format de sortie

```
<file name="MaLibrairie.h">...</file>
<file name="examples/demo/demo.ino">...</file>
```

## Consignes

- Chaque tâche peut produire plusieurs fichiers (`.h`)
- la librairie est toujours un fichier (`.h`) unique pas de fichier (`.cpp`) associer 
- Utiliser les balises `<file name="...">` pour chaque fichier
- Respecter le format Arduino library spec
