"""
Generate DBML representation of the current database schema
"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    SafetySystemsTest,
    NiveauHeliumTest, MLCLeafJawTest, MVICTest, PIQTTest, MVICFenteV2Test,
    PositionTableV2Test, AlignementLaserTest, QuasarTest, IndiceQualityTest,
    MVCenterConfig
)
from sqlalchemy import inspect

def get_column_info(model_class):
    """Get column information from SQLAlchemy model"""
    mapper = inspect(model_class)
    columns = []
    for col in mapper.columns:
        col_type = str(col.type)
        if 'INTEGER' in col_type.upper():
            db_type = 'integer'
        elif 'FLOAT' in col_type.upper() or 'REAL' in col_type.upper():
            db_type = 'float'
        elif 'DATETIME' in col_type.upper():
            db_type = 'datetime'
        elif 'TEXT' in col_type.upper():
            db_type = 'text'
        else:
            db_type = 'varchar'
        
        attributes = []
        if col.primary_key:
            attributes.append('primary key')
        if not col.nullable and not col.primary_key:
            attributes.append('not null')
        
        attr_str = f" [{', '.join(attributes)}]" if attributes else ""
        columns.append(f"  {col.key} {db_type}{attr_str}")
    
    return columns

def generate_dbml():
    """Generate DBML for all test tables"""
    
    output = []
    
    # DAILY TESTS
    output.append("// ============================================================================")
    output.append("// DAILY TESTS")
    output.append("// ============================================================================\n")
    
    output.append("Table daily_safety_systems {")
    output.extend(get_column_info(SafetySystemsTest))
    output.append("}\n")
    
    # Check if result table exists
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'qc_tests.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_safety_systems_results'")
    if cursor.fetchone():
        output.append("Table daily_safety_systems_results {")
        output.append("  id integer [primary key]")
        output.append("  test_id integer [ref: > daily_safety_systems.id]")
        output.append("}\n")
    
    # WEEKLY TESTS
    output.append("// ============================================================================")
    output.append("// WEEKLY TESTS")
    output.append("// ============================================================================\n")
    
    output.append("Table weekly_niveau_helium {")
    output.extend(get_column_info(NiveauHeliumTest))
    output.append("}\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weekly_niveau_helium_results'")
    if cursor.fetchone():
        output.append("Table weekly_niveau_helium_results {")
        output.append("  id integer [primary key]")
        output.append("  test_id integer [ref: > weekly_niveau_helium.id]")
        output.append("}\n")
    
    output.append("Table weekly_mlc_leaf_jaw {")
    output.extend(get_column_info(MLCLeafJawTest))
    output.append("}\n")
    
    # MLC related tables
    mlc_related_tables = [
        'weekly_mlc_center_detection',
        'weekly_mlc_jaw_positions',
        'weekly_mlc_blade_positions',
        'weekly_mlc_blade_straightness'
    ]
    
    for table_name in mlc_related_tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        if cols:
            output.append(f"Table {table_name} {{")
            for col in cols:
                col_name = col[1]
                col_type = col[2].lower()
                is_pk = col[5] == 1
                
                if 'int' in col_type:
                    db_type = 'integer'
                elif 'real' in col_type or 'float' in col_type:
                    db_type = 'float'
                elif 'text' in col_type:
                    db_type = 'text'
                else:
                    db_type = 'varchar'
                
                attr = " [primary key]" if is_pk else ""
                
                # Add foreign key reference
                if col_name == 'mlc_test_id' and not is_pk:
                    attr = " [ref: > weekly_mlc_leaf_jaw.id]"
                
                output.append(f"  {col_name} {db_type}{attr}")
            output.append("}\n")
    
    output.append("Table weekly_mvic {")
    output.extend(get_column_info(MVICTest))
    output.append("}\n")
    
    cursor.execute("PRAGMA table_info(weekly_mvic_results)")
    cols = cursor.fetchall()
    if cols:
        output.append("Table weekly_mvic_results {")
        for col in cols:
            col_name = col[1]
            col_type = col[2].lower()
            is_pk = col[5] == 1
            
            if 'int' in col_type:
                db_type = 'integer'
            elif 'real' in col_type or 'float' in col_type:
                db_type = 'float'
            else:
                db_type = 'varchar'
            
            attr = " [primary key]" if is_pk else ""
            if col_name == 'test_id' and not is_pk:
                attr = " [ref: > weekly_mvic.id]"
            
            output.append(f"  {col_name} {db_type}{attr}")
        output.append("}\n")
    
    output.append("Table weekly_mvic_fente_v2 {")
    output.extend(get_column_info(MVICFenteV2Test))
    output.append("}\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weekly_mvic_fente_v2_results'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(weekly_mvic_fente_v2_results)")
        cols = cursor.fetchall()
        output.append("Table weekly_mvic_fente_v2_results {")
        for col in cols:
            col_name = col[1]
            col_type = col[2].lower()
            is_pk = col[5] == 1
            
            if 'int' in col_type:
                db_type = 'integer'
            elif 'real' in col_type or 'float' in col_type:
                db_type = 'float'
            else:
                db_type = 'varchar'
            
            attr = " [primary key]" if is_pk else ""
            if col_name == 'test_id' and not is_pk:
                attr = " [ref: > weekly_mvic_fente_v2.id]"
            
            output.append(f"  {col_name} {db_type}{attr}")
        output.append("}\n")
    
    output.append("Table weekly_piqt {")
    output.extend(get_column_info(PIQTTest))
    output.append("}\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weekly_piqt_results'")
    if cursor.fetchone():
        output.append("Table weekly_piqt_results {")
        output.append("  id integer [primary key]")
        output.append("  test_id integer [ref: > weekly_piqt.id]")
        output.append("}\n")
    
    # CONFIGURATION TABLES
    output.append("// ============================================================================")
    output.append("// CONFIGURATION TABLES")
    output.append("// ============================================================================\n")
    
    output.append("Table mlc_curie_mv_center_config {")
    output.extend(get_column_info(MVCenterConfig))
    output.append("}\n")
    
    # MONTHLY TESTS
    output.append("// ============================================================================")
    output.append("// MONTHLY TESTS")
    output.append("// ============================================================================\n")
    
    output.append("Table monthly_position_table_v2 {")
    output.extend(get_column_info(PositionTableV2Test))
    output.append("}\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_position_table_v2_results'")
    if cursor.fetchone():
        output.append("Table monthly_position_table_v2_results {")
        output.append("  id integer [primary key]")
        output.append("  test_id integer [ref: > monthly_position_table_v2.id]")
        output.append("}\n")
    
    output.append("Table monthly_alignement_laser {")
    output.extend(get_column_info(AlignementLaserTest))
    output.append("}\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_alignement_laser_results'")
    if cursor.fetchone():
        output.append("Table monthly_alignement_laser_results {")
        output.append("  id integer [primary key]")
        output.append("  test_id integer [ref: > monthly_alignement_laser.id]")
        output.append("}\n")
    
    output.append("Table monthly_quasar {")
    output.extend(get_column_info(QuasarTest))
    output.append("}\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_quasar_results'")
    if cursor.fetchone():
        output.append("Table monthly_quasar_results {")
        output.append("  id integer [primary key]")
        output.append("  test_id integer [ref: > monthly_quasar.id]")
        output.append("}\n")
    
    output.append("Table monthly_indice_quality {")
    output.extend(get_column_info(IndiceQualityTest))
    output.append("}\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_indice_quality_results'")
    if cursor.fetchone():
        output.append("Table monthly_indice_quality_results {")
        output.append("  id integer [primary key]")
        output.append("  test_id integer [ref: > monthly_indice_quality.id]")
        output.append("}\n")
    
    conn.close()
    
    return '\n'.join(output)

if __name__ == '__main__':
    print(generate_dbml())
