# Test MVIC - Documentation

## Vue d'ensemble

Le test MVIC (MV Imaging Check) est un test hebdomadaire qui valide la qualité des images de radiation en vérifiant:

1. **Taille du champ**: Dimensions du champ de radiation à l'isocentre
2. **Forme du champ**: Rectangularité (angles à 90°)

## Spécifications

### Tailles acceptées
- **150x80 mm** - Champ rectangulaire standard
- **85x85 mm** - Champ carré moyen
- **50x50 mm** - Champ carré petit

### Tolérances
- **Taille**: ±1 mm pour largeur et hauteur
- **Angles**: ±1° par rapport à 90°

## Utilisation

### Via l'interface web
1. Naviguer vers "Tests Hebdomadaires"
2. Sélectionner "MVIC - MV Imaging Check"
3. Remplir le formulaire:
   - Date du test
   - Opérateur
   - Fichier DICOM
   - Taille attendue (optionnel)
   - Notes (optionnel)
4. Soumettre le formulaire

### Via ligne de commande

```powershell
cd backend/services/weekly/MVIC
python mvic_test.py "Nom Opérateur" "chemin/vers/image.dcm" "150x80"
```

### Via API

```bash
POST http://localhost:8000/basic-tests/mvic
Content-Type: multipart/form-data

{
  "operator": "Jean Dupont",
  "dicom_file": [fichier DICOM],
  "expected_size": "150x80",  # optionnel
  "test_date": "2025-11-21",
  "notes": "Test de routine"
}
```

## Résultats du test

### Données retournées

```json
{
  "test_name": "MVIC - MV Imaging Check",
  "operator": "Jean Dupont",
  "test_date": "2025-11-21T10:30:00",
  "overall_result": "PASS",
  "results": {
    "taille_detectee": {
      "value": "149.85 × 79.92",
      "status": "INFO",
      "unit": "mm"
    },
    "validation_taille": {
      "value": "150x80",
      "status": "PASS",
      "unit": "mm",
      "tolerance": "±1mm",
      "details": "Erreur: ±0.15mm (largeur), ±0.08mm (hauteur)"
    },
    "coins_detectes": {
      "value": 4,
      "status": "INFO",
      "details": "Nombre de coins du champ détectés"
    },
    "angles_coins": {
      "value": "89.85°, 90.12°, 89.95°, 90.08°",
      "status": "INFO",
      "unit": "°"
    },
    "validation_forme": {
      "value": "Tous les angles à 90°",
      "status": "PASS",
      "unit": "°",
      "tolerance": "±1°"
    },
    "visualisation": {
      "value": "field_shape_image.png",
      "status": "INFO",
      "details": "Fichier image de visualisation généré"
    }
  }
}
```

### Interprétation

- **PASS**: Le champ respecte les tolérances de taille ET de forme
- **FAIL**: Au moins un critère (taille ou forme) est hors tolérance
- **INFO**: Informations complémentaires sans impact sur le résultat

## Architecture technique

### Composants

1. **mvic_test.py**: Classe principale héritant de `BaseTest`
   - Orchestration du test
   - Formatage des résultats
   - Gestion des erreurs

2. **taille_champ.py**: Module `FieldSizeValidator`
   - Détection des contours du champ
   - Calcul des dimensions à l'isocentre
   - Validation contre les tailles attendues

3. **forme_champ.py**: Module `FieldShapeValidator`
   - Détection des coins avec Canny edge detection
   - Calcul des angles avec transformée de Hough
   - Validation de la rectangularité
   - Génération de visualisation (4 panneaux)

### Traitement d'image

Le test utilise une pipeline de traitement identique aux autres tests DICOM:

1. **Normalisation**: 0-1 range
2. **CLAHE**: Amélioration du contraste
3. **Laplacian sharpening**: Netteté des bords
4. **Canny edge detection**: Détection des contours (dérivée première)
5. **Hough line transform**: Détection des lignes droites

### Visualisation générée

Fichier `field_shape_{nom}.png` avec 4 panneaux:

1. **CLAHE Enhanced**: Image après amélioration du contraste
2. **Canny Edges**: Détection des bords (dérivée première)
3. **Detected Field**: Champ détecté avec coins annotés
   - Coins valides: marqueurs verts
   - Coins invalides: marqueurs rouges
   - Angles affichés pour chaque coin
4. **Summary**: Statistiques et résultats de validation

## Dépannage

### Erreur: "Impossible de détecter les dimensions du champ"
- Vérifier que le fichier DICOM contient bien une image MV
- Vérifier les métadonnées DICOM (SAD, SID, pixel spacing)
- Ajuster les paramètres de seuil si nécessaire

### Erreur: "Impossible de détecter les angles du champ"
- Le champ peut être trop irrégulier
- Vérifier la qualité de l'image DICOM
- Le nombre de coins détectés est insuffisant (<3)

### Validation échoue alors que visuellement correct
- Vérifier les tolérances configurées
- Comparer avec la visualisation générée
- Vérifier les valeurs exactes dans les résultats JSON

## Maintenance

### Ajuster les tolérances

Dans `mvic_test.py`, modifier les paramètres:

```python
self.size_validator.size_tolerance = 1.5  # ±1.5mm au lieu de ±1mm
self.shape_validator.angle_tolerance = 2.0  # ±2° au lieu de ±1°
```

### Ajouter une taille de champ

Dans `taille_champ.py`, ligne ~24:

```python
self.expected_sizes = [
    {'width': 150, 'height': 80, 'name': '150x80'},
    {'width': 85, 'height': 85, 'name': '85x85'},
    {'width': 50, 'height': 50, 'name': '50x50'},
    {'width': 100, 'height': 100, 'name': '100x100'},  # NOUVEAU
]
```

### Modifier les paramètres de détection

Dans les deux validateurs (`taille_champ.py` et `forme_champ.py`):

```python
self.tolerance_threshold = 127  # Seuil binarisation (50-150)
self.tolerance_kernel_size = 3  # Taille noyau morphologique (3-9)
self.min_area = 200  # Surface minimale contour (pixels)
self.merge_distance_px = 40  # Distance fusion contours (pixels)
```

## Tests unitaires

Pour tester l'intégration:

```powershell
cd backend
.\env\Scripts\python.exe test_mvic_integration.py
```

Tests effectués:
1. Import des modules
2. Instanciation de la classe
3. Récupération des données de formulaire
4. Enregistrement dans WEEKLY_TESTS
5. Import des validateurs

## Référence rapide

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| Tailles acceptées | 150x80, 85x85, 50x50 | En mm à l'isocentre |
| Tolérance taille | ±1 mm | Pour largeur ET hauteur |
| Angle requis | 90° | Pour tous les coins |
| Tolérance angle | ±1° | Pour chaque coin |
| Fichier requis | .dcm | Format DICOM uniquement |
| Fréquence | Hebdomadaire | Test de routine |
| Temps d'exécution | ~2-5 sec | Dépend de la taille de l'image |
| Output | PNG + JSON | Visualisation + données |
