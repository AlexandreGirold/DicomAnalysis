"""
Script de test pour le générateur de rapports PDF MLC
Ce script vérifie que tout fonctionne correctement
"""
import requests
import sys
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"

def test_server_connection():
    """Test 1: Vérifier que le serveur répond"""
    print("🔍 Test 1: Connexion au serveur...")
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur accessible")
            return True
        else:
            print(f"❌ Serveur répond avec code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur est démarré:")
        print("   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_get_tests():
    """Test 2: Récupérer la liste des tests"""
    print("\n🔍 Test 2: Récupération des tests...")
    try:
        # Tester Leaf Position
        response = requests.get(f"{API_URL}/leaf-position-sessions?limit=5")
        if response.status_code == 200:
            tests = response.json()
            print(f"✅ {len(tests)} tests Leaf Position trouvés")
            if tests:
                print(f"   Premier test: ID={tests[0]['id']}, Date={tests[0]['test_date']}")
                return tests[0]['id']  # Retourner le premier ID
            else:
                print("⚠️  Aucun test Leaf Position trouvé")
                
                # Essayer MLC tests
                response = requests.get(f"{API_URL}/mlc-test-sessions?limit=5")
                if response.status_code == 200:
                    mlc_tests = response.json()
                    print(f"   {len(mlc_tests)} tests MLC trouvés")
                    if mlc_tests:
                        return mlc_tests[0]['id']
                return None
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_get_test_details(test_id):
    """Test 3: Vérifier les détails d'un test"""
    print(f"\n🔍 Test 3: Détails du test ID {test_id}...")
    try:
        response = requests.get(f"{API_URL}/leaf-position-sessions/{test_id}")
        if response.status_code == 200:
            test = response.json()
            blade_results = test.get('blade_results', [])
            print(f"✅ Test récupéré avec {len(blade_results)} lames")
            
            if blade_results:
                blade = blade_results[0]
                print(f"   Exemple de lame:")
                print(f"     - Blade pair: {blade.get('blade_pair')}")
                print(f"     - Field size: {blade.get('field_size_mm')} mm")
                print(f"     - V_sup: {blade.get('v_sup_px')} px")
                print(f"     - V_inf: {blade.get('v_inf_px')} px")
                return True
            else:
                print("⚠️  Test sans blade_results - le rapport sera vide")
                return False
        else:
            print(f"❌ Erreur {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_generate_report(test_id):
    """Test 4: Générer un rapport PDF"""
    print(f"\n🔍 Test 4: Génération du rapport PDF...")
    try:
        response = requests.post(
            f"{API_URL}/reports/mlc-blade-compliance",
            params={
                'test_ids': [test_id],
                'blade_size': 'all'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            # Vérifier que c'est bien un PDF
            if response.content[:4] == b'%PDF':
                size_kb = len(response.content) / 1024
                print(f"✅ Rapport PDF généré ({size_kb:.1f} KB)")
                
                # Sauvegarder le rapport
                output_path = f"C:\\Users\\agirold\\Downloads\\rapport_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Rapport sauvegardé: {output_path}")
                return True
            else:
                print("❌ La réponse n'est pas un PDF valide")
                print(f"   Contenu: {response.content[:100]}")
                return False
        else:
            print(f"❌ Erreur {response.status_code}")
            print(f"   Message: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - la génération prend trop de temps")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_dependencies():
    """Test 0: Vérifier les dépendances Python"""
    print("🔍 Test 0: Vérification des dépendances...")
    missing = []
    
    try:
        import reportlab
        print("✅ reportlab installé")
    except ImportError:
        missing.append("reportlab")
        print("❌ reportlab manquant")
    
    try:
        import matplotlib
        print("✅ matplotlib installé")
    except ImportError:
        missing.append("matplotlib")
        print("❌ matplotlib manquant")
    
    try:
        import pandas
        print("✅ pandas installé")
    except ImportError:
        missing.append("pandas")
        print("❌ pandas manquant")
    
    try:
        import numpy
        print("✅ numpy installé")
    except ImportError:
        missing.append("numpy")
        print("❌ numpy manquant")
    
    if missing:
        print(f"\n❌ Dépendances manquantes: {', '.join(missing)}")
        print(f"   Installer avec: pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """Exécuter tous les tests"""
    print("=" * 60)
    print("TEST DU GÉNÉRATEUR DE RAPPORTS PDF MLC")
    print("=" * 60)
    
    # Test 0: Dépendances
    if not check_dependencies():
        print("\n❌ Tests arrêtés - installer les dépendances d'abord")
        sys.exit(1)
    
    # Test 1: Connexion
    if not test_server_connection():
        print("\n❌ Tests arrêtés - le serveur n'est pas accessible")
        sys.exit(1)
    
    # Test 2: Récupérer tests
    test_id = test_get_tests()
    if not test_id:
        print("\n❌ Tests arrêtés - aucun test trouvé dans la base")
        print("   Exécutez d'abord des tests MLC ou Leaf Position")
        sys.exit(1)
    
    # Test 3: Détails du test
    has_blades = test_get_test_details(test_id)
    if not has_blades:
        print("\n⚠️  Attention: Le test n'a pas de blade_results")
        print("   Le rapport sera généré mais sera vide")
    
    # Test 4: Générer rapport
    if test_generate_report(test_id):
        print("\n" + "=" * 60)
        print("🎉 TOUS LES TESTS ONT RÉUSSI !")
        print("=" * 60)
        print("\nLe système de génération de rapports PDF est opérationnel.")
        print("\nUtilisation:")
        print(f"  POST {API_URL}/reports/mlc-blade-compliance")
        print("  Paramètres: test_ids=[1,2,3], blade_size='all'")
    else:
        print("\n" + "=" * 60)
        print("❌ ÉCHEC DE LA GÉNÉRATION DU RAPPORT")
        print("=" * 60)
        print("\nVérifiez les logs du serveur pour plus de détails")
        sys.exit(1)

if __name__ == "__main__":
    main()
