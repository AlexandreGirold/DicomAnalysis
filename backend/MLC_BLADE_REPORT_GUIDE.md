# Guide d'Utilisation - Générateur de Rapports de Lames MLC

## Vue d'ensemble

Le système de génération de rapports de lames MLC produit des documents PDF professionnels avec :
- ✅ Analyse de conformité des lames par taille (20mm, 30mm, 40mm)
- 📊 Graphiques de tendance avec bandes de tolérance
- 📋 Tableaux détaillés avec toutes les mesures
- 📈 Statistiques et résumé exécutif
- 📖 Annexe méthodologique

## Structure du Rapport Généré

### 1. Page de Garde
- Titre du rapport
- Période d'analyse
- Date de génération
- Nombre de tests analysés

### 2. Résumé Exécutif
Contient :
- Nombre total de lames testées
- Taux de conformité global (pourcentage)
- Nombre de lames conformes / hors tolérance / fermées
- Liste des anomalies majeures identifiées

**Exemple :**
```
Nombre total de lames testées: 480
Lames conformes: 442 (92.1%)
Lames hors tolérance: 35 (7.3%)
Lames fermées: 3 (0.6%)
```

### 3. Graphiques de Tendance

Un graphique par taille de lame (20mm, 30mm, 40mm) montrant :
- **Axe X** : Date du test
- **Axe Y** : Taille mesurée (mm)
- **Points** : 
  - 🟢 Vert (○) : Lame conforme
  - 🔴 Rouge (×) : Hors tolérance
  - ⚫ Noir (×) : Lame fermée
- **Lignes de référence** :
  - Ligne verte : Valeur cible
  - Lignes rouges pointillées : Limites de tolérance (±1.0mm)

### 4. Tableaux Détaillés

Pour chaque taille de lame (20mm, 30mm, 40mm), un tableau avec :

| Colonne | Description | Format |
|---------|-------------|--------|
| **Lame** | Numéro de paire de lames | Entier |
| **V_sup (px)** | Coordonnée supérieure en pixels | Entier |
| **V_inf (px)** | Coordonnée inférieure en pixels | Entier |
| **Top (mm)** | Distance supérieure en mm | 2 décimales |
| **Bottom (mm)** | Distance inférieure en mm | 2 décimales |
| **Size (mm)** | Taille effective mesurée | 2 décimales |
| **Conformité** | Statut | ✅ / ❌ / ⚫ |
| **Commentaires** | Écart par rapport à la cible | "+X.XXmm" ou "-X.XXmm" |

**Exemple de ligne :**
```
27 | 561 | 649 | 19.82 | 0.81 | 19.01 | ✅ | -0.99mm
```

### 5. Annexe Méthodologique

- **Tolérances appliquées** :
  - Lames 20mm : ±1.0 mm
  - Lames 30mm : ±1.0 mm
  - Lames 40mm : ±1.0 mm

- **Méthode de mesure** :
  - Analyse d'images DICOM
  - Détection de contours automatisée
  - Conversion pixel-millimètre basée sur les métadonnées

- **Codes de statut** :
  - `OK` (✅) : Lame conforme, dans la tolérance
  - `OUT_OF_TOLERANCE` (❌) : Hors tolérance, nécessite attention
  - `CLOSED` (⚫) : Lame fermée

## Utilisation de l'API

### Endpoint

```
POST /reports/mlc-blade-compliance
```

### Paramètres

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `test_ids` | List[int] | Oui | Liste des IDs de tests à inclure |
| `blade_size` | string | Non | Filtre de taille : "20mm", "30mm", "40mm", ou "all" (défaut: "all") |

### Exemples d'Utilisation

#### 1. Rapport complet (toutes les tailles)

**Python :**
```python
import requests

# Liste des IDs de tests
test_ids = [1, 2, 3, 4, 5]

# Générer le rapport
response = requests.post(
    'http://localhost:8000/reports/mlc-blade-compliance',
    params={
        'test_ids': test_ids,
        'blade_size': 'all'
    }
)

# Sauvegarder le PDF
with open('rapport_mlc_complet.pdf', 'wb') as f:
    f.write(response.content)

print("Rapport généré avec succès!")
```

**cURL :**
```bash
curl -X POST "http://localhost:8000/reports/mlc-blade-compliance?test_ids=1&test_ids=2&test_ids=3&blade_size=all" \
  --output rapport_mlc_complet.pdf
```

#### 2. Rapport pour lames 20mm uniquement

**Python :**
```python
import requests

response = requests.post(
    'http://localhost:8000/reports/mlc-blade-compliance',
    params={
        'test_ids': [1, 2, 3],
        'blade_size': '20mm'
    }
)

with open('rapport_lames_20mm.pdf', 'wb') as f:
    f.write(response.content)
```

**JavaScript (Frontend) :**
```javascript
async function generateMLCReport(testIds, bladeSize = 'all') {
    const params = new URLSearchParams();
    testIds.forEach(id => params.append('test_ids', id));
    params.append('blade_size', bladeSize);
    
    const response = await fetch(
        `/reports/mlc-blade-compliance?${params.toString()}`,
        { method: 'POST' }
    );
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    
    // Téléchargement automatique
    const a = document.createElement('a');
    a.href = url;
    a.download = `rapport_mlc_${bladeSize}_${Date.now()}.pdf`;
    a.click();
}

// Utilisation
generateMLCReport([1, 2, 3, 4], '30mm');
```

#### 3. Récupérer les tests d'une période et générer un rapport

**Python :**
```python
import requests
from datetime import datetime, timedelta

# 1. Récupérer les tests des 30 derniers jours
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

tests_response = requests.get(
    'http://localhost:8000/mlc-test-sessions',
    params={
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
)

tests = tests_response.json()
test_ids = [test['id'] for test in tests]

print(f"Trouvé {len(test_ids)} tests")

# 2. Générer le rapport
if test_ids:
    report_response = requests.post(
        'http://localhost:8000/reports/mlc-blade-compliance',
        params={
            'test_ids': test_ids,
            'blade_size': 'all'
        }
    )
    
    filename = f"rapport_mlc_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
    with open(filename, 'wb') as f:
        f.write(report_response.content)
    
    print(f"Rapport généré : {filename}")
else:
    print("Aucun test trouvé pour cette période")
```

## Format des Données en Entrée

Le système attend des tests avec la structure suivante dans la base de données :

```python
{
    "test_id": 1,
    "test_date": "2025-12-30T10:30:00",
    "operator": "Dr. Smith",
    "overall_result": "PASS",
    "blade_results": [
        {
            "blade_pair": 27,
            "v_sup_px": 561,
            "v_inf_px": 649,
            "top_mm": 19.82,
            "bottom_mm": 0.81,
            "field_size_mm": 19.01,
            "status": "OK"
        },
        {
            "blade_pair": 28,
            "v_sup_px": 565,
            "v_inf_px": 655,
            "top_mm": 30.15,
            "bottom_mm": 0.85,
            "field_size_mm": 29.30,
            "status": "OUT_OF_TOLERANCE"
        }
        // ... autres lames
    ]
}
```

## Personnalisation

### Modifier les Tolérances

Dans `backend/services/mlc_blade_report_generator.py` :

```python
class MLCBladeReportGenerator:
    # Tolerance thresholds (in mm)
    TOLERANCE_20MM = 1.0  # Modifier ici
    TOLERANCE_30MM = 1.0  # Modifier ici
    TOLERANCE_40MM = 1.0  # Modifier ici
```

### Ajouter des Graphiques Personnalisés

Modifiez la méthode `_create_trend_graphs()` pour ajouter vos propres visualisations.

### Changer le Style du PDF

Personnalisez les styles dans la méthode `_setup_custom_styles()` :

```python
self.styles.add(ParagraphStyle(
    name='ReportTitle',
    fontSize=26,                              # Taille du titre
    textColor=colors.HexColor('#1a5490'),    # Couleur
    alignment=TA_CENTER                       # Alignement
))
```

## Automatisation

### Script de Génération Automatique Hebdomadaire

```python
#!/usr/bin/env python3
"""
Script d'automatisation : génère un rapport hebdomadaire des lames MLC
À exécuter via cron ou task scheduler
"""
import requests
from datetime import datetime, timedelta
import os

def generate_weekly_report():
    # Période : 7 derniers jours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Récupérer les tests
    response = requests.get(
        'http://localhost:8000/mlc-test-sessions',
        params={
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
    )
    
    tests = response.json()
    test_ids = [test['id'] for test in tests]
    
    if not test_ids:
        print("Aucun test cette semaine")
        return
    
    # Générer le rapport
    report_response = requests.post(
        'http://localhost:8000/reports/mlc-blade-compliance',
        params={'test_ids': test_ids, 'blade_size': 'all'}
    )
    
    # Sauvegarder dans le dossier des rapports
    reports_dir = "/path/to/reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    filename = f"rapport_hebdo_{datetime.now().strftime('%Y_semaine_%W')}.pdf"
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(report_response.content)
    
    print(f"Rapport généré : {filepath}")

if __name__ == "__main__":
    generate_weekly_report()
```

### Cron Job (Linux/Mac)

```bash
# Éditer crontab
crontab -e

# Ajouter : exécuter tous les lundis à 8h00
0 8 * * 1 /usr/bin/python3 /path/to/generate_weekly_report.py
```

### Task Scheduler (Windows)

```powershell
# Créer une tâche planifiée
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\generate_weekly_report.py"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am
Register-ScheduledTask -TaskName "MLC Weekly Report" -Action $action -Trigger $trigger
```

## Dépannage

### Erreur : "Report generator not available"

**Solution :** Vérifier que les dépendances sont installées :
```bash
pip install reportlab matplotlib pandas numpy scipy
```

### Erreur : "No valid tests found"

**Solution :** Vérifier que les IDs de tests existent dans la base de données :
```python
import database as db
test = db.get_test_by_id(1)
print(test)
```

### PDF vide ou incomplet

**Solution :** Vérifier que les tests ont des `blade_results` :
```python
import database as db
test = db.get_test_by_id(1)
print(f"Nombre de lames : {len(test.get('blade_results', []))}")
```

### Graphiques ne s'affichent pas

**Solution :** S'assurer que matplotlib utilise le backend 'Agg' :
```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
```

## Support et Contact

Pour toute question ou problème :
- Consulter la documentation technique dans `backend/services/mlc_blade_report_generator.py`
- Vérifier les logs du serveur pour les erreurs détaillées
- Ouvrir une issue sur le repository GitHub

## Roadmap / Améliorations Futures

- [ ] Ajout de graphiques en boîte à moustaches (box plots)
- [ ] Export des données en Excel/CSV
- [ ] Comparaison entre périodes
- [ ] Alertes automatiques par email
- [ ] Dashboard interactif avec graphiques dynamiques
- [ ] Support multi-langue (EN/FR)
