# MVIC Fente Test

## Description

Test d'analyse des **bandes noires** (fentes) dans les images MV du UNITY. Ce test mesure automatiquement :

1. **Position des bandes noires** : Coordonnées (u, v) du centre de chaque bande
2. **Largeur entre bandes** : Distance entre les centres de deux bandes consécutives
3. **Hauteur de chaque bande** : Dimension verticale de chaque bande détectée

## Caractéristiques

- ✅ Supporte **1 ou plusieurs images DICOM**
- ✅ Chaque image est analysée indépendamment
- ✅ Détection automatique des bandes noires (régions sombres)
- ✅ Calculs en **pixels** et en **mm** (si pixel spacing disponible)
- ℹ️ **Pas de critères PASS/FAIL** - Test informatif uniquement

## Algorithme de détection

### 1. Normalisation de l'image
```
image_normalized = (image - min) / (max - min)
```

### 2. Seuillage
- Utilise le **20e percentile** comme seuil
- Les pixels en dessous du seuil sont considérés "noirs"

### 3. Segmentation
- Utilise `scipy.ndimage.label` pour identifier les composants connexes
- Filtre les petites régions (< 10 pixels de hauteur, < 5 pixels de largeur)

### 4. Mesures
Pour chaque bande détectée :
- **Centre (u, v)** = moyenne des coordonnées des pixels
- **Largeur** = `u_max - u_min + 1`
- **Hauteur** = `v_max - v_min + 1`
- **Distance entre bandes** = `sqrt((u2-u1)² + (v2-v1)²)`

## Utilisation

### Via le frontend

1. Sélectionner "MVIC Fente" dans la liste des tests
2. Remplir les champs :
   - Date du test
   - Opérateur
   - Uploader 1 ou plusieurs fichiers DICOM
   - Notes (optionnel)
3. Cliquer sur "Analyser"

### Via l'API

**Endpoint** : `POST /basic-tests/mvic_fente`

**Content-Type** : `multipart/form-data`

**Paramètres** :
```
operator: string (required)
test_date: string (YYYY-MM-DD, optional)
dicom_files: file[] (required, multiple DICOM files)
notes: string (optional)
```

**Exemple avec curl** :
```bash
curl -X POST http://localhost:8000/basic-tests/mvic_fente \
  -F "operator=Dr. Smith" \
  -F "test_date=2025-12-05" \
  -F "dicom_files=@image1.dcm" \
  -F "dicom_files=@image2.dcm" \
  -F "notes=Test mensuel"
```

### Via Python

```python
from services.weekly.MVIC_fente import MVICFenteTest

test = MVICFenteTest()
result = test.execute(
    files=['/path/to/image1.dcm', '/path/to/image2.dcm'],
    operator='Dr. Smith',
    notes='Test mensuel'
)

print(f"Résultat : {result['overall_result']}")
print(f"Bandes détectées : {result['total_bands_detected']}")
```

## Structure des résultats

```json
{
  "test_name": "MVIC Fente",
  "overall_result": "COMPLETE",
  "operator": "Dr. Smith",
  "test_date": "2025-12-05T10:30:00",
  "results": [
    {
      "name": "image_1_band_1_position",
      "value": "(512.5, 200.3)",
      "status": "INFO",
      "unit": "pixels"
    },
    {
      "name": "image_1_band_1_height",
      "value": 45,
      "status": "INFO",
      "unit": "pixels"
    },
    {
      "name": "image_1_distance_band_1_to_2",
      "value": 150.5,
      "status": "INFO",
      "unit": "pixels"
    }
  ],
  "detailed_results": [
    {
      "file": "image1.dcm",
      "num_bands": 3,
      "pixel_spacing_mm": 0.216,
      "bands": [
        {
          "center_u": 512.5,
          "center_v": 200.3,
          "width_pixels": 30,
          "height_pixels": 45,
          "width_mm": 6.48,
          "height_mm": 9.72,
          "bounds": {
            "u_min": 497,
            "u_max": 527,
            "v_min": 178,
            "v_max": 223
          }
        }
      ]
    }
  ],
  "total_images": 2,
  "total_bands_detected": 6
}
```

## Paramètres ajustables

Dans `mvic_fente.py`, classe `MVICFenteTest` :

```python
self.band_detection_percentile = 20  # Seuil de détection (percentile)
self.min_band_height = 10            # Hauteur minimale (pixels)
self.min_band_width = 5              # Largeur minimale (pixels)
```

## Cas d'usage

### Contrôle qualité mensuel
- Vérifier la stabilité des positions des fentes
- Mesurer l'évolution des dimensions dans le temps

### Validation après maintenance
- S'assurer que les fentes MLC n'ont pas bougé
- Comparer avec les mesures de référence

### Caractérisation du système
- Documenter les positions exactes des fentes
- Établir des valeurs de référence

## Limitations

- ❌ Pas de critères automatiques PASS/FAIL
- ⚠️ Sensible au contraste de l'image
- ⚠️ Peut détecter des artefacts comme des bandes
- ℹ️ L'utilisateur doit interpréter les résultats

## Améliorations futures

- [ ] Ajouter des tolérances configurables
- [ ] Générer des visualisations (overlay sur l'image)
- [ ] Détecter automatiquement les patterns attendus
- [ ] Comparaison avec baseline de référence
- [ ] Export des résultats en CSV

## Auteur

Alexandre Girold - Stage EPITA à l'Institut Curie (2025)

## Références

- Documentation UNITY : Elekta MR-Linac
- Normes ANSM pour les contrôles qualité IRM-Linac
