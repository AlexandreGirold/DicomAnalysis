# Frontend JavaScript Architecture

## Overview
The frontend JavaScript has been refactored into modular files for better maintainability and readability.

## File Structure

```
frontend/js/
├── config.js          - Configuration and constants
├── state.js           - Application state management
├── ui.js              - UI helper functions (modals, loading, etc.)
├── test-list.js       - Test list display and categorization
├── form-builder.js    - Dynamic form field generation
├── test-execution.js  - Test execution logic
├── results-display.js - Results visualization
└── main.js            - Application entry point
```

## Module Responsibilities

### config.js
- API base URL configuration
- Global constants

### state.js
- Central state management
- Stores: available tests, current test, form data, visualizations

### ui.js
- Loading indicators
- Modal controls
- Print functionality
- General UI helpers

### test-list.js
- Fetches available tests from API
- Displays tests grouped by category (Basic, Daily, Weekly, Monthly)
- Handles test selection

### form-builder.js
- Builds dynamic form fields based on test requirements
- Supports field types:
  - date
  - text
  - textarea
  - number
  - select (dropdown)
  - file
- Adds field details, tooltips, and tolerance information

### test-execution.js
- Handles form submission
- Distinguishes between file upload tests and regular tests
- Sends data to appropriate API endpoints
- Handles errors and validation

### results-display.js
- Displays test results
- Handles visualization navigation
- Image modal for full-size viewing

### main.js
- Application initialization
- Loads tests on page load

## Test Categories

Tests are organized into 4 categories:

1. **Basic Tests** (Tests de Base)
   - Core functionality tests
   
2. **Daily Tests** (Tests Quotidiens)
   - Daily QC checks (e.g., Safety Systems)
   
3. **Weekly Tests** (Tests Hebdomadaires)
   - Weekly verification tests
   
4. **Monthly Tests** (Tests Mensuels)
   - Monthly comprehensive tests

## Adding New Tests

To add a new test:

1. Create test class in `backend/services/basic_tests/` or `backend/services/daily/`
2. Register test in appropriate `__init__.py` with category
3. Add API endpoint in `backend/main.py` (optional - generic endpoint handles most tests)
4. Frontend will automatically discover and display the test

## Form Field Types

### Date Field
```javascript
{
    name: 'test_date',
    label: 'Date:',
    type: 'date',
    required: true,
    default: '2025-01-01'
}
```

### Select Field
```javascript
{
    name: 'status',
    label: 'Status:',
    type: 'select',
    required: true,
    options: ['PASS', 'FAIL', 'SKIP'],
    details: 'Select test result',
    tolerance: 'Must be functional'
}
```

### Number Field
```javascript
{
    name: 'value',
    label: 'Measurement:',
    type: 'number',
    required: true,
    min: 0,
    max: 100,
    step: 0.1,
    unit: 'mm'
}
```

### Textarea Field
```javascript
{
    name: 'notes',
    label: 'Notes:',
    type: 'textarea',
    required: false,
    placeholder: 'Optional comments...',
    rows: 4
}
```

## API Integration

### List Tests
```
GET /basic-tests
Returns: { available_tests: { test_id: { description, class_name, category } } }
```

### Get Test Form
```
GET /basic-tests/{test_id}/form
Returns: Form configuration with fields, title, description
```

### Execute Test
```
POST /basic-tests/{test_id}
Body: { operator, ...test_specific_fields }
Returns: Test results with status, results, visualizations
```

## Dependencies

All modules depend on:
- `window.APP_CONFIG` (from config.js)
- `window.APP_STATE` (from state.js)

Load order matters - see index.html for correct script order.
