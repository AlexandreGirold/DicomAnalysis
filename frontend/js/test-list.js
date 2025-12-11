/**
 * Test List Management
 */

async function loadAvailableTests() {
    const testList = document.getElementById('testList');
    
    try {
        const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/execute`);
        if (!response.ok) {
            throw new Error('Failed to load tests');
        }
        
        const data = await response.json();
        window.APP_STATE.availableTests = data.available_tests;
        displayTestList(window.APP_STATE.availableTests);
        
    } catch (error) {
        console.error('Error loading tests:', error);
        testList.innerHTML = `
            <div class="error-message">
                <p>❌ Failed to load tests: ${error.message}</p>
                <button class="btn btn-primary" onclick="loadAvailableTests()">Retry</button>
            </div>
        `;
    }
}

function displayTestList(tests) {
    const testList = document.getElementById('testList');
    
    // Group tests by category
    const categorized = {
        daily: [],
        weekly: [],
        monthly: [],
        basic: []
    };
    
    Object.entries(tests).forEach(([testId, testInfo]) => {
        const category = testInfo.category || 'basic';
        categorized[category].push({ id: testId, info: testInfo });
    });
    
    // Build HTML with categories
    let html = '';
    
    const categoryLabels = {
        daily: '📅 Tests Quotidiens (Daily)',
        weekly: '📊 Tests Hebdomadaires (Weekly)',
        monthly: '📆 Tests Mensuels (Monthly)',
        basic: '🔧 Autres Tests (Other)'
    };
    
    // Display categories in order: daily, weekly, monthly, basic
    ['daily', 'weekly', 'monthly', 'basic'].forEach(category => {
        const testItems = categorized[category];
        if (testItems.length > 0) {
            html += `
                <div class="test-category">
                    <h3 class="category-title">${categoryLabels[category]}</h3>
                    <div class="test-category-items">
                        ${testItems.map(({ id, info }) => `
                            <div class="test-item" onclick="openTest('${id}')">
                                <span class="test-name">${info.class_name.replace('Test', '')}</span>
                                <span class="test-description">${info.description}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    });
    
    testList.innerHTML = html || '<p class="no-tests">Aucun test disponible</p>';
}
