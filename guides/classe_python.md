# Python — Création d'une classe

## Étapes de décomposition

1. **T1 — Définir la structure de la classe**
   - Déclarer la classe et le constructeur `__init__`
   - Définir les attributs avec types hints
   - Ajouter la docstring de classe

2. **T2 — Propriétés et validation**
   - Implémenter `@property` et setters
   - Ajouter la validation des données
   - Gérer les valeurs par défaut

3. **T3 — Méthodes métier**
   - Implémenter les méthodes principales
   - Ajouter les types hints et docstrings
   - Gérer les cas d'erreur (exceptions)

4. **T4 — Méthodes spéciales**
   - `__str__`, `__repr__`, `__eq__`
   - `__len__`, `__iter__` si applicable
   - Surcharge d'opérateurs si pertinent

5. **T5 — Tests et documentation**
   - Créer un fichier de test
   - Exemple d'utilisation
   - Documentation finale

## Format de sortie

```
<file name="ma_classe.py">...</file>
<file name="test_ma_classe.py">...</file>
```

## Consignes

- Chaque tâche produit un fichier `.py` fonctionnel
- Code avec typage (`typing` module)
- PEP 8 : conventions de nommage
