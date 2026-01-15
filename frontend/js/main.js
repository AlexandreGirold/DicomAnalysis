/**
 * Main Application Entry Point
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized');
    
    // Ensure APP_CONFIG is available
    if (!window.APP_CONFIG) {
        console.error('APP_CONFIG not initialized');
        const testList = document.getElementById('testList');
        if (testList) {
            testList.innerHTML = `
                <div class="error-message">
                    <p>❌ Configuration error. Please refresh the page.</p>
                    <button class="btn btn-primary" onclick="location.reload()">Refresh</button>
                </div>
            `;
        }
        return;
    }
    
    loadAvailableTests();
});
