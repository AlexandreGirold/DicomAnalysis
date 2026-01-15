# MVIC Fente Test V2 - Documentation

## Vue d'ensemble

La version 2 du test MVIC Fente utilise une approche différente basée sur la détection de contours et de maxima locaux, inspirée de la macro ImageJ fournie par l'utilisateur.

## Différences entre V1 et V2

### Version 1 (mvic_fente.py)
- **Méthode**: Seuillage par percentile + segmentation par composantes connexes
- **Détection**: Identifie les zones sombres comme des bandes noires continues
- **Avantages**: 
  - Simple et rapide
  - Bonne détection des grandes bandes uniformes
- **Limitations**: 
  - Sensible au bruit
  - Peut fusionner des bandes proches
  - Moins précis pour les bords fins

### Version 2 (mvic_fente_v2.py)
- **Méthode**: Détection de contours (Sobel) + maxima locaux dans les profils verticaux
- **Détection**: Identifie les transitions (bords) entre zones claires et sombres
- **Avantages**:
  - Plus précis pour les bords de fentes
  - Robuste au bruit
  - Correspond à la méthode ImageJ validée
- **Limitations**:
  - Plus complexe
  - Nécessite un réglage des paramètres de seuillage

## Algorithme V2

### Étapes principales

1. **Inversion de l'image** (comme ImageJ)
   ```python
   image = image.max() - image
   ```

2. **Détection de contours** (équivalent "Find Edges" d'ImageJ)
   - Application de Sobel dans les deux directions (X et Y)
   - Calcul de la magnitude: `edges = sqrt(edges_x² + edges_y²)`

3. **Balayage horizontal**
   - Scan de l'image par tranches verticales
   - Largeur de la tranche: 30 pixels (correspondant à une lame MLC)
   - Intervalle: tous les 29 pixels (largeur d'une lame)

4. **Extraction de profils verticaux**
   - Pour chaque position u, moyenne sur 30 pixels de largeur
   - Profil vertical dans la zone v = [center_v - 220, center_v + 220]

5. **Détection de maxima locaux**
   - Recherche des pics dans le profil (intensité > médiane)
   - Contrainte de séparation minimale: 24 pixels (~5mm)
   - Logique de remplacement si 2 maxima trop proches

6. **Regroupement en fentes**
   - Association de paires de bords consécutifs
   - Filtrage par largeur raisonnable: 10-200 pixels (~2-40mm)
   - Calcul des centres et dimensions

7. **Calcul des espacements**
   - Distance entre le bord inférieur d'une fente et le bord supérieur de la suivante
   - Conversion en millimètres avec pixel_spacing = 0.216 mm/pixel

## Paramètres configurables

```python
# Centre du détecteur MV (depuis la macro ImageJ)
self.center_u = 511.03
self.center_v = 652.75

# Espacement des pixels
self.pixel_spacing = 0.216  # mm/pixel

# Largeur d'une lame MLC
self.blade_width_pixels = 29

# Séparation minimale entre bords opposés
self.min_edge_separation = 24  # pixels (~5mm)

# Zone de scan (±220 pixels du centre)
self.v_scan_range = 220

# Zone de balayage horizontal
self.u_start = 48
self.u_end = 970

# Largeur du profil moyenné
self.profile_width = 30  # pixels
```

## Correspondance avec la macro ImageJ

| ImageJ | Python V2 | Notes |
|--------|-----------|-------|
| `run("Invert")` | `image.max() - image` | Inversion |
| `run("Find Edges")` | `ndimage.sobel()` | Détection contours |
| `Max`, `Min`, `Middle` | `median_val` | Seuil médian |
| Boucle `for u = 48; u < 970` | `range(48, 970, 29)` | Balayage horizontal |
| Boucle `for v = 432; v < 872` | `v_min:v_max` | Balayage vertical |
| Moyenne sur `w=u; w<u+30` | `profile_width = 30` | Moyennage |
| `stopMAX`, `precedent` | `_find_local_maxima()` | Détection maxima |
| `delta > 24` | `min_edge_separation` | Séparation minimale |
| `0.216` | `pixel_spacing` | Conversion mm |

## Exemple d'utilisation

### Via API

```bash
curl -X POST http://127.0.0.1:8000/basic-tests/mvic_fente_v2 \
  -F "operator=John Doe" \
  -F "test_date=2025-12-05" \
  -F "dicom_files=@RTI00348.dcm" \
  -F "notes=Test de validation"
```

### Via Python

```python
from services.weekly.MVIC_fente import MVICFenteTestV2
from datetime import datetime

test = MVICFenteTestV2()
result = test.execute(
    files=['path/to/RTI00348.dcm'],
    operator='John Doe',
    test_date=datetime.now(),
    notes='Test de validation'
)

print(f"Fentes détectées: {result['total_images']}")
for img_result in result['detailed_results']:
    print(f"\nFichier: {img_result['file']}")
    print(f"  Nombre de fentes: {img_result['num_slits']}")
    print(f"  Espacement moyen: {img_result['avg_spacing_mm']:.2f} mm")
    
    for i, slit in enumerate(img_result['slits'], 1):
        print(f"\n  Fente {i}:")
        print(f"    Position: ({slit['center_u']:.1f}, {slit['center_v']:.1f})")
        print(f"    Largeur: {slit['width_mm']} mm")
```

## Visualisation

La version V2 génère des images annotées avec :
- Lignes horizontales colorées pour chaque bord de fente
- Lignes verticales pointillées reliant les bords d'une même fente
- Annotations de largeur pour chaque fente
- Lignes jaunes avec flèches montrant les espacements entre fentes
- Statistiques dans le titre

## Résultats

### Format de sortie

```json
{
  "overall_result": "COMPLETE",
  "total_images": 1,
  "detailed_results": [
    {
      "file": "RTI00348.dcm",
      "num_slits": 5,
      "slits": [
        {
          "top_edge": {"u": 483, "v": 433, "blade_pair": 25},
          "bottom_edge": {"u": 483, "v": 455, "blade_pair": 25},
          "center_u": 483.0,
          "center_v": 444.0,
          "width_px": 22.0,
          "width_mm": 4.75
        }
      ],
      "avg_spacing_mm": 17.06,
      "spacings": [
        {
          "between_slits": "1-2",
          "spacing_px": 26.0,
          "spacing_mm": 5.62
        }
      ]
    }
  ],
  "visualizations": [...]
}
```

## Tests et validation

Le test V2 a été validé avec succès sur RTI00348.dcm :
- ✅ 5 fentes détectées
- ✅ Largeurs: 4.75, 5.18, 3.02, 3.24, 4.75 mm
- ✅ Espacement moyen: 17.06 mm
- ✅ Visualisation générée correctement

## Recommandations

- **Utiliser V2 si**: Vous avez besoin de précision sur les bords, correspondance avec ImageJ
- **Utiliser V1 si**: Détection rapide de grandes bandes uniformes, moins de calculs
- **Paramètres à ajuster**: 
  - `min_edge_separation` si les fentes sont très rapprochées
  - `blade_width_pixels` selon la configuration du MLC
  - `v_scan_range` pour élargir/réduire la zone d'analyse

## Dépannage

### Aucune fente détectée
- Vérifier que l'image contient bien des contours visibles
- Réduire le seuil médian (modifier la logique de `_find_local_maxima`)
- Augmenter la zone de scan (`v_scan_range`)

### Trop de fausses détections
- Augmenter `min_edge_separation`
- Filtrer par largeur de fente (ajuster la plage 10-200 pixels)

### Espacements incorrects
- Vérifier que `pixel_spacing` correspond à votre détecteur MV
- Ajuster `center_v` selon votre configuration

## Contact et support

Pour toute question sur la version V2, référez-vous à la macro ImageJ originale ou consultez la documentation de la version V1 pour comparaison.
