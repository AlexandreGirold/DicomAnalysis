# Main.py Refactoring Plan

## Current State
- **Total Lines**: 2736
- **Total Endpoints**: 77
- **Status**: Monolithic file - difficult to navigate and maintain

## Refactoring Strategy
Split main.py into focused router modules based on functionality domains.

## Router Modules

### ✅ 1. test_sessions.py (COMPLETED)
**Lines**: ~320  
**Endpoints**: 30 (GET/DELETE for 10 test types)
- Safety Systems (daily)
- Niveau Helium (weekly)
- MVIC Fente V2 (weekly)
- PIQT (weekly)
- Position Table (monthly)
- Alignement Laser (monthly)
- Quasar (monthly)
- Indice Quality (monthly)

### 2. mlc_routes.py (TODO)
**Estimated Lines**: ~400  
**Endpoints**: ~8
- POST /mlc-test-sessions
- GET /mlc-test-sessions
- GET /mlc-test-sessions/{id}
- DELETE /mlc-test-sessions/{id}
- GET /mlc-trend/{parameter}
- GET /mlc-reports/trend
- POST /analyze (MLC analysis logic)
- POST /analyze-batch

### 3. mvic_routes.py (TODO)
**Estimated Lines**: ~350  
**Endpoints**: ~5
- POST /mvic-test-sessions
- GET /mvic-test-sessions
- GET /mvic-test-sessions/{id}
- DELETE /mvic-test-sessions/{id}
- GET /mvic-trend/{parameter}

### 4. test_save_routes.py (TODO)
**Estimated Lines**: ~400  
**Endpoints**: ~10 (POST endpoints for all test types)
- POST /mlc-leaf-jaw-sessions
- POST /mvic-fente-v2-sessions
- POST /niveau-helium-sessions
- POST /piqt-sessions
- POST /safety-systems-sessions
- POST /position-table-sessions
- POST /alignement-laser-sessions
- POST /quasar-sessions
- POST /indice-quality-sessions

### 5. basic_tests_routes.py (TODO)
**Estimated Lines**: ~800  
**Endpoints**: ~15
- GET /basic-tests
- GET /basic-tests/{test_id}/form
- POST /basic-tests/{test_type} (for all test types)
- POST /basic-tests/{test_id}

### 6. legacy_routes.py (TODO)
**Estimated Lines**: ~200  
**Endpoints**: ~9
- GET /tests
- GET /tests/{test_id}
- DELETE /tests/{test_id}
- GET /blade-trend/{blade_pair}
- GET /database/stats
- GET /reports/test/{test_id}
- GET /reports/trend/{test_type}
- GET /generic-tests
- GET /generic-tests/{test_id}
- DELETE /generic-tests/{test_id}

### 7. main.py (FINAL)
**Target Lines**: <200  
**Responsibilities**:
- App initialization
- CORS configuration
- Static file mounting
- Router registration
- Core endpoints (root, config, visualizations)
- Helper functions (sanitize_field_name, parse_test_date)

## Benefits
1. **Maintainability**: Easier to find and update specific functionality
2. **Readability**: Each file has a clear, focused purpose
3. **Scalability**: Easy to add new test types in focused modules
4. **Testing**: Easier to unit test individual router modules
5. **Collaboration**: Multiple developers can work on different routers simultaneously

## Implementation Progress
- ✅ Created routers/ directory
- ✅ Created test_sessions.py router (30 endpoints, ~320 lines)
- ⏳ Need to update main.py to include router
- ⏳ Create remaining router modules
- ⏳ Reduce main.py to <200 lines

## Next Steps
1. Update main.py to import and include test_sessions router
2. Test that all endpoints still work
3. Create mlc_routes.py
4. Create mvic_routes.py
5. Continue with other routers
6. Remove old endpoint definitions from main.py as they're migrated
