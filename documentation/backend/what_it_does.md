# Backend Files Overview

Quick reference for what each file does in the backend.

## Root Directory

- **main.py** - FastAPI application entry point, configures routes and starts uvicorn server
- **database.py** - Legacy compatibility layer, imports from modular database structure
- **database_helpers.py** - CRUD operations for saving test results to database
- **report_generator.py** - PDF report generation for QC test results
- **mv_center_utils.py** - Utilities for MV center detection in DICOM images
- **requirements.txt** - Python package dependencies

## database/

- **config.py** - SQLAlchemy database configuration and Base model
- **queries.py** - Common database query functions
- **daily_tests.py** - Database models for daily QC tests (Safety Systems)
- **weekly_tests.py** - Database models for weekly QC tests (MVIC, MLC, PIQT, Helium, Exactitude du MLC)
- **monthly_tests.py** - Database models for monthly QC tests (Position Table, Laser, Quasar, Indice Quality)
- **mlc_curie.py** - MLC blade analysis and validation functions

## routers/

- **basic_tests_routes.py** - API routes for basic test types
- **config_routes.py** - Configuration management endpoints
- **daily_tests.py** - Daily test execution and save endpoints
- **weekly_tests.py** - Weekly test execution and save endpoints
- **monthly_tests.py** - Monthly test execution and save endpoints
- **mlc_routes.py** - MLC-specific test routes and analysis
- **mvic_routes.py** - MVIC test routes and image analysis
- **reports.py** - PDF report generation endpoints
- **result_display_router.py** - Routes for displaying saved test results
- **test_execution.py** - Generic test execution framework
- **test_sessions.py** - Test session management and history

## result_displays/

- **mlc_display.py** - Display logic for MLC Leaf and Jaw test results
- **mvic_display.py** - Display logic for MVIC 5-image test results
- **mvic_fente_v2_display.py** - Display logic for MVIC Fente V2 slit analysis results
- **niveau_helium_display.py** - Display logic for Helium level test results
- **piqt_display.py** - Display logic for PIQT image quality test results

## services/

- **visualization_storage.py** - Save and manage test visualization images
- **mlc_blade_report_generator.py** - Generate detailed MLC blade compliance PDF reports

## tests/

Test and debug code for radnom shit
