/**
 * UI Helper Functions
 */

function showLoading(message = 'Loading...') {
    const loadingSection = document.getElementById('loadingSection');
    loadingSection.querySelector('p').textContent = message;
    loadingSection.style.display = 'block';
}

function hideLoading() {
    const loadingSection = document.getElementById('loadingSection');
    loadingSection.style.display = 'none';
}

function closeTestModal() {
    const testModal = document.getElementById('testModal');
    testModal.style.display = 'none';
    window.APP_STATE.currentTest = null;
    window.APP_STATE.currentFormData = null;
}

function forceCloseTestModal() {
    closeTestModal();
}

function newTest() {
    const testResultsSection = document.getElementById('testResultsSection');
    testResultsSection.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function printResults() {
    window.print();
}

// Close modal when clicking outside
window.onclick = function(event) {
    const testModal = document.getElementById('testModal');
    if (event.target === testModal) {
        const formElements = testModal.querySelectorAll('input, select, textarea');
        let hasData = false;
        
        for (let element of formElements) {
            if (element.type === 'file') {
                if (element.files && element.files.length > 0) {
                    hasData = true;
                    break;
                }
            } else if (element.value && element.value.trim()) {
                hasData = true;
                break;
            }
        }
        
        if (hasData) {
            if (confirm('You have entered data. Are you sure you want to close this form?')) {
                closeTestModal();
            }
        } else {
            closeTestModal();
        }
    }
}
