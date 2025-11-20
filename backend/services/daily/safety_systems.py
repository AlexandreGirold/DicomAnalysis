"""
ANSM Daily Safety Systems Test
ANSM - 1.1, 1.5 and TG284 Requirements
Procedure ENNOV: IC - 015013

Manual verification test for safety systems including:
- Beam status indicators (audio and visual)
- Beam interruption functionality
- Door interlocks
- Patient monitoring systems
- Table emergency stop
"""
import sys
import os
# Add services directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from basic_tests.base_test import BaseTest
from datetime import datetime
from typing import Optional


class SafetySystemsTest(BaseTest):
    """
    Daily safety systems verification test
    Tests all safety-critical systems including indicators, interlocks, and patient monitoring
    """
    
    def __init__(self):
        super().__init__(
            test_name="Systèmes de Sécurité",
            description="ANSM - Vérification Quotidienne des Systèmes de Sécurité"
        )
    
    def execute(
        self, 
        operator: str,
        accelerator_warmup: str,
        audio_indicator: str,
        visual_indicators_console: str,
        visual_indicator_room: str,
        beam_interruption: str,
        door_interlocks: str,
        camera_monitoring: str,
        patient_communication: str,
        table_emergency_stop: str,
        test_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ):
        """
        Execute the safety systems verification test
        
        Args:
            operator: Name of the operator performing the test
            accelerator_warmup: Status of accelerator warmup (PASS/FAIL/SKIP)
            audio_indicator: ANSM 1.1 - Audio beam indicator (PASS/FAIL/SKIP)
            visual_indicators_console: ANSM 1.1 - Visual indicators at console (PASS/FAIL/SKIP)
            visual_indicator_room: ANSM 1.1 - Visual indicator in treatment room (PASS/FAIL/SKIP)
            beam_interruption: Beam interruption functionality (PASS/FAIL/SKIP)
            door_interlocks: Door closing interlocks (PASS/FAIL/SKIP)
            camera_monitoring: ANSM 1.5 - Camera monitoring systems (PASS/FAIL/SKIP)
            patient_communication: ANSM 1.5 - Patient communication systems (PASS/FAIL/SKIP)
            table_emergency_stop: TG284 - Table emergency stop button (PASS/FAIL/SKIP)
            test_date: Date of the test (defaults to current date)
            notes: Optional notes or comments
        
        Returns:
            dict: Test results
        """
        self.set_test_info(operator, test_date)
        
        self.add_input("operator", operator, "text")
        if notes:
            self.add_input("notes", notes, "text")
        
        # ===== Accelerator Warmup =====
        self.add_result(
            name="accelerator_warmup",
            value="Completed" if accelerator_warmup.upper() == "PASS" else "Not Completed",
            status=accelerator_warmup.upper(),
            tolerance="Must complete warmup beam",
            details="Patient AQUA, OUTPUT (ID=UNITY_Aqua_OUTPUT) - Beam '10 - chauffe' in AQ mode"
        )
        
        # ===== ANSM 1.1 - Audio Indicator =====
        self.add_result(
            name="audio_beam_indicator",
            value="Functional" if audio_indicator.upper() == "PASS" else "Non-Functional",
            status=audio_indicator.upper(),
            tolerance="Functional",
            details="[ANSM - 1.1] Regular beep during UM delivery at console control box"
        )
        
        # ===== ANSM 1.1 - Visual Indicators at Console =====
        console_checks = [
            "(1) Control box LED: Green → Yellow during beam",
            "(2) NRT screen: 'Radiation On' with UM countdown",
            "(3) Bunker door light: Green (powered) → Red (emission)"
        ]
        self.add_result(
            name="visual_indicators_console",
            value="All Functional" if visual_indicators_console.upper() == "PASS" else "Issues Detected",
            status=visual_indicators_console.upper(),
            tolerance="All Functional",
            details=f"[ANSM - 1.1] Console indicators:\n" + "\n".join(console_checks)
        )
        
        # ===== ANSM 1.1 - Visual Indicator in Treatment Room =====
        self.add_result(
            name="visual_indicator_room",
            value="Functional" if visual_indicator_room.upper() == "PASS" else "Non-Functional",
            status=visual_indicator_room.upper(),
            tolerance="Functional",
            details="[ANSM - 1.1] Treatment room light: Green (powered) → Red (emission) - Verified via cameras"
        )
        
        # ===== Beam Interruption =====
        interrupt_procedure = [
            "Patient AQUA, OUTPUT (ID=UNITY_Aqua_OUTPUT)",
            "Beam '11 - interrupt' in AQ mode",
            "Yellow interruption button activated at console",
            "Verify: Beam stops and restarts with correct remaining UM"
        ]
        self.add_result(
            name="beam_interruption",
            value="Functional" if beam_interruption.upper() == "PASS" else "Non-Functional",
            status=beam_interruption.upper(),
            tolerance="Functional",
            details="Beam interruption test:\n" + "\n".join(interrupt_procedure)
        )
        
        # ===== Door Interlocks =====
        door_checks = [
            "(1) Cannot close bunker door without 'last out' button",
            "(2) Door error prevents beam delivery",
            "(3) 'Ring out' error if not activated before closing"
        ]
        self.add_result(
            name="door_interlocks",
            value="All Functional" if door_interlocks.upper() == "PASS" else "Issues Detected",
            status=door_interlocks.upper(),
            tolerance="All Functional",
            details="Door closing safety devices:\n" + "\n".join(door_checks)
        )
        
        # ===== ANSM 1.5 - Camera Monitoring =====
        camera_checks = [
            "(1) Patient monitoring cameras functional with sufficient quality",
            "(2) Rear accelerator view camera functional"
        ]
        self.add_result(
            name="camera_monitoring",
            value="All Functional" if camera_monitoring.upper() == "PASS" else "Issues Detected",
            status=camera_monitoring.upper(),
            tolerance="All Functional",
            details="[ANSM - 1.5] Visual surveillance systems:\n" + "\n".join(camera_checks)
        )
        
        # ===== ANSM 1.5 - Patient Communication =====
        comm_checks = [
            "(3) Patient call button functional",
            "(4) Microphones and headset: Clear and audible communication"
        ]
        self.add_result(
            name="patient_communication",
            value="All Functional" if patient_communication.upper() == "PASS" else "Issues Detected",
            status=patient_communication.upper(),
            tolerance="All Functional",
            details="[ANSM - 1.5] Patient communication systems:\n" + "\n".join(comm_checks)
        )
        
        # ===== TG284 - Table Emergency Stop =====
        table_checks = [
            "Engage table safety at control panel",
            "Verify: Red indicator light activates",
            "Verify: Table movement button inactive immediately",
            "Move table manually",
            "Perform motor reset"
        ]
        self.add_result(
            name="table_emergency_stop",
            value="Functional" if table_emergency_stop.upper() == "PASS" else "Non-Functional",
            status=table_emergency_stop.upper(),
            tolerance="Functional",
            details="[TG284] Table emergency stop control:\n" + "\n".join(table_checks)
        )
        
        # Calculate overall result
        self.calculate_overall_result()
        
        return self.to_dict()
    
    def get_form_data(self):
        """
        Get the form structure for frontend implementation
        
        Returns:
            dict: Form configuration
        """
        return {
            'title': 'ANSM - Vérification Quotidienne des Systèmes de Sécurité',
            'description': 'Vérification manuelle de tous les systèmes critiques de sécurité (ANSM 1.1, 1.5, TG284)',
            'fields': [
                {
                    'name': 'test_date',
                    'label': 'Date:',
                    'type': 'date',
                    'required': True,
                    'default': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'name': 'operator',
                    'label': 'Opérateur:',
                    'type': 'text',
                    'required': True,
                    'placeholder': 'Nom de l\'opérateur'
                },
                {
                    'name': 'accelerator_warmup',
                    'label': 'Chauffe de l\'accélérateur',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': 'Patient AQUA, OUTPUT (ID=UNITY_Aqua_OUTPUT) - Faisceau "10 - chauffe" en mode AQ'
                },
                {
                    'name': 'audio_indicator',
                    'label': '[ANSM - 1.1] Indicateur sonore de l\'état du faisceau',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': 'Bip régulier pendant la délivrance des UM au pupitre',
                    'tolerance': 'Fonctionnel'
                },
                {
                    'name': 'visual_indicators_console',
                    'label': '[ANSM - 1.1] Indicateurs et Voyants lumineux au pupitre',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': '(1) LED boitier: vert→jaune | (2) "Radiation On" sur NRT | (3) Porte bunker: vert→rouge',
                    'tolerance': 'Fonctionnels'
                },
                {
                    'name': 'visual_indicator_room',
                    'label': '[ANSM - 1.1] Voyant lumineux dans la salle de traitement',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': 'Voyant dans la salle: vert→rouge (vérifier avec caméras)',
                    'tolerance': 'Fonctionnel'
                },
                {
                    'name': 'beam_interruption',
                    'label': 'Interruption de faisceau',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': 'Faisceau "11 - interrupt" | Bouton jaune | Vérifier interruption et redémarrage avec UM restant',
                    'tolerance': 'Fonctionnel'
                },
                {
                    'name': 'door_interlocks',
                    'label': 'Dispositifs de fermeture des portes',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': '(1) Porte ne ferme pas sans "dernier sorti" | (2) Erreur porte empêche faisceau | (3) Erreur "Ring out"',
                    'tolerance': 'Fonctionnels'
                },
                {
                    'name': 'camera_monitoring',
                    'label': '[ANSM - 1.5] Systèmes de surveillance visuelle du patient',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': '(1) Caméras fonctionnelles | (2) Vue arrière accélérateur',
                    'tolerance': 'Fonctionnels'
                },
                {
                    'name': 'patient_communication',
                    'label': '[ANSM - 1.5] Systèmes de communication avec le patient',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': '(3) Poire d\'appel | (4) Micros et casque: communication claire',
                    'tolerance': 'Fonctionnels'
                },
                {
                    'name': 'table_emergency_stop',
                    'label': '[TG284] Contrôle du bouton d\'arrêt de la table',
                    'type': 'select',
                    'required': True,
                    'options': ['PASS', 'FAIL', 'SKIP'],
                    'details': 'Sécurité table | Voyant rouge | Bouton inactif | Mouvement manuel | Reset motor',
                    'tolerance': 'Fonctionnel'
                },
                {
                    'name': 'notes',
                    'label': 'Notes / Commentaires:',
                    'type': 'textarea',
                    'required': False,
                    'placeholder': 'Observations, anomalies détectées...'
                }
            ],
            'tolerance': 'All safety systems must be functional',
            'category': 'daily'
        }


# Convenience function for standalone use
def test_safety_systems(
    operator: str,
    accelerator_warmup: str,
    audio_indicator: str,
    visual_indicators_console: str,
    visual_indicator_room: str,
    beam_interruption: str,
    door_interlocks: str,
    camera_monitoring: str,
    patient_communication: str,
    table_emergency_stop: str,
    test_date: Optional[datetime] = None,
    notes: Optional[str] = None
):
    """
    Standalone function to test safety systems
    
    Args:
        operator: Name of the operator
        accelerator_warmup: Status (PASS/FAIL/SKIP)
        audio_indicator: Status (PASS/FAIL/SKIP)
        visual_indicators_console: Status (PASS/FAIL/SKIP)
        visual_indicator_room: Status (PASS/FAIL/SKIP)
        beam_interruption: Status (PASS/FAIL/SKIP)
        door_interlocks: Status (PASS/FAIL/SKIP)
        camera_monitoring: Status (PASS/FAIL/SKIP)
        patient_communication: Status (PASS/FAIL/SKIP)
        table_emergency_stop: Status (PASS/FAIL/SKIP)
        test_date: Date of test
        notes: Optional notes
    
    Returns:
        dict: Test results
    """
    test = SafetySystemsTest()
    return test.execute(
        operator=operator,
        accelerator_warmup=accelerator_warmup,
        audio_indicator=audio_indicator,
        visual_indicators_console=visual_indicators_console,
        visual_indicator_room=visual_indicator_room,
        beam_interruption=beam_interruption,
        door_interlocks=door_interlocks,
        camera_monitoring=camera_monitoring,
        patient_communication=patient_communication,
        table_emergency_stop=table_emergency_stop,
        test_date=test_date,
        notes=notes
    )
