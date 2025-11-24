"""
Script de test pour MVIC
Teste l'import et l'exécution basique du test MVIC
"""
import sys
import os

# Ajouter le chemin backend au sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_mvic_import():
    """Tester l'import du module MVIC"""
    print("Test 1: Import du module MVIC...")
    try:
        from services.weekly.MVIC import MVICTest, test_mvic
        print("✅ Import réussi: MVICTest, test_mvic")
        return True
    except Exception as e:
        print(f"❌ Échec de l'import: {e}")
        return False

def test_mvic_class():
    """Tester l'instanciation de la classe MVICTest"""
    print("\nTest 2: Instanciation de MVICTest...")
    try:
        from services.weekly.MVIC import MVICTest
        test = MVICTest()
        print(f"✅ Classe instanciée: {test.test_name}")
        print(f"   Description: {test.description}")
        return True
    except Exception as e:
        print(f"❌ Échec de l'instanciation: {e}")
        return False

def test_mvic_form_data():
    """Tester la récupération des données de formulaire"""
    print("\nTest 3: Récupération des données de formulaire...")
    try:
        from services.weekly.MVIC import MVICTest
        test = MVICTest()
        form_data = test.get_form_data()
        print(f"✅ Formulaire récupéré:")
        print(f"   Titre: {form_data['title']}")
        print(f"   Nombre de champs: {len(form_data['fields'])}")
        print(f"   Catégorie: {form_data['category']}")
        return True
    except Exception as e:
        print(f"❌ Échec de récupération du formulaire: {e}")
        return False

def test_weekly_tests_registration():
    """Tester l'enregistrement dans WEEKLY_TESTS"""
    print("\nTest 4: Enregistrement dans WEEKLY_TESTS...")
    try:
        from services.weekly import WEEKLY_TESTS
        if 'mvic' in WEEKLY_TESTS:
            test_info = WEEKLY_TESTS['mvic']
            print(f"✅ MVIC enregistré dans WEEKLY_TESTS")
            print(f"   Description: {test_info['description']}")
            print(f"   Catégorie: {test_info['category']}")
            return True
        else:
            print("❌ MVIC non trouvé dans WEEKLY_TESTS")
            print(f"   Tests disponibles: {list(WEEKLY_TESTS.keys())}")
            return False
    except Exception as e:
        print(f"❌ Échec de vérification WEEKLY_TESTS: {e}")
        return False

def test_validators_import():
    """Tester l'import des validateurs"""
    print("\nTest 5: Import des validateurs...")
    try:
        from services.weekly.MVIC.taille_champ import FieldSizeValidator
        from services.weekly.MVIC.forme_champ import FieldShapeValidator
        print("✅ FieldSizeValidator importé")
        print("✅ FieldShapeValidator importé")
        
        size_validator = FieldSizeValidator()
        shape_validator = FieldShapeValidator()
        print(f"   Tailles attendues: {[s['name'] for s in size_validator.expected_sizes]}")
        print(f"   Tolérance taille: ±{size_validator.size_tolerance}mm")
        print(f"   Tolérance angle: ±{shape_validator.angle_tolerance}°")
        return True
    except Exception as e:
        print(f"❌ Échec de l'import des validateurs: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Exécuter tous les tests"""
    print("="*60)
    print("TEST D'INTÉGRATION MVIC")
    print("="*60)
    
    tests = [
        test_mvic_import,
        test_mvic_class,
        test_mvic_form_data,
        test_weekly_tests_registration,
        test_validators_import
    ]
    
    results = []
    for test_func in tests:
        results.append(test_func())
    
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("✅ TOUS LES TESTS SONT PASSÉS")
        return 0
    else:
        print(f"❌ {total - passed} TEST(S) ÉCHOUÉ(S)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
