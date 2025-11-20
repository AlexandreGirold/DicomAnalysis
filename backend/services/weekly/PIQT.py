"""
Test PIQT (Philips Image Quality Test) - Parse HTML report
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monthly.base_test import BaseTest
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
import re


class PIQTTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_name="PIQT - Philips Image Quality Test",
            description="Parse et valide le rapport HTML PIQT"
        )
    
    def parse_html_file(self, file_path: str):
        """Parse le fichier HTML PIQT et extrait les valeurs"""
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        results = {
            'flood_field_uniformity': [],
            'spatial_linearity': [],
            'slice_profile': [],
            'spatial_resolution': []
        }
        
        # Find all tables with ANY border attribute
        tables = soup.find_all('table')
        print(f"[PIQT DEBUG] Found {len(tables)} total tables")
        tables_with_border = soup.find_all('table', {'border': '1'})
        print(f"[PIQT DEBUG] Found {len(tables_with_border)} tables with border=1")
        
        # Find section headers in ALL text
        all_text = soup.get_text()
        print(f"[PIQT DEBUG] Searching for section headers in text...")
        if 'Flood Field Uniformity' in all_text:
            print("[PIQT DEBUG] Found: Flood Field Uniformity")
        if 'Spatial Linearity' in all_text:
            print("[PIQT DEBUG] Found: Spatial Linearity")
        if 'Slice Profile' in all_text:
            print("[PIQT DEBUG] Found: Slice Profile")
        if 'Spatial Resolution' in all_text:
            print("[PIQT DEBUG] Found: Spatial Resolution")
        
        current_section = None
        
        # Find section headers
        for span in soup.find_all('span'):
            text = span.get_text(strip=True)
            if 'Flood Field Uniformity' in text:
                current_section = 'flood_field_uniformity'
            elif 'Spatial Linearity' in text:
                current_section = 'spatial_linearity'
            elif 'Slice Profile' in text:
                current_section = 'slice_profile'
            elif 'Spatial Resolution' in text:
                current_section = 'spatial_resolution'
        
        # Parse tables - use tables_with_border if they exist, otherwise all tables
        tables_to_parse = tables_with_border if tables_with_border else tables
        print(f"[PIQT DEBUG] Will parse {len(tables_to_parse)} tables")
        
        # Track which section we're in by finding span headers before tables
        current_section = None
        section_counters = {
            'flood_field_uniformity': 0,
            'spatial_linearity': 0,
            'slice_profile': 0,
            'spatial_resolution': 0
        }
        
        # Track if we've already counted this table for the current section
        table_counted = {
            'flood_field_uniformity': set(),
            'spatial_linearity': set(),
            'slice_profile': set(),
            'spatial_resolution': set()
        }
        
        # Track table counters per section (to identify different scans)
        for table_idx, table in enumerate(tables_to_parse):
            # Check if there's a section header before this table
            prev_element = table.find_previous('span')
            if prev_element:
                text = prev_element.get_text(strip=True)
                if 'Flood Field Uniformity' in text:
                    current_section = 'flood_field_uniformity'
                elif 'Spatial Linearity' in text:
                    current_section = 'spatial_linearity'
                elif 'Slice Profile' in text:
                    current_section = 'slice_profile'
                elif 'Spatial Resolution' in text:
                    current_section = 'spatial_resolution'
            
            rows = table.find_all('tr')
            print(f"[PIQT DEBUG] Table {table_idx+1} has {len(rows)} rows (Section: {current_section})")
            
            # Try to find scan name in this table
            scan_name = None
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    first_cell = cells[0].get_text(strip=True)
                    if first_cell == 'Scan_Name':
                        # Get all scan names from this row
                        scan_names = []
                        for i in range(1, len(cells)):
                            name = cells[i].get_text(strip=True)
                            if name and name not in scan_names:
                                scan_names.append(name)
                        scan_name = ', '.join(scan_names) if scan_names else None
                        break
            
            for row in rows:
                cells = row.find_all('td')
                if not cells:
                    continue
                
                # Get first cell text (parameter name)
                param_name = cells[0].get_text(strip=True)
                print(f"[PIQT DEBUG] Row parameter: '{param_name}' (cells: {len(cells)})")
                
                # Extract values based on parameter
                if 'Nema S/N (B)' in param_name or 'Nema_Int_Unif' in param_name:
                    # Flood Field Uniformity - increment counter only once per table
                    if table_idx not in table_counted['flood_field_uniformity']:
                        section_counters['flood_field_uniformity'] += 1
                        table_counted['flood_field_uniformity'].add(table_idx)
                    
                    values = self._extract_values_from_row(cells)
                    if values:
                        results['flood_field_uniformity'].append({
                            'parameter': param_name,
                            'table_number': section_counters['flood_field_uniformity'],
                            'scan_name': scan_name,
                            'values': values
                        })
                
                elif 'nema_perc_dif' in param_name:
                    # Spatial Linearity - increment counter only once per table
                    if table_idx not in table_counted['spatial_linearity']:
                        section_counters['spatial_linearity'] += 1
                        table_counted['spatial_linearity'].add(table_idx)
                    
                    values = self._extract_values_from_row(cells)
                    if values:
                        results['spatial_linearity'].append({
                            'parameter': param_name,
                            'table_number': section_counters['spatial_linearity'],
                            'values': values
                        })
                
                elif 'Nema_FWHM' in param_name or 'Nema_Slice_int' in param_name:
                    # Slice Profile - increment counter only once per table
                    if table_idx not in table_counted['slice_profile']:
                        section_counters['slice_profile'] += 1
                        table_counted['slice_profile'].add(table_idx)
                    
                    values = self._extract_values_from_row(cells)
                    if values:
                        results['slice_profile'].append({
                            'parameter': param_name,
                            'table_number': section_counters['slice_profile'],
                            'values': values
                        })
                
                elif 'Nema_Hor_pxl_size' in param_name or 'Nema_Ver_pxl_size' in param_name:
                    # Spatial Resolution - increment counter only once per table
                    if table_idx not in table_counted['spatial_resolution']:
                        section_counters['spatial_resolution'] += 1
                        table_counted['spatial_resolution'].add(table_idx)
                    
                    values = self._extract_values_from_row(cells)
                    if values:
                        results['spatial_resolution'].append({
                            'parameter': param_name,
                            'table_number': section_counters['spatial_resolution'],
                            'values': values
                        })
        
        return results
    
    def _extract_values_from_row(self, cells):
        """Extrait les valeurs et critères d'une ligne de tableau"""
        values = []
        i = 1  # Skip first cell (parameter name)
        
        while i < len(cells):
            cell_text = cells[i].get_text(strip=True)
            
            # Try to parse as float (measured value)
            try:
                measured = float(cell_text)
                criterion = None
                
                # Next cell might be criterion
                if i + 1 < len(cells):
                    next_text = cells[i + 1].get_text(strip=True)
                    if 'C' in next_text or '<' in next_text or '>' in next_text:
                        criterion = next_text
                        i += 1  # Skip criterion cell
                
                values.append({
                    'measured': measured,
                    'criterion': criterion
                })
                
                i += 1
            except ValueError:
                i += 1
        
        return values
    
    def _validate_criterion(self, measured: float, criterion: str) -> tuple:
        """Valide si une valeur mesurée respecte le critère"""
        if not criterion:
            return True, "No criterion"
        
        criterion = criterion.strip()
        
        # Pattern: C > value
        match = re.match(r'C\s*>\s*([\d.]+)', criterion)
        if match:
            threshold = float(match.group(1))
            passed = measured > threshold
            return passed, f"Mesuré: {measured}, Requis: > {threshold}"
        
        # Pattern: C < value
        match = re.match(r'C\s*<\s*([\d.]+)', criterion)
        if match:
            threshold = float(match.group(1))
            passed = measured < threshold
            return passed, f"Mesuré: {measured}, Requis: < {threshold}"
        
        # Pattern: C min - max
        match = re.match(r'C\s*([\d.]+)\s*-\s*([\d.]+)', criterion)
        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            passed = min_val <= measured <= max_val
            return passed, f"Measured: {measured}, Range: {min_val} - {max_val}"
        
        return None, f"Unknown criterion format: {criterion}"
    
    def execute(
        self,
        operator: str,
        html_file_path: str,
        test_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ):
        """
        Exécute le test PIQT
        
        Args:
            operator: Nom de l'opérateur
            html_file_path: Chemin vers le fichier HTML PIQT
            test_date: Date du test
            notes: Notes additionnelles
        """
        self.set_test_info(operator, test_date)
        
        # Inputs
        self.add_input("operator", operator, "text")
        self.add_input("html_file", os.path.basename(html_file_path), "text")
        if notes:
            self.add_input("notes", notes, "text")
        
        # Parse HTML file
        try:
            parsed_data = self.parse_html_file(html_file_path)
        except Exception as e:
            self.add_result(
                name="Erreur de parsing",
                value=str(e),
                status="FAIL",
                unit="",
                tolerance="N/A"
            )
            self.calculate_overall_result()
            return self.to_dict()
        
        # Validate Flood Field Uniformity
        for item in parsed_data['flood_field_uniformity']:
            param = item['parameter']
            table_num = item.get('table_number', 0)
            scan_name = item.get('scan_name', '')
            
            # Create a prefix based on table number
            prefix = f"FFU-{table_num}"
            if scan_name:
                prefix += f" ({scan_name})"
            
            for idx, value_data in enumerate(item['values']):
                measured = value_data['measured']
                criterion = value_data['criterion']
                
                if criterion:
                    passed, details = self._validate_criterion(measured, criterion)
                    status = "PASS" if passed else "FAIL" if passed is not None else "INFO"
                    
                    self.add_result(
                        name=f"{prefix} - {param} #{idx+1}",
                        value=measured,
                        status=status,
                        unit="",
                        tolerance=details
                    )
        
        # Validate Spatial Linearity
        for item in parsed_data['spatial_linearity']:
            param = item['parameter']
            for idx, value_data in enumerate(item['values']):
                measured = value_data['measured']
                criterion = value_data['criterion']
                
                if criterion:
                    passed, details = self._validate_criterion(measured, criterion)
                    status = "PASS" if passed else "FAIL" if passed is not None else "INFO"
                    
                    self.add_result(
                        name=f"Spatial Linearity - {param} #{idx+1}",
                        value=measured,
                        status=status,
                        unit="%",
                        tolerance=details
                    )
        
        # Validate Slice Profile
        for item in parsed_data['slice_profile']:
            param = item['parameter']
            for idx, value_data in enumerate(item['values']):
                measured = value_data['measured']
                criterion = value_data['criterion']
                
                if criterion:
                    passed, details = self._validate_criterion(measured, criterion)
                    status = "PASS" if passed else "FAIL" if passed is not None else "INFO"
                    
                    self.add_result(
                        name=f"Slice Profile - {param} #{idx+1}",
                        value=measured,
                        status=status,
                        unit="mm",
                        tolerance=details
                    )
        
        # Validate Spatial Resolution
        for item in parsed_data['spatial_resolution']:
            param = item['parameter']
            for idx, value_data in enumerate(item['values']):
                measured = value_data['measured']
                criterion = value_data['criterion']
                
                if criterion:
                    passed, details = self._validate_criterion(measured, criterion)
                    status = "PASS" if passed else "FAIL" if passed is not None else "INFO"
                    
                    self.add_result(
                        name=f"Spatial Resolution - {param} #{idx+1}",
                        value=measured,
                        status=status,
                        unit="mm",
                        tolerance=details
                    )
        
        self.calculate_overall_result()
        return self.to_dict()
    
    def get_form_data(self):
        """Retourne les données pour générer le formulaire"""
        return {
            'title': 'Test PIQT',
            'description': 'Parse et valide le rapport HTML PIQT (Philips Image Quality Test)',
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
                    'name': 'html_file',
                    'label': 'Fichier HTML PIQT:',
                    'type': 'file',
                    'required': True,
                    'accept': '.html,.htm',
                    'description': 'Sélectionnez le fichier HTML du rapport PIQT'
                },
                {
                    'name': 'notes',
                    'label': 'Notes:',
                    'type': 'textarea',
                    'required': False,
                    'description': 'Notes et observations supplémentaires'
                }
            ],
            'category': 'weekly',
            'file_upload': True
        }


def test_piqt(
    operator: str,
    html_file_path: str,
    test_date: Optional[datetime] = None,
    notes: Optional[str] = None
):
    """Fonction wrapper pour exécuter le test PIQT"""
    return PIQTTest().execute(
        operator=operator,
        html_file_path=html_file_path,
        test_date=test_date,
        notes=notes
    )
