// API Configuration
const API_BASE_URL = window.location.origin;  // Use same origin as the page

// State
let allTests = [];
let selectedTest = null;

// DOM Elements
const loadingSection = document.getElementById('loadingSection');
const testsContainer = document.getElementById('testsContainer');
const testDetailSection = document.getElementById('testDetailSection');
const filterBtn = document.getElementById('filterBtn');
const clearFilterBtn = document.getElementById('clearFilterBtn');
const startDateInput = document.getElementById('startDate');
const endDateInput = document.getElementById('endDate');
const deleteTestBtn = document.getElementById('deleteTestBtn');
const detailVizSelect = document.getElementById('detailVizSelect');
const detailVisualizationDisplay = document.getElementById('detailVisualizationDisplay');
const detailSearchInput = document.getElementById('detailSearchInput');
const detailStatusFilter = document.getElementById('detailStatusFilter');
const detailResultsTableBody = document.getElementById('detailResultsTableBody');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadTests();
    loadDatabaseStats();
});

function setupEventListeners() {
    filterBtn.addEventListener('click', applyDateFilter);
    clearFilterBtn.addEventListener('click', clearDateFilter);
    deleteTestBtn.addEventListener('click', deleteTest);
    detailVizSelect.addEventListener('change', displayDetailVisualization);
    detailSearchInput.addEventListener('input', filterDetailTable);
    detailStatusFilter.addEventListener('change', filterDetailTable);
}

async function loadDatabaseStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/database/stats`);
        const stats = await response.json();
        
        document.getElementById('totalTests').textContent = stats.total_tests || 0;
        document.getElementById('totalMeasurements').textContent = stats.total_blade_measurements || 0;
        
        if (stats.oldest_test_date && stats.newest_test_date) {
            const oldest = new Date(stats.oldest_test_date).toLocaleDateString();
            const newest = new Date(stats.newest_test_date).toLocaleDateString();
            document.getElementById('dateRange').textContent = `${oldest} - ${newest}`;
        } else {
            document.getElementById('dateRange').textContent = 'No data';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadTests(startDate = null, endDate = null) {
    loadingSection.style.display = 'block';
    
    try {
        let url = `${API_BASE_URL}/tests?limit=100`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        allTests = data.tests;
        displayTests();
    } catch (error) {
        console.error('Error loading tests:', error);
        testsContainer.innerHTML = '<p class="placeholder-text">Error loading tests</p>';
    } finally {
        loadingSection.style.display = 'none';
    }
}

function displayTests() {
    if (allTests.length === 0) {
        testsContainer.innerHTML = '<p class="placeholder-text">No tests found. Run some analyses first!</p>';
        return;
    }
    
    testsContainer.innerHTML = allTests.map(test => {
        const testDate = test.file_creation_date ? 
            new Date(test.file_creation_date).toLocaleString() : 
            'Unknown';
        
        const uploadDate = new Date(test.upload_date).toLocaleString();
        
        return `
            <div class="test-card" onclick="viewTestDetail(${test.id})">
                <h4>Test #${test.id}</h4>
                <div class="test-card-info">📄 ${test.filename}</div>
                <div class="test-card-info">📅 Test Date: ${testDate}</div>
                <div class="test-card-info">⬆️ Upload Date: ${uploadDate}</div>
                <div class="test-card-summary">
                    <span>
                        <span class="label">Total</span>
                        <span class="value">${test.summary.total_blades}</span>
                    </span>
                    <span style="color: var(--success-color)">
                        <span class="label">OK</span>
                        <span class="value">${test.summary.ok_blades}</span>
                    </span>
                    <span style="color: var(--warning-color)">
                        <span class="label">Out</span>
                        <span class="value">${test.summary.out_of_tolerance}</span>
                    </span>
                    <span style="color: var(--info-color)">
                        <span class="label">Closed</span>
                        <span class="value">${test.summary.closed_blades}</span>
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

async function viewTestDetail(testId) {
    loadingSection.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE_URL}/tests/${testId}`);
        const test = await response.json();
        
        selectedTest = test;
        displayTestDetail(test);
        
        // Scroll to detail section
        testDetailSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error loading test detail:', error);
        alert('Error loading test details');
    } finally {
        loadingSection.style.display = 'none';
    }
}

function displayTestDetail(test) {
    testDetailSection.style.display = 'block';
    
    // Update info
    document.getElementById('detailTestId').textContent = test.id;
    document.getElementById('detailFilename').textContent = test.filename;
    
    const testDate = test.file_creation_date ? 
        new Date(test.file_creation_date).toLocaleString() : 
        'Unknown';
    document.getElementById('detailDate').textContent = testDate;
    
    const uploadDate = new Date(test.upload_date).toLocaleString();
    document.getElementById('detailUploadDate').textContent = uploadDate;
    
    // Update summary
    document.getElementById('detailTotalBlades').textContent = test.summary.total_blades;
    document.getElementById('detailOkBlades').textContent = test.summary.ok_blades;
    document.getElementById('detailOutOfTolerance').textContent = test.summary.out_of_tolerance;
    document.getElementById('detailClosedBlades').textContent = test.summary.closed_blades;
    
    // Populate visualization dropdown
    detailVizSelect.innerHTML = '';
    if (test.visualization) {
        const vizList = Array.isArray(test.visualization) ? test.visualization : [test.visualization];
        vizList.forEach((viz, index) => {
            const option = document.createElement('option');
            option.value = viz;
            option.textContent = `Visualization ${index + 1}`;
            detailVizSelect.appendChild(option);
        });
        
        // Display first visualization
        if (vizList.length > 0) {
            detailVizSelect.value = vizList[0];
            displayDetailVisualization();
        }
    } else {
        detailVizSelect.innerHTML = '<option value="">-- No visualizations available --</option>';
        detailVisualizationDisplay.innerHTML = '<p class="placeholder-text">No visualizations available for this test</p>';
    }
    
    // Populate results table
    populateDetailTable(test.results);
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

function applyDateFilter() {
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    
    if (!startDate && !endDate) {
        alert('Please select at least one date');
        return;
    }
    
    loadTests(startDate, endDate);
}

function clearDateFilter() {
    startDateInput.value = '';
    endDateInput.value = '';
    loadTests();
}

async function deleteTest() {
    if (!selectedTest) return;
    
    if (!confirm(`Are you sure you want to delete Test #${selectedTest.id}?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/tests/${selectedTest.id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete test');
        }
        
        alert('✅ Test deleted successfully');
        
        // Close detail view and reload tests
        closeTestDetail();
        loadTests();
        loadDatabaseStats();
        
    } catch (error) {
        console.error('Error deleting test:', error);
        alert('Error deleting test');
    }
}
