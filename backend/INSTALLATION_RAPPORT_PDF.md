# Installation et Configuration du Générateur de Rapports PDF MLC

## Étape 1 : Vérifier les Dépendances Python

Le système de génération de rapports nécessite plusieurs bibliothèques Python. Installez-les avec :

```powershell
cd C:\Users\agirold\Desktop\DicomAnalysis\backend
.\env\Scripts\Activate.ps1
pip install reportlab matplotlib pandas numpy scipy pillow
```

### Vérification de l'installation

```powershell
python -c "import reportlab; import matplotlib; import pandas; import numpy; print('✅ Toutes les dépendances sont installées')"
```

## Étape 2 : Vérifier la Structure du Projet

Assurez-vous que ces fichiers existent :

```
backend/
├── services/
│   └── mlc_blade_report_generator.py  ← NOUVEAU fichier créé
├── routers/
│   └── reports.py  ← Modifié avec nouveau endpoint
├── database/
│   └── queries.py  ← Utilisé pour récupérer les tests
└── main.py
```

## Étape 3 : Redémarrer le Serveur Backend

**Important** : Le serveur doit être redémarré pour charger les nouveaux modules.

```powershell
# Arrêter le serveur (Ctrl+C si en cours d'exécution)

# Redémarrer
cd C:\Users\agirold\Desktop\DicomAnalysis\backend
.\env\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Vous devriez voir :
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Étape 4 : Tester le Nouveau Endpoint

### Option A : Test avec PowerShell

```powershell
# Test simple
$response = Invoke-WebRequest -Uri "http://localhost:8000/reports/mlc-blade-compliance?test_ids=1&test_ids=2&test_ids=3&blade_size=all" `
    -Method POST `
    -OutFile "C:\Users\agirold\Downloads\rapport_test.pdf"

Write-Host "✅ Rapport généré : C:\Users\agirold\Downloads\rapport_test.pdf"
```

### Option B : Test avec Python

Créez un fichier `test_report.py` :

```python
import requests
import os

# Configuration
API_URL = "http://localhost:8000"
test_ids = [1, 2, 3]  # Remplacer par des IDs réels
blade_size = "all"  # ou "20mm", "30mm", "40mm"

# Générer le rapport
print(f"Génération du rapport pour les tests : {test_ids}")

try:
    response = requests.post(
        f"{API_URL}/reports/mlc-blade-compliance",
        params={
            'test_ids': test_ids,
            'blade_size': blade_size
        },
        timeout=30
    )
    
    if response.status_code == 200:
        # Sauvegarder le PDF
        output_path = "C:\\Users\\agirold\\Downloads\\rapport_mlc_test.pdf"
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Rapport généré avec succès !")
        print(f"📄 Fichier : {output_path}")
        print(f"📏 Taille : {len(response.content)} bytes")
        
        # Ouvrir automatiquement
        os.startfile(output_path)
    else:
        print(f"❌ Erreur {response.status_code}")
        print(f"Message : {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Impossible de se connecter au serveur")
    print("Vérifiez que le serveur est démarré sur http://localhost:8000")
except Exception as e:
    print(f"❌ Erreur : {e}")
```

Exécutez :
```powershell
python test_report.py
```

## Étape 5 : Vérifier que des Tests Existent dans la Base

Avant de générer un rapport, vérifiez qu'il y a des tests dans la base de données :

```python
# check_tests.py
import requests

response = requests.get("http://localhost:8000/leaf-position-sessions")
tests = response.json()

print(f"Nombre de tests Leaf Position : {len(tests)}")
for test in tests[:5]:  # Afficher les 5 premiers
    print(f"  - Test ID {test['id']}: {test['test_date']}")

# Vérifier MLC tests
response = requests.get("http://localhost:8000/mlc-test-sessions")
mlc_tests = response.json()
print(f"\nNombre de tests MLC : {len(mlc_tests)}")
for test in mlc_tests[:5]:
    print(f"  - Test ID {test['id']}: {test['test_date']}")
```

## Étape 6 : Dépannage Commun

### Problème 1 : Erreur "Report generator not available"

**Cause** : Le module `mlc_blade_report_generator.py` n'est pas trouvé.

**Solution** :
```powershell
# Vérifier que le fichier existe
Test-Path "C:\Users\agirold\Desktop\DicomAnalysis\backend\services\mlc_blade_report_generator.py"
# Doit retourner True

# Redémarrer le serveur
```

### Problème 2 : Erreur "No valid tests found"

**Cause** : Les IDs de tests fournis n'existent pas ou ne sont pas du bon type.

**Solution** :
```python
# Lister les tests disponibles
import requests

# Tests Leaf Position
response = requests.get("http://localhost:8000/leaf-position-sessions?limit=10")
leaf_tests = response.json()
print("Tests Leaf Position disponibles :")
for test in leaf_tests:
    print(f"  ID: {test['id']}, Date: {test['test_date']}")

# Tests MLC
response = requests.get("http://localhost:8000/mlc-test-sessions?limit=10")
mlc_tests = response.json()
print("\nTests MLC disponibles :")
for test in mlc_tests:
    print(f"  ID: {test['id']}, Date: {test['test_date']}")
```

### Problème 3 : Erreur d'import matplotlib

**Cause** : Matplotlib n'est pas installé ou mal configuré.

**Solution** :
```powershell
pip uninstall matplotlib
pip install matplotlib --upgrade
pip install pillow
```

### Problème 4 : PDF vide ou corrompu

**Cause** : Les données de test n'ont pas de `blade_results`.

**Solution** :
```python
# Vérifier la structure d'un test
import requests

response = requests.get("http://localhost:8000/leaf-position-sessions/1")  # Remplacer 1 par un ID réel
test = response.json()

print("Structure du test :")
print(f"  ID: {test.get('id')}")
print(f"  Date: {test.get('test_date')}")
print(f"  Blade results: {len(test.get('blade_results', []))} lames")

# Afficher une lame
if test.get('blade_results'):
    blade = test['blade_results'][0]
    print(f"\nExemple de lame :")
    print(f"  Blade pair: {blade.get('blade_pair')}")
    print(f"  Field size: {blade.get('field_size_mm')} mm")
    print(f"  Status: {blade.get('status_message')}")
```

## Étape 7 : Exemple Complet d'Utilisation

```python
# generate_weekly_report.py
import requests
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000"

# 1. Récupérer les tests de la semaine dernière
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"Recherche des tests entre {start_date.date()} et {end_date.date()}")

response = requests.get(
    f"{API_URL}/leaf-position-sessions",
    params={
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
)

tests = response.json()
test_ids = [test['id'] for test in tests]

print(f"✅ Trouvé {len(test_ids)} tests")

if not test_ids:
    print("❌ Aucun test trouvé pour cette période")
    exit(1)

# 2. Générer le rapport pour chaque taille
for blade_size in ['20mm', '30mm', '40mm']:
    print(f"\nGénération du rapport pour les lames {blade_size}...")
    
    response = requests.post(
        f"{API_URL}/reports/mlc-blade-compliance",
        params={
            'test_ids': test_ids,
            'blade_size': blade_size
        }
    )
    
    if response.status_code == 200:
        filename = f"rapport_lames_{blade_size}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = f"C:\\Users\\agirold\\Downloads\\{filename}"
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ {filename} généré ({len(response.content)} bytes)")
    else:
        print(f"❌ Erreur pour {blade_size}: {response.text}")

print("\n🎉 Génération terminée !")
```

## Étape 8 : Vérifier les Logs du Serveur

En cas d'erreur, consultez les logs du serveur FastAPI dans le terminal :

```
INFO:     127.0.0.1:xxxxx - "POST /reports/mlc-blade-compliance?test_ids=1 HTTP/1.1" 200 OK
[MLC-BLADE-REPORT] Generating report for 1 tests, size filter: all
[MLC-BLADE-REPORT] Successfully generated report: mlc_blade_compliance_all_20251230_143025.pdf
```

Les erreurs apparaîtront avec `ERROR` ou `WARNING`.

## Résumé des Commandes Rapides

```powershell
# 1. Installer dépendances
pip install reportlab matplotlib pandas numpy scipy pillow

# 2. Redémarrer serveur
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Tester
python test_report.py

# 4. Vérifier tests disponibles
python check_tests.py
```

## Support

Si vous rencontrez des problèmes :

1. ✅ Vérifiez que le serveur est démarré
2. ✅ Vérifiez que les dépendances sont installées
3. ✅ Vérifiez qu'il y a des tests dans la base avec `blade_results`
4. ✅ Consultez les logs du serveur pour les détails des erreurs
5. ✅ Testez avec un seul test_id d'abord avant d'en utiliser plusieurs
