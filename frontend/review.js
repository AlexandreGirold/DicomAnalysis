// API Configuration
const API_BASE_URL = window.location.origin;

// State
let allTests = [];
let filteredTests = [];
let selectedTest = null;
let currentFilters = {
    testType: '',
    specificTest: '',
    startDate: '',
    endDate: ''
};

// Test name mapping
const TEST_DISPLAY_NAMES = {
    'safety_systems': 'Safety Systems',
    'niveau_helium': 'Niveau Helium',
    'mlc_leaf_jaw': 'MLC Leaf & Jaw',
    'mvic': 'MVIC',
    'mvic_fente_v2': 'Précision du MLC',
    'leaf_position': 'Exactitude du MLC',
    'piqt': 'PIQT',
    'position_table_v2': 'Position Table V2',
    'alignement_laser': 'Alignement Laser',
    'quasar': 'Quasar',
    'indice_quality': 'Indice Quality'
};

// Test frequency mapping
const TEST_FREQUENCY = {
    'safety_systems': 'daily',
    'niveau_helium': 'weekly',
    'mlc_leaf_jaw': 'weekly',
    'mvic': 'weekly',
    'mvic_fente_v2': 'weekly',
    'leaf_position': 'weekly',
    'piqt': 'weekly',
    'position_table_v2': 'monthly',
    'alignement_laser': 'monthly',
    'quasar': 'monthly',
    'indice_quality': 'monthly'
};

// DOM Elements
const loadingSection = document.getElementById('loadingSection');
const testsContainer = document.getElementById('testsContainer');
const testDetailSection = document.getElementById('testDetailSection');
const testTypeFilter = document.getElementById('testTypeFilter');
const specificTestFilter = document.getElementById('specificTestFilter');
const startDateInput = document.getElementById('startDate');
const endDateInput = document.getElementById('endDate');
const applyFilterBtn = document.getElementById('applyFilterBtn');
const clearFilterBtn = document.getElementById('clearFilterBtn');
const deleteTestBtn = document.getElementById('deleteTestBtn');
const downloadReportBtn = document.getElementById('downloadReportBtn');
const detailVizSelect = document.getElementById('detailVizSelect');
const detailVisualizationDisplay = document.getElementById('detailVisualizationDisplay');
const detailSearchInput = document.getElementById('detailSearchInput');
const detailStatusFilter = document.getElementById('detailStatusFilter');
const detailResultsTableBody = document.getElementById('detailResultsTableBody');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadAllTests();
});

function setupEventListeners() {
    applyFilterBtn.addEventListener('click', applyFilters);
    clearFilterBtn.addEventListener('click', clearFilters);
    deleteTestBtn.addEventListener('click', deleteTest);
    downloadReportBtn.addEventListener('click', downloadTestReport);
    detailVizSelect.addEventListener('change', displayDetailVisualization);
    detailSearchInput.addEventListener('input', filterDetailTable);
    detailStatusFilter.addEventListener('change', filterDetailTable);
    
    // Update specific test dropdown when test type changes
    testTypeFilter.addEventListener('change', updateSpecificTestDropdown);
}

function updateSpecificTestDropdown() {
    const testType = testTypeFilter.value;
    const specificTest = specificTestFilter;
    
    // Enable/disable options based on test type filter
    const options = specificTest.querySelectorAll('option');
    options.forEach(option => {
        if (option.value === '') {
            option.disabled = false;
            return;
        }
        
        if (!testType) {
            option.disabled = false;
        } else {
            const frequency = TEST_FREQUENCY[option.value];
            option.disabled = frequency !== testType;
        }
    });
    
    // Reset selection if current selection is now disabled
    if (specificTest.selectedOptions[0].disabled) {
        specificTest.value = '';
    }
}

async function loadAllTests() {
    loadingSection.style.display = 'block';
    
    try {
        // Fetch all test type endpoints
        const testEndpoints = [
            { endpoint: 'safety-systems-sessions', type: 'safety_systems' },
            { endpoint: 'niveau-helium-sessions', type: 'niveau_helium' },
            { endpoint: 'mlc-test-sessions', type: 'mlc_leaf_jaw' },
            { endpoint: 'mvic-test-sessions', type: 'mvic' },
            { endpoint: 'mvic-fente-v2-sessions', type: 'mvic_fente_v2' },
            { endpoint: 'leaf-position-sessions', type: 'leaf_position' },
            { endpoint: 'piqt-sessions', type: 'piqt' },
            { endpoint: 'position-table-sessions', type: 'position_table_v2' },
            { endpoint: 'alignement-laser-sessions', type: 'alignement_laser' },
            { endpoint: 'quasar-sessions', type: 'quasar' },
            { endpoint: 'indice-quality-sessions', type: 'indice_quality' }
        ];
        
        const fetchPromises = testEndpoints.map(async ({ endpoint, type }) => {
            try {
                const response = await fetch(`${API_BASE_URL}/${endpoint}?limit=1000`);
                if (!response.ok) {
                    console.warn(`Failed to fetch ${endpoint}: ${response.status}`);
                    return [];
                }
                const data = await response.json();
                const tests = data.tests || data || [];
                return tests.map(test => ({
                    ...test,
                    test_type: type,
                    test_frequency: TEST_FREQUENCY[type]
                }));
            } catch (error) {
                console.error(`Error loading ${type}:`, error);
                return [];
            }
        });
        
        const results = await Promise.all(fetchPromises);
        allTests = results.flat().sort((a, b) => {
            return new Date(b.test_date || b.upload_date) - new Date(a.test_date || a.upload_date);
        });
        
        console.log(`Loaded ${allTests.length} tests total`);
        
        // Apply initial filter (show all)
        applyFilters();
        
    } catch (error) {
        console.error('Error loading tests:', error);
        testsContainer.innerHTML = '<p class="placeholder-text">Erreur lors du chargement des tests. Consultez la console pour plus de détails.</p>';
    } finally {
        loadingSection.style.display = 'none';
    }
}

function applyFilters() {
    // Get filter values
    currentFilters.testType = testTypeFilter.value;
    currentFilters.specificTest = specificTestFilter.value;
    currentFilters.startDate = startDateInput.value;
    currentFilters.endDate = endDateInput.value;
    
    // Filter tests
    filteredTests = allTests.filter(test => {
        // Filter by test frequency (daily/weekly/monthly)
        if (currentFilters.testType && test.test_frequency !== currentFilters.testType) {
            return false;
        }
        
        // Filter by specific test
        if (currentFilters.specificTest && test.test_type !== currentFilters.specificTest) {
            return false;
        }
        
        // Filter by date range
        const testDate = new Date(test.test_date);
        if (currentFilters.startDate) {
            const startDate = new Date(currentFilters.startDate);
            if (testDate < startDate) return false;
        }
        if (currentFilters.endDate) {
            const endDate = new Date(currentFilters.endDate);
            endDate.setHours(23, 59, 59, 999);
            if (testDate > endDate) return false;
        }
        
        return true;
    });
    
    displayTests();
    updateStats();
}

function clearFilters() {
    testTypeFilter.value = '';
    specificTestFilter.value = '';
    startDateInput.value = '';
    endDateInput.value = '';
    
    currentFilters = {
        testType: '',
        specificTest: '',
        startDate: '',
        endDate: ''
    };
    
    updateSpecificTestDropdown();
    applyFilters();
}

function displayTests() {
    if (filteredTests.length === 0) {
        testsContainer.innerHTML = '<p class="placeholder-text">Aucun test ne correspond aux filtres actuels</p>';
        return;
    }
    
    testsContainer.innerHTML = filteredTests.map(test => {
        const testDate = test.test_date ? 
            new Date(test.test_date).toLocaleDateString('fr-FR', { 
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit'
            }) : 'Unknown';
        
        const uploadDate = test.upload_date ? 
            new Date(test.upload_date).toLocaleDateString('fr-FR', { 
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit'
            }) : 'N/A';
        
        const result = (test.overall_result || 'N/A').toUpperCase();
        const testDisplayName = TEST_DISPLAY_NAMES[test.test_type] || test.test_type.toUpperCase();
        const frequencyBadge = test.test_frequency ? 
            `<span class="frequency-badge ${test.test_frequency}">${test.test_frequency}</span>` : '';
        
        // Determine result class
        let resultClass = 'result-na';
        if (result.includes('PASS')) resultClass = 'result-pass';
        else if (result.includes('FAIL')) resultClass = 'result-fail';
        else if (result.includes('WARNING')) resultClass = 'result-warning';
        else if (result.includes('COMPLETE')) resultClass = 'result-complete';
        
        return `
            <div class="test-item-compact" onclick="viewTestDetail(${test.id}, '${test.test_type}')">
                <div class="test-item-id">#${test.id}</div>
                <div class="test-item-name">${testDisplayName}</div>
                <div>${frequencyBadge}</div>
                <div class="test-item-operator">👤 ${test.operator}</div>
                <div class="test-item-date">📅 ${testDate}</div>
                <div class="test-item-date">⬆️ ${uploadDate}</div>
                <div class="test-item-result ${resultClass}">${result}</div>
            </div>
        `;
    }).join('');
}

function updateStats() {
    // Update shown tests count
    document.getElementById('shownTests').textContent = filteredTests.length;
    
    // Update current test type
    let testTypeText = 'Tous';
    if (currentFilters.specificTest) {
        testTypeText = TEST_DISPLAY_NAMES[currentFilters.specificTest];
    } else if (currentFilters.testType) {
        testTypeText = currentFilters.testType.charAt(0).toUpperCase() + currentFilters.testType.slice(1);
    }
    document.getElementById('currentTestType').textContent = testTypeText;
    
    // Update current date range
    let dateRangeText = 'Toutes les dates';
    if (currentFilters.startDate || currentFilters.endDate) {
        const start = currentFilters.startDate || '...';
        const end = currentFilters.endDate || '...';
        dateRangeText = `${start} à ${end}`;
    }
    document.getElementById('currentDateRange').textContent = dateRangeText;
}

async function viewTestDetail(testId, testType) {
    loadingSection.style.display = 'block';
    
    try {
        // Map test type to endpoint
        const endpointMap = {
            'safety_systems': 'safety-systems-sessions',
            'niveau_helium': 'niveau-helium-sessions',
            'mlc_leaf_jaw': 'mlc-leaf-jaw-sessions',
            'mvic': 'mvic-test-sessions',
            'mvic_fente_v2': 'mvic-fente-v2-sessions',
            'leaf_position': 'leaf-position-sessions',
            'piqt': 'piqt-sessions',
            'position_table': 'position-table-sessions',
            'alignement_laser': 'alignement-laser-sessions',
            'quasar': 'quasar-sessions',
            'indice_quality': 'indice-quality-sessions'
        };
        
        const endpoint = endpointMap[testType];
        if (!endpoint) {
            throw new Error(`Unknown test type: ${testType}`);
        }
        
        const response = await fetch(`${API_BASE_URL}/${endpoint}/${testId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch test: ${response.statusText}`);
        }
        
        const test = await response.json();
        test.test_type = testType;
        
        selectedTest = test;
        displayTestDetail(test);
        
        // Scroll to detail section
        testDetailSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error loading test detail:', error);
        alert(`Error loading test details: ${error.message}`);
    } finally {
        loadingSection.style.display = 'none';
    }
}

function displayTestDetail(test) {
    testDetailSection.style.display = 'block';
    
    const testDisplayName = TEST_DISPLAY_NAMES[test.test_type] || test.test_type.toUpperCase();
    
    // Update info
    document.getElementById('detailTestId').textContent = `${testDisplayName} #${test.id}`;
    document.getElementById('detailFilename').textContent = `Operator: ${test.operator}`;
    
    const testDate = test.test_date ? 
        new Date(test.test_date).toLocaleString() : 
        'Unknown';
    document.getElementById('detailDate').textContent = testDate;
    
    const uploadDate = new Date(test.upload_date).toLocaleString();
    document.getElementById('detailUploadDate').textContent = uploadDate;
    
    const summaryCard = document.querySelector('.summary-card');
    
    // Helper function to format numbers
    const fmt = (val) => val != null ? (typeof val === 'number' ? val.toFixed(2) : val) : 'N/A';
    
    // Display based on test type
    if (test.test_type === 'mvic') {
        // MVIC-Champ test display
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats MVIC-Champ</h3>
            <div class="summary-grid" style="font-size: 1.1em !important; gap: 1px; line-height: 1.0;">
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Image 1:</span>
                    <span class="value" style="font-size: 1em !important;">${fmt(test.image1.width_mm)}×${fmt(test.image1.height_mm)}mm, angle: ${fmt(test.image1.avg_angle)}° (σ=${fmt(test.image1.angle_std_dev)}°)</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Image 2:</span>
                    <span class="value" style="font-size: 1em !important;">${fmt(test.image2.width_mm)}×${fmt(test.image2.height_mm)}mm, angle: ${fmt(test.image2.avg_angle)}° (σ=${fmt(test.image2.angle_std_dev)}°)</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Image 3:</span>
                    <span class="value" style="font-size: 1em !important;">${fmt(test.image3.width_mm)}×${fmt(test.image3.height_mm)}mm, angle: ${fmt(test.image3.avg_angle)}° (σ=${fmt(test.image3.angle_std_dev)}°)</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Image 4:</span>
                    <span class="value" style="font-size: 1em !important;">${fmt(test.image4.width_mm)}×${fmt(test.image4.height_mm)}mm, angle: ${fmt(test.image4.avg_angle)}° (σ=${fmt(test.image4.angle_std_dev)}°)</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Image 5:</span>
                    <span class="value" style="font-size: 1em !important;">${fmt(test.image5.width_mm)}×${fmt(test.image5.height_mm)}mm, angle: ${fmt(test.image5.avg_angle)}° (σ=${fmt(test.image5.angle_std_dev)}°)</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Résultat:</span>
                    <span class="value" style="font-size: 1em !important;"><strong>${test.overall_result || 'N/A'}</strong></span>
                </div>
            </div>
            ${test.notes ? `<div style="font-size: 0.70em !important; margin-top: 2px;"><strong>Notes :</strong> ${test.notes}</div>` : ''}
            <div style="margin-top: 10px; font-size: 0.85em;">
                <a href="result_displays/mvic_display.html?id=${test.id}" target="_blank" style="color: #007bff; text-decoration: none;">
                    📊 View Full MVIC-Champ Report →
                </a>
            </div>
        `;
        // Hide visualizations and results table for MVIC-Champ tests
        document.querySelector('.visualization-section').style.display = 'none';
        document.querySelector('.results-table-section').style.display = 'none';
    } else if (test.test_type === 'piqt') {
        // PIQT test display
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats PIQT</h3>
            <div class="summary-grid" style="font-size: 1.1em !important; gap: 1px; line-height: 1.0;">
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Résultat:</span>
                    <span class="value" style="font-size: 1em !important;"><strong>${test.overall_result || 'N/A'}</strong></span>
                </div>
            </div>
            ${test.notes ? `<div style="font-size: 0.70em !important; margin-top: 2px;"><strong>Notes :</strong> ${test.notes}</div>` : ''}
            <div style="margin-top: 10px; font-size: 0.85em;">
                <a href="result_displays/piqt_display.html?id=${test.id}" target="_blank" style="color: #007bff; text-decoration: none;">
                    📊 View Full PIQT Report →
                </a>
            </div>
        `;
        // Hide visualizations and results table for PIQT tests in review page
        document.querySelector('.visualization-section').style.display = 'none';
        document.querySelector('.results-table-section').style.display = 'none';
    } else if (test.test_type === 'mlc_leaf_jaw') {
        // MLC test display
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats MLC</h3>
            <div class="summary-grid" style="font-size: 1.1em !important; gap: 1px; line-height: 1.0;">
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Centre:</span>
                    <span class="value" style="font-size: 1em !important;">U=${fmt(test.test1_center.center_u)} px, V=${fmt(test.test1_center.center_v)} px</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Jaw:</span>
                    <span class="value" style="font-size: 1em !important;">X1=${fmt(test.test2_jaw.jaw_x1_mm)} mm, X2=${fmt(test.test2_jaw.jaw_x2_mm)} mm</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Lames haut:</span>
                    <span class="value" style="font-size: 1em !important;">moyenne = ${fmt(test.test3_blade_top.average)} mm, écart type = ${fmt(test.test3_blade_top.std_dev)} mm</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Lames bas:</span>
                    <span class="value" style="font-size: 1em !important;">moyenne = ${fmt(test.test4_blade_bottom.average)} mm, écart type = ${fmt(test.test4_blade_bottom.std_dev)} mm</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Angle:</span>
                    <span class="value" style="font-size: 1em !important;">moyenne = ${fmt(test.test5_angle.average_angle)}°</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Résultat:</span>
                    <span class="value" style="font-size: 1em !important;"><strong>${test.overall_result || 'N/A'}</strong></span>
                </div>
            </div>
            ${test.notes ? `<div style="font-size: 0.70em !important; margin-top: 2px;"><strong>Notes :</strong> ${test.notes}</div>` : ''}
            <div style="margin-top: 10px; font-size: 0.85em;">
                <a href="result_displays/mlc_display.html?id=${test.id}" target="_blank" style="color: #007bff; text-decoration: none;">
                    📊 View Full MLC Report →
                </a>
            </div>
        `;
        // Hide visualizations and results table for MLC tests
        document.querySelector('.visualization-section').style.display = 'none';
        document.querySelector('.results-table-section').style.display = 'none';
    } else if (test.test_type === 'mvic_fente_v2') {
        // MVIC Fente test display
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats MVIC Fente</h3>
            <div class="summary-grid" style="font-size: 1.1em !important; gap: 1px; line-height: 1.0;">
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Résultat:</span>
                    <span class="value" style="font-size: 1em !important;"><strong>${test.overall_result || 'N/A'}</strong></span>
                </div>
            </div>
            ${test.notes ? `<div style="font-size: 0.70em !important; margin-top: 2px;"><strong>Notes :</strong> ${test.notes}</div>` : ''}
            <div style="margin-top: 10px; font-size: 0.85em;">
                <a href="result_displays/mvic_fente_v2_display.html?id=${test.id}" target="_blank" style="color: #007bff; text-decoration: none;">
                    📊 View Full MVIC Fente Report →
                </a>
            </div>
        `;
        // Hide visualizations and results table for MVIC Fente tests
        document.querySelector('.visualization-section').style.display = 'none';
        document.querySelector('.results-table-section').style.display = 'none';
    } else if (test.test_type === 'leaf_position') {
        // Leaf Position test display
        const bladeResults = test.blade_results || [];
        const totalBlades = bladeResults.length;
        const okBlades = bladeResults.filter(b => b.is_valid === 'OK').length;
        const outOfTolerance = bladeResults.filter(b => b.is_valid === 'OUT_OF_TOLERANCE').length;
        const closedBlades = bladeResults.filter(b => b.is_valid === 'CLOSED').length;
        
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats Leaf Position</h3>
            <div class="summary-grid" style="font-size: 1.1em !important; gap: 1px; line-height: 1.0;">
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Total Lames:</span>
                    <span class="value" style="font-size: 1em !important;">${totalBlades}</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">OK:</span>
                    <span class="value" style="font-size: 1em !important; color: green;">${okBlades}</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Hors tolérance:</span>
                    <span class="value" style="font-size: 1em !important; color: orange;">${outOfTolerance}</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Fermées:</span>
                    <span class="value" style="font-size: 1em !important; color: gray;">${closedBlades}</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Résultat:</span>
                    <span class="value" style="font-size: 1em !important;"><strong>${test.overall_result || 'N/A'}</strong></span>
                </div>
            </div>
            ${test.notes ? `<div style="font-size: 0.70em !important; margin-top: 2px;"><strong>Notes :</strong> ${test.notes}</div>` : ''}
            <div style="margin-top: 10px; font-size: 0.85em;">
                <a href="result_displays/leaf_position_display.html?id=${test.id}" target="_blank" style="color: #007bff; text-decoration: none;">
                    📊 View Full Leaf Position Report →
                </a>
            </div>
        `;
        
        // Hide visualizations and results table - show in full report instead
        document.querySelector('.visualization-section').style.display = 'none';
        document.querySelector('.results-table-section').style.display = 'none';
    } else if (test.test_type === 'niveau_helium') {
        // Niveau Helium test display
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats Niveau Helium</h3>
            <div class="summary-grid" style="font-size: 1.1em !important; gap: 1px; line-height: 1.0;">
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Niveau Helium:</span>
                    <span class="value" style="font-size: 1em !important;">${fmt(test.helium_level)}%</span>
                </div>
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Résultat:</span>
                    <span class="value" style="font-size: 1em !important;"><strong>${test.overall_result || 'N/A'}</strong></span>
                </div>
            </div>
            ${test.notes ? `<div style="font-size: 0.70em !important; margin-top: 2px;"><strong>Notes :</strong> ${test.notes}</div>` : ''}
            <div style="margin-top: 10px; font-size: 0.85em;">
                <a href="result_displays/niveau_helium_display.html?id=${test.id}" target="_blank" style="color: #007bff; text-decoration: none;">
                    📊 View Full Niveau Helium Report →
                </a>
            </div>
        `;
        // Hide visualizations and results table for Niveau Helium tests
        document.querySelector('.visualization-section').style.display = 'none';
        document.querySelector('.results-table-section').style.display = 'none';
    } else {
        // Default display for other test types
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats</h3>
            <div class="summary-grid" style="font-size: 1.1em !important; gap: 1px; line-height: 1.0;">
                <div class="summary-item" style="padding: 6px; padding-left: 8px; padding-bottom: 6px;">
                    <span class="label">Résultat:</span>
                    <span class="value" style="font-size: 1em !important;"><strong>${test.overall_result || 'N/A'}</strong></span>
                </div>
            </div>
            ${test.notes ? `<div style="font-size: 0.70em !important; margin-top: 2px;"><strong>Notes :</strong> ${test.notes}</div>` : ''}
        `;
        // Hide visualizations and results table for unknown test types
        document.querySelector('.visualization-section').style.display = 'none';
        document.querySelector('.results-table-section').style.display = 'none';
    }
}

function populateDetailTable(results) {
    detailResultsTableBody.innerHTML = results.map(r => {
        let statusClass = 'status-ok';
        let statusText = r.status;
        
        if (r.status.includes('OUT_OF_TOLERANCE')) {
            statusClass = 'status-warning';
            statusText = 'Out of Tolerance';
        } else if (r.status === 'CLOSED') {
            statusClass = 'status-closed';
            statusText = 'Closed';
        } else if (r.status === 'OK') {
            statusClass = 'status-ok';
            statusText = 'OK';
        }
        
        return `
            <tr>
                <td>${r.blade_pair}</td>
                <td>${r.distance_sup_mm !== null ? r.distance_sup_mm.toFixed(3) : '-'}</td>
                <td>${r.distance_inf_mm !== null ? r.distance_inf_mm.toFixed(3) : '-'}</td>
                <td>${r.field_size_mm !== null ? r.field_size_mm.toFixed(3) : '-'}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            </tr>
        `;
    }).join('');
}

function displayDetailVisualization() {
    const selectedViz = detailVizSelect.value;
    
    if (!selectedViz) {
        detailVisualizationDisplay.innerHTML = '<p class="placeholder-text">No visualizations available</p>';
        return;
    }
    
    detailVisualizationDisplay.innerHTML = `
        <img src="${API_BASE_URL}/visualization/${selectedViz}" alt="Blade Detection Visualization">
    `;
}

function filterDetailTable() {
    const searchTerm = detailSearchInput.value.toLowerCase();
    const statusValue = detailStatusFilter.value;
    
    const rows = detailResultsTableBody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const bladePair = row.cells[0].textContent.toLowerCase();
        const status = row.cells[4].textContent.trim();
        
        const matchesSearch = bladePair.includes(searchTerm);
        const matchesStatus = !statusValue || status.includes(statusValue.replace('_', ' '));
        
        row.style.display = matchesSearch && matchesStatus ? '' : 'none';
    });
}

function closeTestDetail() {
    testDetailSection.style.display = 'none';
    selectedTest = null;
}

async function deleteTest() {
    if (!selectedTest) return;
    
    const testDisplayName = TEST_DISPLAY_NAMES[selectedTest.test_type] || selectedTest.test_type.toUpperCase();
    
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le Test ${testDisplayName} #${selectedTest.id} ?\n\nCette action est irréversible.`)) {
        return;
    }
    
    try {
        // Map test type to endpoint
        const endpointMap = {
            'safety_systems': 'safety-systems-sessions',
            'niveau_helium': 'niveau-helium-sessions',
            'mlc_leaf_jaw': 'mlc-test-sessions',
            'mvic': 'mvic-test-sessions',
            'mvic_fente_v2': 'mvic-fente-v2-sessions',
            'leaf_position': 'leaf-position-sessions',
            'piqt': 'piqt-sessions',
            'position_table_v2': 'position-table-sessions',
            'alignement_laser': 'alignement-laser-sessions',
            'quasar': 'quasar-sessions',
            'indice_quality': 'indice-quality-sessions'
        };
        
        const endpoint = endpointMap[selectedTest.test_type];
        const response = await fetch(`${API_BASE_URL}/${endpoint}/${selectedTest.id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete test');
        }
        
        alert(`✅ Test ${testDisplayName} supprimé avec succès`);
        
        // Close detail view and reload tests
        closeTestDetail();
        loadAllTests();
        
    } catch (error) {
        console.error('Error deleting test:', error);
        alert('Erreur lors de la suppression du test');
    }
}

async function downloadTestReport() {
    if (!selectedTest) {
        alert('Veuillez d\'abord sélectionner un test');
        return;
    }
    
    alert('Génération de rapport pour les tests individuels non encore implémentée');
}
