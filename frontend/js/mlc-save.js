/**
 * MLC/MVIC Test Database Save Functionality
 * Handles saving MLC and MVIC test results to the database
 */

// Store current test data globally
window.CURRENT_MLC_TEST_DATA = null;
window.CURRENT_TEST_TYPE = null; // 'mlc' or 'mvic'

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
    
    // Extract data from visualizations (contains statistics for each image)
    if (analysisResult.visualizations && Array.isArray(analysisResult.visualizations)) {
        console.log('Processing MVIC visualizations:', analysisResult.visualizations);
        
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
    return mvicData;
}

/**
 * Show save button and store test data
 */
function enableMLCTestSave(analysisResult, testType = 'mlc') {
    console.log('enableMLCTestSave called with type:', testType, 'result:', analysisResult);
    
    // Detect test type from test_name if not provided
    if (!testType || testType === 'mlc') {
        if (analysisResult.test_name && analysisResult.test_name.includes('MVIC')) {
            testType = 'mvic';
        } else if (analysisResult.test_name && analysisResult.test_name.includes('MLC')) {
            testType = 'mlc';
        }
    }
    
    console.log('Final test type:', testType);
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
    if (testType === 'mvic') {
        testData = prepareMVICTestData(analysisResult);
    } else {
        testData = prepareMLCTestData(analysisResult);
    }
    
    if (!testData) {
        console.warn('Could not prepare test data - button shown but data not prepared');
        // Still show button with minimal data
        window.CURRENT_MLC_TEST_DATA = {
            test_date: new Date().toISOString(),
            operator: null,
            overall_result: analysisResult.overall_result || 'UNKNOWN',
            notes: 'Partial data - manual entry may be needed'
        };
        return;
    }
    
    console.log('Test data prepared:', testData);
    
    // Store globally
    window.CURRENT_MLC_TEST_DATA = testData;
}

/**
 * Save test to database (routes to MLC or MVIC endpoint based on test type)
 */
async function saveMLCTestToDatabase() {
    if (!window.CURRENT_MLC_TEST_DATA) {
        alert('No test data available to save');
        return;
    }
    
    const testData = window.CURRENT_MLC_TEST_DATA;
    const testType = window.CURRENT_TEST_TYPE || 'mlc';
    
    console.log('Saving test with type:', testType, 'data:', testData);
    
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
        // Choose endpoint based on test type
        const endpoint = testType === 'mvic' 
            ? `${window.APP_CONFIG.API_BASE_URL}/mvic-test-sessions`
            : `${window.APP_CONFIG.API_BASE_URL}/mlc-test-sessions`;
        
        console.log('Saving to endpoint:', endpoint);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save test');
        }
        
        const result = await response.json();
        
        const testTypeName = testType === 'mvic' ? 'MVIC' : 'MLC';
        alert(`✅ ${testTypeName} test saved successfully!\n\nTest ID: ${result.test_id}\n\nYou can view this test in the Review page.`);
        
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
