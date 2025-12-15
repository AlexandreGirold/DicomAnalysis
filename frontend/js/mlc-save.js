/**
 * MLC/MVIC Test Database Save Functionality
 * Handles saving MLC and MVIC test results to the database
 */

// Store current test data globally
window.CURRENT_MLC_TEST_DATA = null;
window.CURRENT_TEST_TYPE = null; // 'mlc' or 'mvic'

/**
 * Extract filenames from analysis result
 */
function extractFilenames(analysisResult) {
    const filenames = [];
    
    // Check file_results array
    if (analysisResult.file_results && Array.isArray(analysisResult.file_results)) {
        analysisResult.file_results.forEach(fr => {
            if (fr.filename) {
                filenames.push(fr.filename);
            }
        });
    }
    
    // Check visualizations array
    if (analysisResult.visualizations && Array.isArray(analysisResult.visualizations)) {
        analysisResult.visualizations.forEach(viz => {
            if (viz.filename) {
                filenames.push(viz.filename);
            }
        });
    }
    
    // Check top-level filename or filenames field
    if (analysisResult.filename) {
        filenames.push(analysisResult.filename);
    }
    if (analysisResult.filenames && Array.isArray(analysisResult.filenames)) {
        filenames.push(...analysisResult.filenames);
    }
    
    // Return unique filenames
    return [...new Set(filenames)];
}

/**
 * Prepare generic test data (for simple tests)
 * Extracts test-specific fields from inputs and results
 */
function prepareGenericTestData(analysisResult) {
    console.log('🔧 prepareGenericTestData - Full result:', analysisResult);
    
    const baseData = {
        test_date: analysisResult.test_date || new Date().toISOString(),
        operator: analysisResult.operator || null,
        overall_result: analysisResult.overall_result || 'PASS',
        notes: analysisResult.notes || '',
        filenames: extractFilenames(analysisResult)
    };
    
    // Extract ALL test-specific fields from inputs
    // This handles: niveau_helium, safety_systems, position_table, alignement_laser, quasar, indice_quality, piqt
    if (analysisResult.inputs) {
        console.log('📥 Found inputs:', analysisResult.inputs);
        
        Object.keys(analysisResult.inputs).forEach(key => {
            // Skip fields that are already in baseData (operator, notes, test_date)
            if (!baseData[key] && analysisResult.inputs[key] !== undefined) {
                // Extract the value from the input object structure
                const inputValue = analysisResult.inputs[key];
                if (inputValue && typeof inputValue === 'object' && 'value' in inputValue) {
                    baseData[key] = inputValue.value;
                    console.log(`✓ Extracted ${key} from inputs.value:`, baseData[key]);
                } else {
                    baseData[key] = inputValue;
                    console.log(`✓ Extracted ${key} from inputs:`, baseData[key]);
                }
            }
        });
    }
    
    // Extract fields from results (for computed values)
    // Some tests return results as an array (e.g., PIQT), others as key-value pairs (dict)
    if (analysisResult.results) {
        console.log('📊 Found results:', analysisResult.results);
        
        // Check if results is an array
        if (Array.isArray(analysisResult.results)) {
            // Store the entire array for tests that use array format
            baseData.results = analysisResult.results;
            console.log(`✓ Stored results array with ${analysisResult.results.length} items`);
        } 
        // Check if results is an object/dict (BaseTest format)
        else if (typeof analysisResult.results === 'object') {
            // Store as-is - backend will convert dict to array format
            baseData.results = analysisResult.results;
            console.log(`✓ Stored results object with ${Object.keys(analysisResult.results).length} keys`);
        }
    }
    
    // Also check top-level fields as fallback
    // Some tests might return data directly at the top level
    const topLevelFields = Object.keys(analysisResult).filter(key => 
        !['test_name', 'description', 'test_date', 'operator', 'inputs', 'results', 
          'overall_result', 'overall_status', 'notes', 'filenames'].includes(key)
    );
    
    topLevelFields.forEach(field => {
        if (analysisResult[field] !== undefined && !baseData[field]) {
            baseData[field] = analysisResult[field];
            console.log(`✓ Extracted from top level ${field}:`, baseData[field]);
        }
    });
    
    console.log('📦 Final prepared data:', baseData);
    return baseData;
}

/**
 * Extract and prepare MLC test data from analysis results
 * @param {object} analysisResult - The raw analysis result from backend
 */
function prepareMLCTestData(analysisResult) {
    console.log('Full analysis result:', analysisResult);
    
    // The actual test result structure from backend
    const mlcData = {
        test_date: analysisResult.test_date || new Date().toISOString(),
        operator: analysisResult.operator || null,
        test1_center: {},
        test2_jaw: {},
        test3_blade_top: {},
        test4_blade_bottom: {},
        test5_angle: {},
        overall_result: analysisResult.overall_result || 'UNKNOWN',
        notes: ''
    };
    
    // Check if we have file_results (per-image analysis data)
    if (analysisResult.file_results && Array.isArray(analysisResult.file_results)) {
        console.log('Processing file_results:', analysisResult.file_results);
        
        analysisResult.file_results.forEach((fileResult, index) => {
            const analysisType = fileResult.analysis_type;
            const results = fileResult.results;
            
            console.log(`File ${index + 1} - Type: ${analysisType}`, results);
            
            // Extract data based on analysis type
            switch(analysisType) {
                case 'center_detection':  // Test 1
                    if (results && results.type === 'center_detection') {
                        mlcData.test1_center = {
                            center_u: results.u_center_px,
                            center_v: results.v_center_px
                        };
                    }
                    break;
                    
                case 'jaw_position':  // Test 2
                    if (results && results.type === 'jaw_position') {
                        mlcData.test2_jaw = {
                            jaw_x1_mm: results.x1_mm,
                            jaw_x2_mm: results.x2_mm
                        };
                    }
                    break;
                    
                case 'leaf_position':  // Test 3 or Test 4
                    // Calculate average and std deviation for this image
                    if (Array.isArray(results)) {
                        const fieldSizes = results
                            .filter(r => r[3] !== null && r[4] !== 'CLOSED')
                            .map(r => r[3]);  // field_size_mm is at index 3
                        
                        if (fieldSizes.length > 0) {
                            const average = fieldSizes.reduce((a, b) => a + b, 0) / fieldSizes.length;
                            const variance = fieldSizes.reduce((sum, val) => sum + Math.pow(val - average, 2), 0) / fieldSizes.length;
                            const stdDev = Math.sqrt(variance);
                            
                            // Image 3 is top, Image 4 is bottom (0-indexed: 2 and 3)
                            if (index === 2) {  // Test 3 - Top
                                mlcData.test3_blade_top = {
                                    average: average,
                                    std_dev: stdDev
                                };
                            } else if (index === 3) {  // Test 4 - Bottom
                                mlcData.test4_blade_bottom = {
                                    average: average,
                                    std_dev: stdDev
                                };
                            }
                        }
                    }
                    break;
                    
                case 'blade_straightness':  // Test 5
                    if (results && results.type === 'blade_straightness' && results.average_angle) {
                        mlcData.test5_angle = {
                            average_angle: results.average_angle
                        };
                    }
                    break;
            }
        });
    }
    
    console.log('Prepared MLC data:', mlcData);
    
    // Include visualizations for saving as image files
    if (analysisResult.visualizations) {
        mlcData.visualizations = analysisResult.visualizations;
    }
    
    return mlcData;
}

/**
 * Prepare MVIC test data from analysis results
 */
function prepareMVICTestData(analysisResult) {
    console.log('Preparing MVIC test data:', analysisResult);
    
    const mvicData = {
        test_date: analysisResult.test_date || new Date().toISOString(),
        operator: analysisResult.operator || null,
        overall_result: analysisResult.overall_result || 'UNKNOWN',
        notes: ''
    };
    
    // First, try to extract data from file_results (most complete data)
    if (analysisResult.file_results && Array.isArray(analysisResult.file_results)) {
        console.log('Processing MVIC file_results:', analysisResult.file_results);
        
        analysisResult.file_results.forEach((fileResult, index) => {
            const imageNum = index + 1;
            const measurements = fileResult.measurements || {};
            
            mvicData[`image${imageNum}`] = {
                width_mm: measurements.width_mm || 0,
                height_mm: measurements.height_mm || 0,
                avg_angle: measurements.avg_angle || 90.0,
                angle_std_dev: measurements.angle_std_dev || 0,
                top_left_angle: measurements.top_left_angle || 90.0,
                top_right_angle: measurements.top_right_angle || 90.0,
                bottom_left_angle: measurements.bottom_left_angle || 90.0,
                bottom_right_angle: measurements.bottom_right_angle || 90.0
            };
        });
    }
    
    // Fallback: Extract data from visualizations if file_results not available
    if (!analysisResult.file_results && analysisResult.visualizations && Array.isArray(analysisResult.visualizations)) {
        console.log('Processing MVIC visualizations (fallback):', analysisResult.visualizations);
        
        analysisResult.visualizations.forEach((viz, index) => {
            const imageNum = index + 1;
            const stats = viz.statistics;
            
            // Parse field size "150.20x85.10mm" format
            if (stats && stats.field_size && stats.field_size !== 'N/A') {
                const sizeMatch = stats.field_size.match(/([0-9.]+)x([0-9.]+)mm/);
                if (sizeMatch) {
                    mvicData[`image${imageNum}`] = {
                        width_mm: parseFloat(sizeMatch[1]),
                        height_mm: parseFloat(sizeMatch[2])
                    };
                }
            }
        });
    }
    
    // Extract angle data from results
    if (analysisResult.results && Array.isArray(analysisResult.results)) {
        console.log('Processing MVIC results for angles:', analysisResult.results);
        
        // Group results by image (look for "Image N:" pattern)
        let currentImageNum = 0;
        
        analysisResult.results.forEach(result => {
            // Detect image number from result name
            const imageMatch = result.name && result.name.match(/Image (\d+):/);
            if (imageMatch) {
                currentImageNum = parseInt(imageMatch[1]);
            }
            
            // Extract angle statistics
            if (result.name && result.name.includes('Angles')) {
                if (result.details && typeof result.details === 'string') {
                    // Parse details like "Average: 90.12°, Std Dev: 0.45°"
                    const avgMatch = result.details.match(/Average:\s*([0-9.]+)°/);
                    const stdMatch = result.details.match(/Std Dev:\s*([0-9.]+)°/);
                    
                    if (avgMatch || stdMatch) {
                        if (!mvicData[`image${currentImageNum}`]) {
                            mvicData[`image${currentImageNum}`] = {};
                        }
                        if (avgMatch) {
                            mvicData[`image${currentImageNum}`].avg_angle = parseFloat(avgMatch[1]);
                        }
                        if (stdMatch) {
                            mvicData[`image${currentImageNum}`].angle_std_dev = parseFloat(stdMatch[1]);
                        }
                    }
                }
            }
        });
    }
    
    console.log('Prepared MVIC data:', mvicData);
    
    // Include visualizations for saving as image files
    if (analysisResult.visualizations) {
        mvicData.visualizations = analysisResult.visualizations;
    }
    
    // Include file_results with per-file metadata and detailed measurements
    if (analysisResult.file_results) {
        mvicData.file_results = analysisResult.file_results;
    }
    
    // Include filenames for database storage
    if (analysisResult.filenames) {
        mvicData.filenames = analysisResult.filenames;
    }
    
    return mvicData;
}

/**
 * Show save button and store test data
 */
function enableMLCTestSave(analysisResult, testType = null) {
    console.log('============================================');
    console.log('🔍 SAVE BUTTON ACTIVATION');
    console.log('============================================');
    console.log('📥 Input testType:', testType);
    console.log('📄 Test Name:', analysisResult.test_name);
    console.log('📊 Full Result:', analysisResult);
    
    // Try to detect test type from multiple sources
    if (!testType || testType === 'mlc') {
        console.log('⚠️  Need to detect test type (got null or "mlc")');
        
        // Try from test_name first
        const detectedType = mapTestNameToEndpoint(analysisResult.test_name);
        if (detectedType) {
            console.log('✅ Detected from test_name:', detectedType);
            testType = detectedType;
        }
        // Legacy fallback: check if it contains MVIC or MLC keywords
        else if (analysisResult.test_name) {
            const name = analysisResult.test_name.toLowerCase();
            console.log('🔎 Checking test name pattern:', name);
            if (name.includes('mvic')) {
                testType = 'mvic';
                console.log('✅ Detected MVIC from name');
            } else if (name.includes('mlc')) {
                testType = 'mlc_leaf_jaw';
                console.log('✅ Detected MLC from name');
            }
        }
    } else {
        console.log('✅ Test type provided:', testType);
    }
    
    // If still not detected, try to infer from result structure
    if (!testType || testType === 'mlc') {
        console.log('⚠️  Still not detected, checking result structure...');
        if (analysisResult.visualizations && Array.isArray(analysisResult.visualizations)) {
            testType = 'mvic';  // MVIC tests have visualizations
            console.log('✅ Detected MVIC from visualizations array');
        } else if (analysisResult.file_results && Array.isArray(analysisResult.file_results)) {
            // Check analysis types in file_results
            const analysisTypes = analysisResult.file_results.map(fr => fr.analysis_type);
            console.log('🔍 Analysis types found:', analysisTypes);
            if (analysisTypes.some(t => t === 'center_detection' || t === 'jaw_position')) {
                testType = 'mlc_leaf_jaw';
                console.log('✅ Detected MLC from analysis types');
            }
        }
    }
    
    console.log('🎯 FINAL TEST TYPE:', testType);
    console.log('🔗 Will use endpoint:', TEST_SAVE_ENDPOINTS[testType]);
    console.log('============================================');
    window.CURRENT_TEST_TYPE = testType;
    
    // Always show the save button for any test result
    const saveBtn = document.getElementById('saveTestBtn');
    console.log('Save button element:', saveBtn);
    
    if (saveBtn) {
        saveBtn.style.display = 'inline-block';
        console.log('Save button displayed');
    } else {
        console.error('Save button not found in DOM!');
        return;
    }
    
    // Prepare data based on test type
    let testData = null;
    
    // Special handling for complex tests
    if (testType === 'mvic') {
        testData = prepareMVICTestData(analysisResult);
    } else if (testType === 'mlc_leaf_jaw') {
        testData = prepareMLCTestData(analysisResult);
    } else if (testType === 'mvic_fente' || testType === 'mvic_fente_v2') {
        // For MVIC Fente, we need to extract slit data
        testData = prepareGenericTestData(analysisResult);
        // Use detailed_results which has the slits array structure
        testData.results = analysisResult.detailed_results || [];
        // Include visualizations for saving as image files
        testData.visualizations = analysisResult.visualizations || [];
        // Include file_results with per-file metadata
        testData.file_results = analysisResult.file_results || [];
    } else {
        // For all other tests, use generic preparation
        testData = prepareGenericTestData(analysisResult);
    }
    
    if (!testData) {
        console.warn('Could not prepare test data - using fallback');
        // Fallback with minimal data
        testData = prepareGenericTestData(analysisResult);
    }
    
    console.log('Test data prepared:', testData);
    
    // Store globally
    window.CURRENT_MLC_TEST_DATA = testData;
}

/**
 * Map test IDs/types to their save endpoints
 * MUST match the test IDs from backend services/__init__.py files
 */
const TEST_SAVE_ENDPOINTS = {
    // Weekly tests
    'mvic': '/mvic-test-sessions',
    'mvic_fente': '/mvic-fente-v2-sessions',
    'mvic_fente_v2': '/mvic-fente-v2-sessions',
    'mlc_leaf_jaw': '/mlc-leaf-jaw-sessions',
    'niveau_helium': '/niveau-helium-sessions',
    'piqt': '/piqt-sessions',
    
    // Daily tests
    'safety_systems': '/safety-systems-sessions',
    
    // Monthly tests
    'position_table_v2': '/position-table-sessions',
    'alignement_laser': '/alignement-laser-sessions',
    'quasar': '/quasar-sessions',
    'indice_quality': '/indice-quality-sessions'
};

/**
 * Map test names (from result.test_name) to endpoint keys
 */
function mapTestNameToEndpoint(testName) {
    if (!testName) return null;
    
    const name = testName.toLowerCase();
    
    if (name.includes('mvic') && name.includes('fente')) {
        return 'mvic_fente_v2';
    }
    if (name.includes('mvic')) {
        return 'mvic';
    }
    if (name.includes('mlc') && name.includes('leaf')) {
        return 'mlc_leaf_jaw';
    }
    if (name.includes('helium') || name.includes('hélium')) {
        return 'niveau_helium';
    }
    if (name.includes('piqt')) {
        return 'piqt';
    }
    if (name.includes('safety')) {
        return 'safety_systems';
    }
    if (name.includes('position') && name.includes('table')) {
        return 'position_table_v2';
    }
    if (name.includes('alignement') && name.includes('laser')) {
        return 'alignement_laser';
    }
    if (name.includes('quasar')) {
        return 'quasar';
    }
    if (name.includes('indice') || name.includes('quality')) {
        return 'indice_quality';
    }
    
    return null;
}

/**
 * Save test to database (routes to correct endpoint based on test type)
 */
async function saveMLCTestToDatabase() {
    if (!window.CURRENT_MLC_TEST_DATA) {
        alert('No test data available to save');
        return;
    }
    
    const testData = window.CURRENT_MLC_TEST_DATA;
    const testType = window.CURRENT_TEST_TYPE || 'mvic';
    
    console.log('============================================');
    console.log('💾 SAVING TEST TO DATABASE');
    console.log('============================================');
    console.log('🔑 Test Type:', testType);
    console.log('📦 Test Data:', testData);
    
    // Prompt for operator name if not set
    if (!testData.operator) {
        const operator = prompt('Enter operator name:');
        if (!operator) {
            alert('Operator name is required');
            return;
        }
        testData.operator = operator;
    }
    
    // Ensure test_date is set
    if (!testData.test_date) {
        testData.test_date = new Date().toISOString();
    }
    
    // Show loading state
    const saveBtn = document.getElementById('saveTestBtn');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = '⏳ Saving...';
    
    try {
        // Get the correct endpoint for this test type
        const endpointPath = TEST_SAVE_ENDPOINTS[testType];
        if (!endpointPath) {
            console.error('❌ UNKNOWN TEST TYPE!');
            console.error('Available types:', Object.keys(TEST_SAVE_ENDPOINTS));
            throw new Error(`Unknown test type: ${testType}. Cannot determine save endpoint.`);
        }
        
        const endpoint = `${window.APP_CONFIG.API_BASE_URL}${endpointPath}`;
        console.log('🌐 POST to:', endpoint);
        console.log('📤 Sending data:', JSON.stringify(testData, null, 2));
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        console.log('📡 Response status:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Server error:', error);
            throw new Error(error.detail || 'Failed to save test');
        }
        
        const result = await response.json();
        console.log('✅ SUCCESS! Result:', result);
        console.log('============================================');
        
        // Get test type name for display
        const testTypeNames = {
            'mvic': 'MVIC',
            'mvic_fente': 'MVIC Fente',
            'mvic_fente_v2': 'MVIC Fente V2',
            'mlc_leaf_jaw': 'MLC Leaf Jaw',
            'niveau_helium': 'Niveau Helium',
            'piqt': 'PIQT',
            'safety_systems': 'Safety Systems',
            'position_table_v2': 'Position Table V2',
            'alignement_laser': 'Alignement Laser',
            'quasar': 'Quasar',
            'indice_quality': 'Indice Quality'
        };
        const testDisplayName = testTypeNames[testType] || testType.toUpperCase();
        
        alert(`✅ ${testDisplayName} test saved successfully!\n\nTest ID: ${result.test_id}\n\nYou can view this test in the Review page.`);
        
        // Update button to show saved state
        saveBtn.textContent = '✅ Saved';
        saveBtn.classList.remove('btn-success');
        saveBtn.classList.add('btn-secondary');
        
        // Clear stored data
        window.CURRENT_MLC_TEST_DATA = null;
        window.CURRENT_TEST_TYPE = null;
        
    } catch (error) {
        console.error('Error saving test:', error);
        alert(`Error saving test: ${error.message}`);
        
        // Restore button
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }
}

/**
 * Helper function to add operator input field to the form
 * Call this when showing the test form
 */
function addOperatorInputToForm() {
    // Check if operator field already exists
    if (document.getElementById('operatorInput')) {
        return;
    }
    
    // Find the form container (you may need to adjust this selector)
    const formContainer = document.querySelector('.form-grid');
    if (!formContainer) {
        return;
    }
    
    // Create operator input field
    const operatorField = document.createElement('div');
    operatorField.className = 'form-field';
    operatorField.innerHTML = `
        <label for="operatorInput">Operator Name:</label>
        <input type="text" id="operatorInput" class="form-input" placeholder="Enter your name" required>
    `;
    
    // Insert at the beginning of form
    formContainer.insertBefore(operatorField, formContainer.firstChild);
}

/**
 * Get operator name from input field
 */
function getOperatorFromInput() {
    const operatorInput = document.getElementById('operatorInput');
    return operatorInput ? operatorInput.value : null;
}
