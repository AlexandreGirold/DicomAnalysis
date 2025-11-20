"""
Test QUASAR - Latence du gating et Précision
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_test import BaseTest
from datetime import datetime
from typing import Optional


class QuasarTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_name="QUASAR",
            description="Test de Latence du gating et Test de précision QUASAR"
        )
    
    def execute(
        self,
        operator: str,
        latence_status: str,
        latence_reason: Optional[str] = None,
        coord_correction: Optional[float] = None,
        x_value: Optional[float] = None,
        y_value: Optional[float] = None,
        z_value: Optional[float] = None,
        test_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ):
        """
        Exécute le test QUASAR
        
        Args:
            operator: Nom de l'opérateur
            latence_status: Statut du test de latence (PASS/FAIL/SKIP)
            latence_reason: Raison si SKIP
            coord_correction: Correction du système de coordonnées
            x_value: Coordonnée X en cm
            y_value: Coordonnée Y en cm
            z_value: Coordonnée Z en cm
            test_date: Date du test
            notes: Notes additionnelles
        """
        self.set_test_info(operator, test_date)
        
        # Inputs
        self.add_input("operator", operator, "text")
        if notes:
            self.add_input("notes", notes, "text")
        self.add_input("latence_status", latence_status, "text")
        if latence_reason:
            self.add_input("latence_reason", latence_reason, "text")
        
        # S4.4 - Test de Latence du gating
        if latence_status == "PASS":
            self.add_result(
                name="Latence du gating",
                value="PASS",
                status="PASS",
                unit="",
                tolerance="Test manuel"
            )
        elif latence_status == "FAIL":
            self.add_result(
                name="Latence du gating",
                value="FAIL",
                status="FAIL",
                unit="",
                tolerance="Test manuel"
            )
        elif latence_status == "SKIP":
            self.add_result(
                name="Latence du gating",
                value=f"SKIP - {latence_reason or 'Non spécifié'}",
                status="INFO",
                unit="",
                tolerance="Test manuel"
            )
        
        # S4.5 - Test de Précision QUASAR
        if coord_correction is not None:
            self.add_input("coord_correction", coord_correction, "")
            self.add_result(
                name="Correction Système Coord.",
                value=coord_correction,
                status="INFO",
                unit="",
                tolerance="Information"
            )
        
        if x_value is not None:
            self.add_input("x_value", x_value, "cm")
            # Tolérance typique pour QUASAR: ±2mm
            x_status = "PASS" if abs(x_value) <= 0.2 else "FAIL"
            self.add_result(
                name="Position X",
                value=x_value,
                status=x_status,
                unit="cm",
                tolerance="± 0.2 cm"
            )
        
        if y_value is not None:
            self.add_input("y_value", y_value, "cm")
            y_status = "PASS" if abs(y_value) <= 0.2 else "FAIL"
            self.add_result(
                name="Position Y",
                value=y_value,
                status=y_status,
                unit="cm",
                tolerance="± 0.2 cm"
            )
        
        if z_value is not None:
            self.add_input("z_value", z_value, "cm")
            z_status = "PASS" if abs(z_value) <= 0.2 else "FAIL"
            self.add_result(
                name="Position Z",
                value=z_value,
                status=z_status,
                unit="cm",
                tolerance="± 0.2 cm"
            )
        
        self.calculate_overall_result()
        return self.to_dict()
    
    def get_form_data(self):
        """Retourne les données pour générer le formulaire"""
        return {
            'title': 'Test QUASAR',
            'description': 'S4.4 Test de Latence du gating et S4.5 Test de Précision QUASAR',
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
                    'name': 'section_latence',
                    'label': 'S4.4 - Test de Latence du gating',
                    'type': 'section'
                },
                {
                    'name': 'latence_status',
                    'label': 'Statut Latence:',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'description': 'Résultat du test de latence du gating'
                },
                {
                    'name': 'latence_reason',
                    'label': 'Raison (si SKIP):',
                    'type': 'text',
                    'required': False,
                    'description': 'Raison pour laquelle le test a été ignoré'
                },
                {
                    'name': 'section_accuracy',
                    'label': 'S4.5 - Test de Précision QUASAR (Accuracy)',
                    'type': 'section'
                },
                {
                    'name': 'coord_correction',
                    'label': 'Coord System Correction:',
                    'type': 'number',
                    'required': False,
                    'step': '0.01',
                    'description': 'Correction du système de coordonnées'
                },
                {
                    'name': 'x_value',
                    'label': 'X (cm):',
                    'type': 'number',
                    'required': False,
                    'step': '0.01',
                    'description': 'Coordonnée X mesurée',
                    'tolerance': '± 0.2 cm (± 2 mm)'
                },
                {
                    'name': 'y_value',
                    'label': 'Y (cm):',
                    'type': 'number',
                    'required': False,
                    'step': '0.01',
                    'description': 'Coordonnée Y mesurée',
                    'tolerance': '± 0.2 cm (± 2 mm)'
                },
                {
                    'name': 'z_value',
                    'label': 'Z (cm):',
                    'type': 'number',
                    'required': False,
                    'step': '0.01',
                    'description': 'Coordonnée Z mesurée',
                    'tolerance': '± 0.2 cm (± 2 mm)'
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


def test_quasar(
    operator: str,
    latence_status: str,
    latence_reason: Optional[str] = None,
    coord_correction: Optional[float] = None,
    x_value: Optional[float] = None,
    y_value: Optional[float] = None,
    z_value: Optional[float] = None,
    test_date: Optional[datetime] = None,
    notes: Optional[str] = None
):
    """Fonction wrapper pour exécuter le test QUASAR"""
    return QuasarTest().execute(
        operator=operator,
        latence_status=latence_status,
        latence_reason=latence_reason,
        coord_correction=coord_correction,
        x_value=x_value,
        y_value=y_value,
        z_value=z_value,
        test_date=test_date,
        notes=notes
    )
