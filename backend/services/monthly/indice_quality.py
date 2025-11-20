"""
Test Indice de Qualité - D10/D20 et D5/D15
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_test import BaseTest
from datetime import datetime
from typing import Optional


class IndiceQualityTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_name="Indice de Qualité",
            description="Test D10/D20 et D5/D15 - Mesure des ratios de dose"
        )
        
        # Reference values
        self.d20_d10_reference = 0.704
        self.d15_d5_reference = 0.723
        self.tolerance = 0.01
    
    def execute(
        self,
        operator: str,
        d10_m1: float,
        d10_m2: float,
        d10_m3: float,
        d20_m1: float,
        d20_m2: float,
        d20_m3: float,
        d5_m1: float = 0.0,
        d5_m2: float = 0.0,
        d5_m3: float = 0.0,
        d15_m1: float = 0.0,
        d15_m2: float = 0.0,
        d15_m3: float = 0.0,
        test_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ):
        """
        Exécute le test d'indice de qualité
        
        Args:
            operator: Nom de l'opérateur
            d10_m1, d10_m2, d10_m3: Mesures D10 en nC (obligatoires)
            d20_m1, d20_m2, d20_m3: Mesures D20 en nC (obligatoires)
            d5_m1, d5_m2, d5_m3: Mesures D5 en nC (optionnelles, défaut: 0)
            d15_m1, d15_m2, d15_m3: Mesures D15 en nC (optionnelles, défaut: 0)
            test_date: Date du test
            notes: Notes additionnelles
        """
        self.set_test_info(operator, test_date)
        
        # Inputs
        self.add_input("operator", operator, "text")
        if notes:
            self.add_input("notes", notes, "text")
        
        # Calculate averages
        d10_moyenne = (d10_m1 + d10_m2 + d10_m3) / 3
        d20_moyenne = (d20_m1 + d20_m2 + d20_m3) / 3
        d5_moyenne = (d5_m1 + d5_m2 + d5_m3) / 3
        d15_moyenne = (d15_m1 + d15_m2 + d15_m3) / 3
        
        # Add measurement inputs
        self.add_input("d10_m1", d10_m1, "nC")
        self.add_input("d10_m2", d10_m2, "nC")
        self.add_input("d10_m3", d10_m3, "nC")
        self.add_input("d20_m1", d20_m1, "nC")
        self.add_input("d20_m2", d20_m2, "nC")
        self.add_input("d20_m3", d20_m3, "nC")
        
        if d5_m1 != 0 or d5_m2 != 0 or d5_m3 != 0:
            self.add_input("d5_m1", d5_m1, "nC")
            self.add_input("d5_m2", d5_m2, "nC")
            self.add_input("d5_m3", d5_m3, "nC")
        
        if d15_m1 != 0 or d15_m2 != 0 or d15_m3 != 0:
            self.add_input("d15_m1", d15_m1, "nC")
            self.add_input("d15_m2", d15_m2, "nC")
            self.add_input("d15_m3", d15_m3, "nC")
        
        # Add average results (informational)
        self.add_result(
            name="D10 Moyenne",
            value=round(d10_moyenne, 3),
            status="INFO",
            unit="nC",
            tolerance="Information"
        )
        
        self.add_result(
            name="D20 Moyenne",
            value=round(d20_moyenne, 3),
            status="INFO",
            unit="nC",
            tolerance="Information"
        )
        
        # Calculate D20/D10 ratio
        if d10_moyenne != 0:
            d20_d10_ratio = d20_moyenne / d10_moyenne
            d20_d10_diff = abs(d20_d10_ratio - self.d20_d10_reference)
            d20_d10_status = "PASS" if d20_d10_diff <= self.tolerance else "FAIL"
            
            self.add_result(
                name="Ratio D20/D10",
                value=round(d20_d10_ratio, 4),
                status=d20_d10_status,
                unit="",
                tolerance=f"{self.d20_d10_reference} ± {self.tolerance} (Plage: 0.694-0.714)"
            )
        else:
            self.add_result(
                name="Ratio D20/D10",
                value="Erreur: D10 = 0",
                status="FAIL",
                unit="",
                tolerance=f"{self.d20_d10_reference} ± {self.tolerance}"
            )
        
        # Check if D5/D15 measurements were provided
        d5_d15_provided = (d5_moyenne != 0 and d15_moyenne != 0)
        
        if d5_d15_provided:
            self.add_result(
                name="D5 Moyenne",
                value=round(d5_moyenne, 3),
                status="INFO",
                unit="nC",
                tolerance="Information"
            )
            
            self.add_result(
                name="D15 Moyenne",
                value=round(d15_moyenne, 3),
                status="INFO",
                unit="nC",
                tolerance="Information"
            )
            
            # Calculate D15/D5 ratio
            if d5_moyenne != 0:
                d15_d5_ratio = d15_moyenne / d5_moyenne
                d15_d5_diff = abs(d15_d5_ratio - self.d15_d5_reference)
                d15_d5_status = "PASS" if d15_d5_diff <= self.tolerance else "FAIL"
                
                self.add_result(
                    name="Ratio D15/D5",
                    value=round(d15_d5_ratio, 4),
                    status=d15_d5_status,
                    unit="",
                    tolerance=f"{self.d15_d5_reference} ± {self.tolerance} (Plage: 0.713-0.733)"
                )
            else:
                self.add_result(
                    name="Ratio D15/D5",
                    value="Erreur: D5 = 0",
                    status="FAIL",
                    unit="",
                    tolerance=f"{self.d15_d5_reference} ± {self.tolerance}"
                )
        
        self.calculate_overall_result()
        return self.to_dict()
    
    def get_form_data(self):
        """Retourne les données pour générer le formulaire"""
        return {
            'title': 'Test Indice de Qualité',
            'description': 'Test D10/D20 et D5/D15 - Mesure des ratios de dose (en 2 étapes)',
            'fields': [
                {
                    'name': 'test_date',
                    'label': 'Date du test:',
                    'type': 'date',
                    'required': True,
                    'description': 'Date de réalisation du test'
                },
                {
                    'name': 'operator',
                    'label': 'Opérateur:',
                    'type': 'text',
                    'required': True,
                    'description': 'Nom de l\'opérateur effectuant le test'
                },
                {
                    'name': 'section_step1',
                    'label': '━━━ ÉTAPE 1 : MESURES D10 et D20 (OBLIGATOIRE) ━━━',
                    'type': 'section',
                    'description': 'Effectuez 3 mesures (M1, M2, M3) pour D10 et D20'
                },
                {
                    'name': 'd10_m1',
                    'label': 'D10 - M1 (nC):',
                    'type': 'number',
                    'required': True,
                    'step': '0.001',
                    'description': 'Première mesure à 10 cm de profondeur'
                },
                {
                    'name': 'd10_m2',
                    'label': 'D10 - M2 (nC):',
                    'type': 'number',
                    'required': True,
                    'step': '0.001',
                    'description': 'Deuxième mesure à 10 cm de profondeur'
                },
                {
                    'name': 'd10_m3',
                    'label': 'D10 - M3 (nC):',
                    'type': 'number',
                    'required': True,
                    'step': '0.001',
                    'description': 'Troisième mesure à 10 cm de profondeur'
                },
                {
                    'name': 'd20_m1',
                    'label': 'D20 - M1 (nC):',
                    'type': 'number',
                    'required': True,
                    'step': '0.001',
                    'description': 'Première mesure à 20 cm de profondeur'
                },
                {
                    'name': 'd20_m2',
                    'label': 'D20 - M2 (nC):',
                    'type': 'number',
                    'required': True,
                    'step': '0.001',
                    'description': 'Deuxième mesure à 20 cm de profondeur'
                },
                {
                    'name': 'd20_m3',
                    'label': 'D20 - M3 (nC):',
                    'type': 'number',
                    'required': True,
                    'step': '0.001',
                    'description': 'Troisième mesure à 20 cm de profondeur'
                },
                {
                    'name': 'section_step2',
                    'label': '━━━ ÉTAPE 2 : MESURES D5 et D15 (OPTIONNEL) ━━━',
                    'type': 'section',
                    'description': 'Vous pouvez laisser ces champs vides si vous ne souhaitez pas effectuer ces mesures'
                },
                {
                    'name': 'info_optional',
                    'label': '⚠️ Si vous ne faites pas ces mesures, laissez simplement tous les champs vides ou à 0',
                    'type': 'info'
                },
                {
                    'name': 'd5_m1',
                    'label': 'D5 - M1 (nC):',
                    'type': 'number',
                    'required': False,
                    'step': '0.001',
                    'value': '0',
                    'description': 'Première mesure à 5 cm de profondeur (optionnel)'
                },
                {
                    'name': 'd5_m2',
                    'label': 'D5 - M2 (nC):',
                    'type': 'number',
                    'required': False,
                    'step': '0.001',
                    'value': '0',
                    'description': 'Deuxième mesure à 5 cm de profondeur (optionnel)'
                },
                {
                    'name': 'd5_m3',
                    'label': 'D5 - M3 (nC):',
                    'type': 'number',
                    'required': False,
                    'step': '0.001',
                    'value': '0',
                    'description': 'Troisième mesure à 5 cm de profondeur (optionnel)'
                },
                {
                    'name': 'd15_m1',
                    'label': 'D15 - M1 (nC):',
                    'type': 'number',
                    'required': False,
                    'step': '0.001',
                    'value': '0',
                    'description': 'Première mesure à 15 cm de profondeur (optionnel)'
                },
                {
                    'name': 'd15_m2',
                    'label': 'D15 - M2 (nC):',
                    'type': 'number',
                    'required': False,
                    'step': '0.001',
                    'value': '0',
                    'description': 'Deuxième mesure à 15 cm de profondeur (optionnel)'
                },
                {
                    'name': 'd15_m3',
                    'label': 'D15 - M3 (nC):',
                    'type': 'number',
                    'required': False,
                    'step': '0.001',
                    'value': '0',
                    'description': 'Troisième mesure à 15 cm de profondeur (optionnel)'
                },
                {
                    'name': 'notes',
                    'label': 'Notes:',
                    'type': 'textarea',
                    'required': False,
                    'description': 'Notes et observations supplémentaires'
                }
            ],
            'category': 'monthly'
        }


def test_indice_quality(
    operator: str,
    d10_m1: float,
    d10_m2: float,
    d10_m3: float,
    d20_m1: float,
    d20_m2: float,
    d20_m3: float,
    d5_m1: float = 0.0,
    d5_m2: float = 0.0,
    d5_m3: float = 0.0,
    d15_m1: float = 0.0,
    d15_m2: float = 0.0,
    d15_m3: float = 0.0,
    test_date: Optional[datetime] = None,
    notes: Optional[str] = None
):
    """Fonction wrapper pour exécuter le test d'indice de qualité"""
    return IndiceQualityTest().execute(
        operator=operator,
        d10_m1=d10_m1,
        d10_m2=d10_m2,
        d10_m3=d10_m3,
        d20_m1=d20_m1,
        d20_m2=d20_m2,
        d20_m3=d20_m3,
        d5_m1=d5_m1,
        d5_m2=d5_m2,
        d5_m3=d5_m3,
        d15_m1=d15_m1,
        d15_m2=d15_m2,
        d15_m3=d15_m3,
        test_date=test_date,
        notes=notes
    )
