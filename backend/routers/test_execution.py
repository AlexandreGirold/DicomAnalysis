"""
Test Execution Router
Endpoints for executing quality control tests and returning analysis results
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import shutil
import logging
import traceback
import database_helpers

logger = logging.getLogger(__name__)
router = APIRouter()


def parse_test_date(date_str: str) -> datetime:
    """
    Parse test date string, preserving current time if only date is provided
    
    Args:
        date_str: Date string in ISO format or YYYY-MM-DD format
        
    Returns:
        datetime: Parsed datetime with current time if only date provided
    """
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        # If only date provided (YYYY-MM-DD), use current time
        date_only = datetime.strptime(date_str, '%Y-%m-%d').date()
        return datetime.combine(date_only, datetime.now().time())


# Import basic tests functionality
try:
    from basic_tests import (
        get_available_tests,
        create_test_instance,
        execute_test
    )
    logger.info("Successfully imported basic tests in router")
except ImportError as e:
    logger.error(f"Failed to import basic tests in router: {e}")


@router.get("/execute")
async def get_executable_tests():
    """
    Get list of available quality control tests that can be executed
    """
    logger.info("[TEST-EXECUTION] Getting available tests")
    try:
        tests = get_available_tests()
        return JSONResponse({
            'available_tests': tests,
            'count': len(tests)
        })
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error getting tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execute/{test_id}/form")
async def get_test_form(test_id: str):
    """
    Get form structure for a specific test
    """
    logger.info(f"[TEST-EXECUTION] Getting form for test: {test_id}")
    try:
        test_instance = create_test_instance(test_id)
        form_data = test_instance.get_form_data()
        return JSONResponse(form_data)
    except ValueError as e:
        logger.warning(f"[TEST-EXECUTION] Test not found: {test_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error getting form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/niveau-helium")
async def execute_niveau_helium(data: dict):
    """
    Execute niveau d'hélium test
    Expected data: {"helium_level": float, "operator": str, "test_date": str (optional)}
    """
    logger.info("[TEST-EXECUTION] Executing niveau hélium test")
    try:
        # Validate required fields
        if 'helium_level' not in data:
            raise HTTPException(status_code=400, detail="helium_level is required")
        if 'operator' not in data:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'niveau_helium',
            helium_level=float(data['helium_level']),
            operator=data['operator'],
            test_date=test_date
        )
        
        logger.info(f"[TEST-EXECUTION] Niveau hélium test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[TEST-EXECUTION] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/position-table-v2")
async def execute_position_table_v2(data: dict):
    """
    Execute position table V2 test
    Expected data: {"position_175": float, "position_215": float, "operator": str, "test_date": str (optional)}
    """
    logger.info("[TEST-EXECUTION] Executing position table V2 test")
    try:
        # Validate required fields
        required_fields = ['position_175', 'position_215', 'operator']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'position_table_v2',
            position_175=float(data['position_175']),
            position_215=float(data['position_215']),
            operator=data['operator'],
            test_date=test_date
        )
        
        logger.info(f"[TEST-EXECUTION] Position table V2 test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[TEST-EXECUTION] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/alignement-laser")
async def execute_alignement_laser(data: dict):
    """
    Execute alignement laser test
    Expected data: {"ecart_proximal": float, "ecart_central": float, "ecart_distal": float, "operator": str, "test_date": str (optional)}
    """
    logger.info("[TEST-EXECUTION] Executing alignement laser test")
    try:
        # Validate required fields
        required_fields = ['ecart_proximal', 'ecart_central', 'ecart_distal', 'operator']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'alignement_laser',
            ecart_proximal=float(data['ecart_proximal']),
            ecart_central=float(data['ecart_central']),
            ecart_distal=float(data['ecart_distal']),
            operator=data['operator'],
            test_date=test_date
        )
        
        logger.info(f"[TEST-EXECUTION] Alignement laser test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[TEST-EXECUTION] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/quasar")
async def execute_quasar_test(data: dict):
    """
    Execute QUASAR test (Latence du gating et Précision)
    Expected data: {
        "operator": str,
        "latence_status": "PASS"/"FAIL"/"SKIP",
        "latence_reason": str (optional, required if SKIP),
        "coord_correction": float (optional),
        "x_value": float (optional),
        "y_value": float (optional),
        "z_value": float (optional),
        "test_date": str (optional),
        "notes": str (optional)
    }
    """
    logger.info("[TEST-EXECUTION] Executing QUASAR test")
    try:
        # Validate required fields
        if 'operator' not in data:
            raise HTTPException(status_code=400, detail="operator is required")
        if 'latence_status' not in data:
            raise HTTPException(status_code=400, detail="latence_status is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'quasar',
            operator=data['operator'],
            latence_status=data['latence_status'],
            latence_reason=data.get('latence_reason'),
            coord_correction=float(data['coord_correction']) if data.get('coord_correction') else None,
            x_value=float(data['x_value']) if data.get('x_value') else None,
            y_value=float(data['y_value']) if data.get('y_value') else None,
            z_value=float(data['z_value']) if data.get('z_value') else None,
            test_date=test_date,
            notes=data.get('notes')
        )
        
        logger.info(f"[TEST-EXECUTION] QUASAR test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[TEST-EXECUTION] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/indice-quality")
async def execute_indice_quality_test(data: dict):
    """
    Execute Indice de Qualité test (D10/D20 et D5/D15)
    Expected data: {
        "operator": str,
        "d10_m1": float, "d10_m2": float, "d10_m3": float,
        "d20_m1": float, "d20_m2": float, "d20_m3": float,
        "d5_m1": float (optional, default 0), "d5_m2": float (optional), "d5_m3": float (optional),
        "d15_m1": float (optional, default 0), "d15_m2": float (optional), "d15_m3": float (optional),
        "test_date": str (optional),
        "notes": str (optional)
    }
    """
    logger.info("[TEST-EXECUTION] Executing Indice de Qualité test")
    try:
        # Validate required fields
        required_fields = ['operator', 'd10_m1', 'd10_m2', 'd10_m3', 'd20_m1', 'd20_m2', 'd20_m3']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"{field} is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'indice_quality',
            operator=data['operator'],
            d10_m1=float(data['d10_m1']),
            d10_m2=float(data['d10_m2']),
            d10_m3=float(data['d10_m3']),
            d20_m1=float(data['d20_m1']),
            d20_m2=float(data['d20_m2']),
            d20_m3=float(data['d20_m3']),
            d5_m1=float(data.get('d5_m1', 0)),
            d5_m2=float(data.get('d5_m2', 0)),
            d5_m3=float(data.get('d5_m3', 0)),
            d15_m1=float(data.get('d15_m1', 0)),
            d15_m2=float(data.get('d15_m2', 0)),
            d15_m3=float(data.get('d15_m3', 0)),
            test_date=test_date,
            notes=data.get('notes')
        )
        
        logger.info(f"[TEST-EXECUTION] Indice de Qualité test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[TEST-EXECUTION] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/piqt")
async def execute_piqt_test(request: Request):
    """
    Execute PIQT test (Philips Image Quality Test)
    Expects multipart form with:
        - operator: str
        - html_file: uploaded HTML file
        - test_date: str (optional)
        - notes: str (optional)
    """
    logger.info("[TEST-EXECUTION] Executing PIQT test")
    
    try:
        # Parse form data
        form = await request.form()
        logger.info(f"[TEST-EXECUTION] Form keys: {list(form.keys())}")
        
        # Debug: log all form data
        for key in form.keys():
            value = form[key]
            logger.info(f"[TEST-EXECUTION] PIQT form field '{key}': type={type(value)}, hasattr(filename)={hasattr(value, 'filename')}")
            if hasattr(value, 'filename'):
                logger.info(f"[TEST-EXECUTION]   -> filename: {value.filename}")
        
        # Extract operator
        operator = form.get("operator")
        if not operator:
            logger.error("[TEST-EXECUTION] operator field is missing")
            raise HTTPException(status_code=400, detail="operator is required")
        
        logger.info(f"[TEST-EXECUTION] Operator: {operator}")
        
        # Extract HTML file
        html_file = form.get("html_file")
        if not html_file or not hasattr(html_file, 'filename'):
            logger.error(f"[TEST-EXECUTION] html_file is missing or invalid. html_file={html_file}, hasattr={hasattr(html_file, 'filename') if html_file else 'N/A'}")
            raise HTTPException(status_code=400, detail="html_file is required")
        
        if not html_file.filename.lower().endswith(('.html', '.htm')):
            raise HTTPException(status_code=400, detail=f"File {html_file.filename} is not an HTML file")
        
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, html_file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(html_file.file, buffer)
        
        logger.info(f"[TEST-EXECUTION] Saved HTML file: {html_file.filename}")
        
        # Extract test date
        test_date = None
        test_date_str = form.get("test_date")
        if test_date_str:
            try:
                test_date = datetime.fromisoformat(test_date_str.replace('Z', '+00:00'))
            except ValueError:
                try:
                    test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"[TEST-EXECUTION] Invalid date format: {test_date_str}")
        
        # Execute test
        result = execute_test(
            'piqt',
            operator=operator,
            html_file_path=file_path,
            test_date=test_date,
            notes=form.get('notes')
        )
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except OSError:
            pass
        
        logger.info(f"[TEST-EXECUTION] PIQT test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing PIQT test: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/safety-systems")
async def execute_safety_systems(data: dict):
    """
    Execute daily safety systems verification test
    Expected data: {
        "operator": str,
        "accelerator_warmup": "PASS"/"FAIL"/"SKIP",
        "audio_indicator": "PASS"/"FAIL"/"SKIP",
        "visual_indicators_console": "PASS"/"FAIL"/"SKIP",
        "visual_indicator_room": "PASS"/"FAIL"/"SKIP",
        "beam_interruption": "PASS"/"FAIL"/"SKIP",
        "door_interlocks": "PASS"/"FAIL"/"SKIP",
        "camera_monitoring": "PASS"/"FAIL"/"SKIP",
        "patient_communication": "PASS"/"FAIL"/"SKIP",
        "table_emergency_stop": "PASS"/"FAIL"/"SKIP",
        "test_date": str (optional),
        "notes": str (optional)
    }
    """
    logger.info("[TEST-EXECUTION] Executing safety systems test")
    try:
        # Validate required fields
        if 'operator' not in data:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Execute test
        result = execute_test(
            'safety_systems',
            operator=data['operator'],
            accelerator_warmup=data.get('accelerator_warmup', 'SKIP'),
            audio_indicator=data.get('audio_indicator', 'SKIP'),
            visual_indicators_console=data.get('visual_indicators_console', 'SKIP'),
            visual_indicator_room=data.get('visual_indicator_room', 'SKIP'),
            beam_interruption=data.get('beam_interruption', 'SKIP'),
            door_interlocks=data.get('door_interlocks', 'SKIP'),
            camera_monitoring=data.get('camera_monitoring', 'SKIP'),
            patient_communication=data.get('patient_communication', 'SKIP'),
            table_emergency_stop=data.get('table_emergency_stop', 'SKIP'),
            test_date=test_date,
            notes=data.get('notes')
        )
        
        logger.info(f"[TEST-EXECUTION] Safety systems test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        logger.warning(f"[TEST-EXECUTION] Invalid data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/mlc-leaf-jaw-debug")
async def debug_mlc_upload(request: Request):
    """
    Debug endpoint to see what's being sent
    """
    logger.info("[DEBUG] Raw request received")
    
    # Get form data
    form = await request.form()
    logger.info(f"[DEBUG] Form keys: {list(form.keys())}")
    
    for key in form.keys():
        value = form[key]
        logger.info(f"[DEBUG] Field '{key}': {type(value)}")
    
    return {"received_keys": list(form.keys())}


@router.post("/execute/mlc-leaf-jaw")
async def execute_mlc_leaf_jaw(request: Request):
    """
    Execute MLC leaf and jaw test with DICOM file uploads
    """
    logger.info("[TEST-EXECUTION] Executing MLC leaf and jaw test")
    
    file_paths = []  # Initialize at the start to avoid UnboundLocalError
    
    try:
        # Parse form data
        form = await request.form()
        logger.info(f"[TEST-EXECUTION] Form keys: {list(form.keys())}")
        
        # Extract operator
        operator = form.get("operator")
        if not operator:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Parse test date
        test_date = None
        test_date_str = form.get('test_date')
        if test_date_str:
            test_date = parse_test_date(test_date_str)
        
        # Extract DICOM files (multiple files sent with same field name 'dicom_files')
        dicom_files = []
        
        # When multiple files are uploaded with the same field name,
        # form.getlist() returns all of them
        if 'dicom_files' in form:
            files_data = form.getlist('dicom_files')
            for file in files_data:
                if hasattr(file, 'filename') and file.filename:
                    dicom_files.append(file)
        
        # Fallback: check for individually named files (dicom_file_1, dicom_file_2, etc.)
        if not dicom_files:
            for key in form.keys():
                if key.startswith('dicom_file'):
                    file = form[key]
                    if hasattr(file, 'filename') and file.filename:
                        dicom_files.append(file)
        
        if not dicom_files:
            raise HTTPException(status_code=400, detail="At least one DICOM file is required")
        
        logger.info(f"[TEST-EXECUTION] Received {len(dicom_files)} DICOM files for MLC test")
        
        # Save uploaded files
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in dicom_files:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)
            logger.info(f"[TEST-EXECUTION] Saved DICOM file: {file.filename}")
        
        # Execute test
        result = execute_test(
            'mlc_leaf_jaw',
            operator=operator,
            files=file_paths,
            test_date=test_date
        )
        
        # Clean up uploaded files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.info(f"[TEST-EXECUTION] MLC leaf and jaw test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except Exception as e:
        # Clean up uploaded files on error
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.error(f"[TEST-EXECUTION] Error executing MLC test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/mvic")
async def execute_mvic(request: Request):
    """
    Execute MVIC-Champ (MV Imaging Check) test with 5 DICOM files upload
    Validates field size and shape with automatic detection
    """
    logger.info("[TEST-EXECUTION] Executing MVIC-Champ test")
    
    file_paths = []
    
    try:
        # Parse form data
        form = await request.form()
        logger.info(f"[TEST-EXECUTION] Form keys: {list(form.keys())}")
        
        # Extract operator
        operator = form.get("operator")
        if not operator:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Extract test date
        test_date = None
        test_date_str = form.get("test_date")
        if test_date_str:
            try:
                test_date = datetime.fromisoformat(test_date_str.replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
        
        # Extract exactly 5 DICOM files (multiple files sent with same field name 'dicom_files')
        dicom_files = []
        
        # When multiple files are uploaded with the same field name,
        # form.getlist() returns all of them
        if 'dicom_files' in form:
            files_data = form.getlist('dicom_files')
            for file in files_data:
                if hasattr(file, 'filename') and file.filename:
                    dicom_files.append(file)
        
        # Fallback: check for individually named files (dicom_file_1, dicom_file_2, etc.)
        if not dicom_files:
            for i in range(1, 6):
                key = f'dicom_file_{i}'
                if key in form:
                    file = form[key]
                    if hasattr(file, 'filename') and file.filename:
                        dicom_files.append(file)
        
        if len(dicom_files) != 5:
            raise HTTPException(status_code=400, detail=f"Exactly 5 DICOM files are required, received {len(dicom_files)}")
        
        logger.info(f"[TEST-EXECUTION] Received {len(dicom_files)} DICOM files")
        
        # Save uploaded files
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in dicom_files:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)
            logger.info(f"[TEST-EXECUTION] Saved DICOM file: {file.filename}")
        
        # Execute test
        result = execute_test(
            'mvic',
            operator=operator,
            files=file_paths,
            test_date=test_date,
            notes=form.get('notes')
        )
        
        # Clean up uploaded files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.info(f"[TEST-EXECUTION] MVIC-Champ test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except Exception as e:
        # Clean up uploaded files on error
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.error(f"[TEST-EXECUTION] Error executing MVIC-Champ test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/mvic_fente_v2")
@router.post("/execute/mvic-fente-v2")
async def execute_mvic_fente_v2(request: Request):
    """
    Execute MVIC Fente V2 test with DICOM file upload
    Analyzes MLC slits using edge detection (ImageJ method)
    """
    logger.info("[TEST-EXECUTION] Executing MVIC Fente test")
    
    file_paths = []
    
    try:
        # Parse form data
        form = await request.form()
        logger.info(f"[TEST-EXECUTION] Form keys: {list(form.keys())}")
        
        # Extract operator
        operator = form.get("operator")
        if not operator:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Extract test date
        test_date = None
        test_date_str = form.get("test_date")
        if test_date_str:
            try:
                test_date = datetime.fromisoformat(test_date_str.replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
        
        # Extract DICOM files (multiple files sent with same field name 'dicom_files')
        dicom_files = []
        
        # When multiple files are uploaded, form.getlist() returns all of them
        if 'dicom_files' in form:
            files_data = form.getlist('dicom_files')
            for file in files_data:
                if hasattr(file, 'filename') and file.filename:
                    dicom_files.append(file)
        
        if not dicom_files:
            raise HTTPException(status_code=400, detail="At least one DICOM file is required")
        
        logger.info(f"[TEST-EXECUTION] Received {len(dicom_files)} DICOM files for MVIC Fente")
        
        # Save all uploaded files
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in dicom_files:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)
            logger.info(f"[TEST-EXECUTION] Saved DICOM file: {file.filename}")
        
        # Execute test on all files
        result = execute_test(
            'mvic_fente_v2',
            files=file_paths,
            operator=operator,
            test_date=test_date,
            notes=form.get('notes')
        )
        
        # Clean up uploaded files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.info(f"[TEST-EXECUTION] MVIC Fente test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except Exception as e:
        # Clean up uploaded files on error
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.error(f"[TEST-EXECUTION] Error executing MVIC Fente test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/leaf-position")
async def execute_leaf_position(request: Request):
    """
    Execute Leaf Position test with DICOM file uploads
    Automatically detects blade positions and field size
    """
    logger.info("[LEAF-POSITION] ========== NEW REQUEST ==========")
    
    file_paths = []
    
    try:
        # Parse form data
        form = await request.form()
        logger.info(f"[LEAF-POSITION] Form keys: {list(form.keys())}")
        
        # Extract operator
        operator = form.get("operator")
        if not operator:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Extract test date
        test_date = None
        test_date_str = form.get("test_date")
        if test_date_str:
            test_date = parse_test_date(test_date_str)
        
        # Extract DICOM files (multiple files sent with same field name 'dicom_files' or 'dicom_file')
        dicom_files = []
        
        # Try dicom_files (plural) first
        if 'dicom_files' in form:
            files_data = form.getlist('dicom_files')
            for file in files_data:
                if hasattr(file, 'filename') and file.filename:
                    dicom_files.append(file)
        
        # Try dicom_file (singular) - this field can contain multiple files when multiple=True
        if not dicom_files and 'dicom_file' in form:
            files_data = form.getlist('dicom_file')  # Use getlist to get all files with this name
            for file in files_data:
                if hasattr(file, 'filename') and file.filename:
                    dicom_files.append(file)
        
        if not dicom_files:
            raise HTTPException(status_code=400, detail="At least one DICOM file is required")
        
        logger.info(f"[LEAF-POSITION] Processing {len(dicom_files)} files: {[f.filename for f in dicom_files]}")
        
        # Save all uploaded files
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in dicom_files:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(file_path)
            logger.info(f"[LEAF-POSITION] Saved DICOM file: {file.filename}")
        
        # Execute test on all files AT ONCE (should create ONE test)
        logger.info(f"[LEAF-POSITION] Executing test with {len(file_paths)} files")
        result = execute_test(
            'leaf_position',
            files=file_paths,
            operator=operator,
            test_date=test_date,
            notes=form.get('notes')
        )
        logger.info(f"[LEAF-POSITION] Test execution completed. Result keys: {list(result.keys())}")
        
        # Prepare data for database saving
        # Extract blade results for each image
        blade_results = []
        filenames = [os.path.basename(fp) for fp in file_paths]
        logger.info(f"[LEAF-POSITION] Extracting blade results from {len(filenames)} files")
        
        for file_idx, filename in enumerate(filenames, 1):
            image_blades = []
            
            # Extract blade data from results
            for result_key, result_value in result.get('results', {}).items():
                # Look for blade results matching this file
                if result_key.startswith(f'file_{file_idx}_blade_'):
                    value_data = result_value.get('value', {})
                    image_blades.append({
                        'pair': int(result_key.split('_')[-1]),  # Extract blade pair number
                        'position_u_px': value_data.get('position_u_px'),
                        'v_sup_px': value_data.get('v_sup_px'),
                        'v_inf_px': value_data.get('v_inf_px'),
                        'distance_sup_mm': value_data.get('distance_sup_mm'),
                        'distance_inf_mm': value_data.get('distance_inf_mm'),
                        'length_mm': value_data.get('length_mm'),
                        'field_size_mm': value_data.get('length_mm'),  # Same as length
                        'is_valid': value_data.get('status', 'UNKNOWN'),
                        'status_message': result_value.get('details', '')
                    })
            
            blade_results.append({
                'blades': image_blades
            })
        
        # Add blade results to response for frontend to save
        result['blade_results'] = blade_results
        result['filenames'] = [os.path.basename(fp) for fp in file_paths]
        logger.info(f"[LEAF-POSITION] Added {len(blade_results)} image results to response")
        
        # DON'T auto-save - let user click Save button
        # Instead, save visualizations with a temporary ID and update later
        
        # For now, include visualizations in response as base64
        # The save endpoint will handle saving them to files
        
        # Clean up uploaded files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.info(f"[TEST-EXECUTION] Leaf Position test result: {result['overall_result']}")
        return JSONResponse(result)
        
    except Exception as e:
        # Clean up uploaded files on error
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        logger.error(f"[TEST-EXECUTION] Error executing Leaf Position test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{test_id}")
async def execute_test_generic(test_id: str, data: dict):
    """
    Execute any test by ID with generic data
    This is a flexible endpoint for frontend integration
    """
    logger.info(f"[TEST-EXECUTION] Executing test: {test_id}")
    try:
        # Validate operator
        if 'operator' not in data:
            raise HTTPException(status_code=400, detail="operator is required")
        
        # Parse test date if provided
        test_date = None
        if 'test_date' in data and data['test_date']:
            try:
                test_date = datetime.fromisoformat(data['test_date'].replace('Z', '+00:00'))
            except ValueError:
                test_date = datetime.strptime(data['test_date'], '%Y-%m-%d')
        
        # Prepare parameters
        params = dict(data)
        if test_date:
            params['test_date'] = test_date
        
        # Map dicom_file/dicom_files to files parameter for file-based tests
        if 'dicom_file' in params and 'files' not in params:
            file_value = params.pop('dicom_file')
            # Convert single file or list of files to files parameter
            if isinstance(file_value, list):
                params['files'] = file_value
            else:
                params['files'] = [file_value] if file_value else []
        elif 'dicom_files' in params and 'files' not in params:
            params['files'] = params.pop('dicom_files')
        
        # Execute test
        result = execute_test(test_id, **params)
        
        logger.info(f"[TEST-EXECUTION] Test {test_id} result: {result['overall_result']}")
        return JSONResponse(result)
        
    except ValueError as e:
        if "not found" in str(e):
            logger.warning(f"[TEST-EXECUTION] Test not found: {test_id}")
            raise HTTPException(status_code=404, detail=str(e))
        else:
            logger.warning(f"[TEST-EXECUTION] Invalid data: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TEST-EXECUTION] Error executing test: {e}")
        raise HTTPException(status_code=500, detail=str(e))
