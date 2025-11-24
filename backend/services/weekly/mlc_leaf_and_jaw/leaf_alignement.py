"""
Analyse d'Alignement des Lames

Utilise la détection des bords de champ pour trouver les blocs de lames MLC individuels,
puis calcule les lignes médianes entre les lames adjacentes pour déterminer les angles d'alignement.
L'objectif est de trouver le milieu entre chaque lame individuelle et de calculer :
- Angle Moyen du Banc de Lames Y1
- Angle Moyen du Banc de Lames Y2
"""
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web server
import matplotlib.pyplot as plt
import pydicom
import sys
from pathlib import Path


class LeafAlignmentAnalyzer:
    def __init__(self):
        # Paramètres de détection (identiques à field_edge_detection.py)
        self.tolerance_threshold = 127  # Seuil binaire à 50%
        self.tolerance_kernel_size = 3  # Noyau pour les opérations morphologiques
        self.min_area = 200  # Surface minimale du contour en pixels
        self.merge_distance_px = 40  # Distance pour fusionner les contours proches
        
    def load_dicom_image(self, filepath):
        """Charger l'image DICOM et extraire les métadonnées"""
        try:
            ds = pydicom.dcmread(filepath)
            image_array = ds.pixel_array.astype(np.float32)
            
            # Extraire les paramètres géométriques
            SAD = float(ds.RadiationMachineSAD)
            SID = float(ds.RTImageSID)
            scaling_factor = SAD / SID
            
            # Extraire l'espacement des pixels
            pixel_spacing = ds.ImagePlanePixelSpacing
            pixel_spacing_x = float(pixel_spacing[0])
            pixel_spacing_y = float(pixel_spacing[1])
            
            # Extraire la position de l'image RT
            rt_image_position = ds.RTImagePosition
            rt_image_pos_x = float(rt_image_position[0])
            rt_image_pos_y = float(rt_image_position[1])
            
            metadata = {
                'SAD': SAD,
                'SID': SID,
                'scaling_factor': scaling_factor,
                'pixel_spacing_x': pixel_spacing_x,
                'pixel_spacing_y': pixel_spacing_y,
                'rt_image_pos_x': rt_image_pos_x,
                'rt_image_pos_y': rt_image_pos_y
            }
            
            return image_array, ds, metadata
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None, None
    
    def preprocess_image(self, image_array):
        """
        Prétraiter l'image avec normalisation, CLAHE et netteté laplacienne.
        Utilise le même prétraitement que field_edge_detection.py
        """
        # Normaliser dans la plage 0-1
        normalized_img = (image_array - image_array.min()) / (image_array.max() - image_array.min())
        
        # Convertir en 8 bits pour le traitement OpenCV
        img_8bit = cv2.normalize(normalized_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Appliquer CLAHE pour l'amélioration du contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(img_8bit)
        
        # Appliquer la netteté laplacienne (du notebook)
        laplacian_kernel = np.array([[0, -1, 0],
                                     [-1, 5, -1],
                                     [0, -1, 0]], dtype=np.float32)
        laplacian_sharpened = cv2.filter2D(clahe_img, -1, laplacian_kernel)
        laplacian_sharpened = np.clip(laplacian_sharpened, 0, 255).astype(np.uint8)
        
        return img_8bit, clahe_img, laplacian_sharpened
    
    def detect_field_contours(self, clahe_img):
        """
        Détecter les contours du champ en utilisant la même méthode que field_edge_detection.py
        """
        # Créer une image binaire
        _, binary_image = cv2.threshold(clahe_img, self.tolerance_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Appliquer des opérations morphologiques pour nettoyer les régions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                          (self.tolerance_kernel_size, self.tolerance_kernel_size))
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
        binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
        
        # Trouver les contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > self.min_area]
        
        return contours, binary_image
    
    def merge_nearby_contours(self, contours, binary_image):
        """
        Fusionner les contours qui sont proches les uns des autres.
        Utilise la même méthode que field_edge_detection.py
        """
        if len(contours) <= 1:
            return contours
        
        # Obtenir les rectangles englobants et les centres pour tous les contours
        contour_data = []
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            cx = x + w / 2
            cy = y + h / 2
            contour_data.append({
                'index': i,
                'contour': contour,
                'bbox': (x, y, w, h),
                'center': (cx, cy),
                'merged': False
            })
        
        merged_contours = []
        
        for i, data_i in enumerate(contour_data):
            if data_i['merged']:
                continue
                
            close_contours = [data_i['contour']]
            data_i['merged'] = True
            
            for j, data_j in enumerate(contour_data):
                if i == j or data_j['merged']:
                    continue
                    
                # Calculer la distance entre les centres
                dx = data_i['center'][0] - data_j['center'][0]
                dy = data_i['center'][1] - data_j['center'][1]
                distance = np.sqrt(dx**2 + dy**2)
                
                # Vérifier si alignés verticalement (même rangée)
                vertical_alignment = abs(dy) < 15
                
                # Fusionner si proches et alignés
                if distance < self.merge_distance_px and vertical_alignment:
                    close_contours.append(data_j['contour'])
                    data_j['merged'] = True
            
            # Fusionner plusieurs contours proches
            if len(close_contours) > 1:
                mask = np.zeros(binary_image.shape, dtype=np.uint8)
                for contour in close_contours:
                    cv2.fillPoly(mask, [contour], 255)
                
                merged_contours_temp, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if merged_contours_temp:
                    merged_contours.append(merged_contours_temp[0])
            else:
                merged_contours.append(close_contours[0])
        
        return merged_contours
    
    def find_leaf_midlines(self, contours):
        """
        Trouver les lignes médianes entre les blocs de lames adjacents
        """
        if len(contours) < 2:
            return [], []
        
        # Obtenir les boîtes englobantes et trier par coordonnée x (de gauche à droite)
        leaf_boxes = []
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            leaf_boxes.append({
                'index': i,
                'contour': contour,
                'bbox': (x, y, w, h),
                'center_x': x + w/2,
                'center_y': y + h/2,
                'left_edge': x,
                'right_edge': x + w,
                'top_edge': y,
                'bottom_edge': y + h
            })
        
        # Trier par coordonnée x (de gauche à droite)
        leaf_boxes.sort(key=lambda box: box['center_x'])
        
        # Trouver les lignes médianes entre les lames adjacentes
        midlines = []
        for i in range(len(leaf_boxes) - 1):
            left_leaf = leaf_boxes[i]
            right_leaf = leaf_boxes[i + 1]
            
            # Calculer la coordonnée x médiane entre les lames adjacentes
            middle_x = (left_leaf['right_edge'] + right_leaf['left_edge']) / 2
            
            # Déterminer la plage y (région de chevauchement entre les deux lames)
            top_y = max(left_leaf['top_edge'], right_leaf['top_edge'])
            bottom_y = min(left_leaf['bottom_edge'], right_leaf['bottom_edge'])
            
            if bottom_y > top_y:  # Chevauchement valide
                midlines.append({
                    'x': middle_x,
                    'y_start': top_y,
                    'y_end': bottom_y,
                    'center_y': (top_y + bottom_y) / 2,
                    'length': bottom_y - top_y,
                    'angle': 90.0,  # Supposer une verticale parfaite pour l'instant
                    'left_leaf_idx': i,
                    'right_leaf_idx': i + 1
                })
        
        return midlines, leaf_boxes
    
    def calculate_midline_angles(self, midlines, processed_img):
        """
        Calculer les angles réels des lignes médianes en analysant les données d'image le long de chaque ligne médiane
        """
        for midline in midlines:
            x = int(midline['x'])
            y_start = int(midline['y_start'])
            y_end = int(midline['y_end'])
            
            # Extraire les valeurs de pixels le long de la ligne médiane
            if y_end > y_start and 0 <= x < processed_img.shape[1]:
                # Obtenir une petite fenêtre autour de la ligne médiane pour détecter le bord réel
                window_width = 5
                x_start = max(0, x - window_width)
                x_end = min(processed_img.shape[1], x + window_width)
                
                # Extraire la région autour de la ligne médiane
                region = processed_img[y_start:y_end, x_start:x_end]
                
                if region.size > 0:
                    # Trouver la ligne la plus verticale dans cette région en utilisant la détection des bords
                    edges = cv2.Canny(region, 50, 150)
                    
                    # Utiliser HoughLines pour détecter la ligne la plus proéminente
                    lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=int(region.shape[0] * 0.3))
                    
                    if lines is not None and len(lines) > 0:
                        # Trouver la ligne la plus verticale (la plus proche de 90 degrés)
                        best_angle = 90.0
                        for line in lines:
                            rho, theta = line[0]
                            angle_deg = np.degrees(theta)
                            
                            # Convertir en angle depuis la verticale (90 degrés est une verticale parfaite)
                            if angle_deg > 90:
                                angle_from_vertical = 180 - angle_deg
                            else:
                                angle_from_vertical = angle_deg
                            
                            # Convertir en angle réel (90° est une verticale parfaite)
                            actual_angle = 90 + (angle_from_vertical - 90)
                            
                            # Conserver l'angle le plus proche de la verticale
                            if abs(actual_angle - 90) < abs(best_angle - 90):
                                best_angle = actual_angle
                        
                        midline['angle'] = best_angle
                    else:
                        # Par défaut 90 degrés si aucune ligne détectée
                        midline['angle'] = 90.0
                else:
                    midline['angle'] = 90.0
            else:
                midline['angle'] = 90.0
        
        return [midline['angle'] for midline in midlines]
    
    def classify_midlines_by_banks(self, midlines, image_height):
        """
        Classer les lignes médianes en bancs Y1 (bas) et Y2 (haut)
        """
        y1_midlines = []  # Banc inférieur
        y2_midlines = []  # Banc supérieur
        
        # Utiliser le centre de l'image comme ligne de division
        center_y = image_height / 2
        
        for midline in midlines:
            if midline['center_y'] > center_y:
                y1_midlines.append(midline)
            else:
                y2_midlines.append(midline)
        
        return y1_midlines, y2_midlines
    
    # Visualization removed - values only for monthly trend analysis
    
    def process_image(self, filepath):
        """Traiter une seule image DICOM pour analyser l'alignement des lames
        filepath: Chemin vers le DICOM
        returns: Dictionnaire avec les résultats d'analyse et les métadonnées
        """
        print(f"\n{'='*60}") # ===========================
        print(f"Analyse d'alignement des lames : {Path(filepath).name}")
        print(f"{'='*60}")
        
        image_array, ds, metadata = self.load_dicom_image(filepath)
        if image_array is None:
            return None
        
        # Prétraiter l'image (identique à field_edge_detection.py)
        img_8bit, clahe_img, laplacian_sharpened = self.preprocess_image(image_array)
        print("Prétraitement : Normalisation → CLAHE → Netteté Laplacienne")
        
        # Détecter les contours des blocs de lames (utilisant l'approche de détection des bords de champ)
        contours, binary_image = self.detect_field_contours(clahe_img)
        print(f"Contours initiaux trouvés : {len(contours)}")
        
        # Fusionner les contours proches (identique à field_edge_detection.py)
        merged_contours = self.merge_nearby_contours(contours, binary_image)
        final_contours = [c for c in merged_contours if cv2.contourArea(c) > self.min_area]
        print(f"Après fusion : {len(final_contours)} blocs de lames détectés")
        
        # Trouver les lignes médianes entre les lames adjacentes
        midlines, leaf_boxes = self.find_leaf_midlines(final_contours)
        print(f"Trouvé {len(midlines)} lignes médianes entre les lames adjacentes")
        
        angles = self.calculate_midline_angles(midlines, clahe_img)
        
        # Classify midlines into Y1 and Y2 banks
        y1_midlines, y2_midlines = self.classify_midlines_by_banks(midlines, image_array.shape[0])
        print(f"Y1 (bas): {len(y1_midlines)} midlines")
        print(f"Y2 (haut): {len(y2_midlines)} midlines")
        
        # Calculer les angles moyens
        y1_angles = [midline['angle'] for midline in y1_midlines]
        y2_angles = [midline['angle'] for midline in y2_midlines]
        
        y1_avg_angle = np.mean(y1_angles) if y1_angles else 0
        y2_avg_angle = np.mean(y2_angles) if y2_angles else 0
        
        print(f"\nRÉSULTAT D'ALIGNEMENT DES LAMES :")
        print(f"Banc de lames : Moyenne des angles (°)")
        print(f"Y1           {y1_avg_angle:.2f}")
        print(f"Y2           {y2_avg_angle:.2f}")
        
        print(f"{'='*60}\n")
        
        return {
            'y1_avg_angle': y1_avg_angle,
            'y2_avg_angle': y2_avg_angle,
            'y1_midlines': y1_midlines,
            'y2_midlines': y2_midlines,
            'total_midlines': len(midlines),
            'total_leaf_blocks': len(final_contours),
            'metadata': metadata
        }


def main():
    """Point d'entrée principal pour l'exécution autonome"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage : python leaf_alignement.py <fichier_dicom>")
        sys.exit(1)
    
    analyzer = LeafAlignmentAnalyzer()
    result = analyzer.process_image(sys.argv[1])
    
    if result:
        print(f"✅ Analyse d'alignement des lames terminée avec succès")
        print(f"   Angle moyen Y1 : {result['y1_avg_angle']:.2f}°")
        print(f"   Angle moyen Y2 : {result['y2_avg_angle']:.2f}°")
        print(f"   Total lignes médianes : {result['total_midlines']}")
        print(f"   Total blocs de lames : {result['total_leaf_blocks']}")
    else:
        print("❌ Échec de l'analyse d'alignement des lames")


if __name__ == "__main__":
    main()