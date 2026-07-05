# Arduino — Projet standard

## Étapes de décomposition

### T1 — Analyser la demande
- Extraire du prompt et lister les points essentiels de la demande
- Déterminer les variables globales et fonctions nécessaires
- Lister le matériel et périphériques (type de processeur, capteurs, entrées/sorties, protocoles I2C/SPI/Serial, etc.)
- Définir l'organisation générale du code : grandes fonctions, leur rôle et leur ordre d'appel dans `loop()`
- **Production** : fichier `.ino` avec l'analyse en commentaires + `#include`, déclarations globales, `setup()` et `loop()` squelette

### T2 — Configuration broches et constantes
- Définir les broches d'entrée/sortie avec des `const int` explicites
- Définir les constantes `const float` explicites
- Déclarer les constantes (seuils, calibration, adresses I2C)
- Initialiser la communication série (`Serial.begin()`) et les périphériques dans `setup()`
- **Production** : fonction(s) préfixée(s) `t2_*()` appelées depuis le `setup()` de T1

### T3 — Lecture des entrées / capteurs
- Lire les valeurs analogiques (`analogRead`) ou numériques (`digitalRead`)
- Convertir en unités physiques (tension, distance, température, etc.)
- Retourner les valeurs lues via paramètres par pointeur ou retour de fonction ou variable globale déclarer en début de programme
- **Production** : fonction(s) préfixée(s) `t3_*()` (ex: `void t3_lire_capteurs(float* tension)`)

### T4 — Logique métier et traitement
- Traiter les données lues par T3
- Appliquer les seuils et conditions (alarme si tension > 4.5V, etc.)
- Calculer les sorties
- **Production** : fonction(s) préfixée(s) `t4_*()` (ex: `bool t4_verifier_seuil(float valeur)`)

### T5 — Affichage et sorties
- Afficher les résultats sur Serial, LCD, LED, page web, etc.
- Activer les actionneurs (relais, moteurs, etc.)
- **Production** : fonction(s) préfixée(s) `t5_*()` (ex: `void t5_afficher(float valeur, bool alerte)`)

### T6 — Vérification Code
- Créer un fichier de test autonome `t6_verification.ino` avec son propre `setup()` et `loop()`
- Ce fichier appelle les fonctions de T2→T5 pour vérifier leur bon fonctionnement
- Affiche les résultats des tests sur Serial (OK/FAIL)
- Ne sera PAS inclus dans le fichier final — c'est un fichier de test indépendant

### T7 — Finalisation et documentation
- Ajuster les commentaires si nécessaire
- Ne produit PAS de nouveau code

---

## Consignes — construction incrémentale

### Rôle de chaque tâche

| Tâche | Contenu du fichier produit | setup/loop ? |
|-------|---------------------------|-------------|
| **T1** | Analyse en commentaires + `#include`, déclarations globales, `setup()` et `loop()` squelette appelant les fonctions T2→T5 | OUI |
| **T2** | Fonctions préfixées `t2_*()` pour la configuration | NON |
| **T3** | Fonctions préfixées `t3_*()` pour la lecture capteurs | NON |
| **T4** | Fonctions préfixées `t4_*()` pour la logique métier | NON |
| **T5** | Fonctions préfixées `t5_*()` pour l'affichage | NON |
| **T6** | Fichier de test autonome avec `setup()` et `loop()` qui vérifie les fonctions T2→T5 | OUI (test) |
| **T7** | Aucun code (documentation en français uniquement) | NON |

### Règles générales

1. **T1 — squelette** : produit les `#include`, les déclarations globales/variables partagées, `setup()` et `loop()`. Le `loop()` contient uniquement des appels aux fonctions des étapes suivantes :
   ```cpp
   void setup() {
     t2_init();
     Serial.begin(9600);
   }

   void loop() {
     float valeur;
     t3_lire_capteurs(&valeur);
     bool alerte = t4_verifier_seuil(valeur);
     t5_afficher(valeur, alerte);
     delay(100);
   }
   ```

2. **T2 à T5 — fonctions uniquement** : produisent UNIQUEMENT des fonctions avec le préfixe de leur tâche. PAS de `setup()` ni `loop()`. PAS de `#include "..."` pointant vers d'autres fichiers du projet.
   ```cpp
   // Exemple T3
   void t3_lire_capteurs(float* tension) {
     int raw = analogRead(A0);
     *tension = raw * (5.0 / 1023.0);
   }
   ```

3. **Variables partagées** : les variables qui doivent être accessibles par plusieurs tâches (ex: broches, seuils) sont déclarées en globales dans T1. Les tâches T2→T5 les utilisent directement (elles sont dans le même espace de noms après fusion).

4. **Dépendances** : chaque tâche T3+ doit lire les fichiers des tâches précédentes (fournis dans "FICHIERS EXISTANTS") pour connaître les signatures de fonctions et variables déjà définies. Ne PAS redéclarer ce qui existe déjà.

5. **Signatures cohérentes** : les appels dans `loop()` (T1) doivent correspondre exactement aux signatures des fonctions produites par T2→T5. Si T1 appelle `t3_lire_capteurs(&valeur)`, alors T3 doit définir `void t3_lire_capteurs(float*)`.

6. **T6 (test)** : produit un fichier de test complet avec son propre `setup()` et `loop()`. Il appelle les fonctions T2→T5 et affiche les résultats sur Serial. Ne sera PAS fusionné dans le fichier final.

7. **T7** : ne produit AUCUN code. Uniquement des commentaires de documentation en français.

