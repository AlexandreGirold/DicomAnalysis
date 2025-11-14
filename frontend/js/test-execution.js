/**
 * Test Execution Logic
 */

async function openTest(testId) {
    try {
        window.APP_STATE.currentTest = testId;
        
        showLoading('Loading test form...');
        
        console.log(`Fetching form for test: ${testId}`);
        const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/basic-tests/${testId}/form`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Form fetch failed:', response.status, errorText);
            throw new Error(`Failed to load test form: ${response.status} - ${errorText}`);
        }
        
        window.APP_STATE.currentFormData = await response.json();
        console.log('Form data loaded:', window.APP_STATE.currentFormData);
        hideLoading();
        
        // Populate modal
        const modalTitle = document.getElementById('modalTitle');
        const modalDescription = document.getElementById('modalDescription');
        const testModal = document.getElementById('testModal');
        
        modalTitle.textContent = window.APP_STATE.currentFormData.title;
        modalDescription.textContent = window.APP_STATE.currentFormData.description;
        
        // Build form fields
        buildFormFields(window.APP_STATE.currentFormData.fields);
        
        // Show modal
        testModal.style.display = 'block';
        
    } catch (error) {
        hideLoading();
        console.error('Error opening test:', error);
        alert(`Failed to open test: ${error.message}`);
    }
}

async function handleTestSubmission(e) {
    e.preventDefault();
    
    try {
        const testId = window.APP_STATE.currentTest;
        if (!testId) {
            throw new Error('No test selected. Please close this modal and select a test again.');
        }
        
        console.log('Current test:', testId);
        console.log('Current form data:', window.APP_STATE.currentFormData);
        
        const testForm = document.getElementById('testForm');
        const capturedFormData = new FormData(testForm);
        
        console.log('Captured form data entries:');
        for (let [key, value] of capturedFormData.entries()) {
            console.log(`${key}:`, value);
        }
        
        // Determine if this is a file upload test
        let isFileUploadTest = false;
        if (window.APP_STATE.currentFormData && window.APP_STATE.currentFormData.file_upload) {
            isFileUploadTest = true;
        } else if (testId === 'mlc_leaf_jaw') {
            isFileUploadTest = true;
        }
        
        console.log('Is file upload test:', isFileUploadTest);
        
        // Validate based on test type
        if (isFileUploadTest) {
            const fileInput = document.querySelector('input[type="file"]');
            if (!fileInput || !fileInput.files.length) {
                throw new Error('Please select at least one file');
            }
            
            const operatorValue = capturedFormData.get('operator');
            if (!operatorValue || !operatorValue.trim()) {
                throw new Error('Please enter operator name');
            }
        } else {
            const operatorValue = capturedFormData.get('operator');
            if (!operatorValue || !operatorValue.trim()) {
                throw new Error('Please enter operator name');
            }
        }
        
        showLoading('Executing test...');
        closeTestModal();
        
        if (isFileUploadTest) {
            await handleFileUploadTest(capturedFormData, testId);
        } else {
            await handleRegularTest(capturedFormData, testId);
        }
        
    } catch (error) {
        hideLoading();
        console.error('Error executing test:', error);
        alert(`Test execution failed: ${error.message}`);
    }
}

async function handleRegularTest(capturedFormData, testId) {
    const data = {};
    for (let [key, value] of capturedFormData.entries()) {
        const inputElement = document.querySelector(`input[name="${key}"]`);
        if (inputElement && inputElement.type === 'number') {
            data[key] = parseFloat(value);
        } else {
            data[key] = value;
        }
    }
    
    console.log('Submitting regular test data:', data);
    
    const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/basic-tests/${testId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Test execution failed');
    }
    
    const result = await response.json();
    hideLoading();
    
    displayTestResults(result);
}

async function handleFileUploadTest(capturedFormData, testId) {
    console.log('Submitting file upload test');
    
    const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/basic-tests/mlc-leaf-jaw`, {
        method: 'POST',
        body: capturedFormData
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        console.error('Upload error:', errorText);
        throw new Error(`Upload failed: ${errorText}`);
    }
    
    const result = await response.json();
    hideLoading();
    
    displayTestResults(result);
}

// Initialize form submission handler
document.addEventListener('DOMContentLoaded', () => {
    const testForm = document.getElementById('testForm');
    if (testForm) {
        testForm.addEventListener('submit', handleTestSubmission);
    }
});
