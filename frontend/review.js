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
const downloadReportBtn = document.getElementById('downloadReportBtn');
const generateTrendReportBtn = document.getElementById('generateTrendReportBtn');
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
    downloadReportBtn.addEventListener('click', downloadTestReport);
    generateTrendReportBtn.addEventListener('click', generateTrendReport);
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
        // Build query parameters
        let queryParams = 'limit=100';
        if (startDate) queryParams += `&start_date=${startDate}`;
        if (endDate) queryParams += `&end_date=${endDate}`;
        
        // Load both MLC and MVIC tests
        const [mlcResponse, mvicResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/mlc-test-sessions?${queryParams}`),
            fetch(`${API_BASE_URL}/mvic-test-sessions?${queryParams}`)
        ]);
        
        const mlcData = await mlcResponse.json();
        const mvicData = await mvicResponse.json();
        
        // Tag tests with their type
        const mlcTests = (mlcData.tests || []).map(test => ({...test, test_type: 'mlc'}));
        const mvicTests = (mvicData.tests || []).map(test => ({...test, test_type: 'mvic'}));
        
        // Combine and sort by date (most recent first)
        allTests = [...mlcTests, ...mvicTests].sort((a, b) => {
            return new Date(b.test_date) - new Date(a.test_date);
        });
        
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
        const testDate = test.test_date ? 
            new Date(test.test_date).toLocaleString() : 
            'Unknown';
        
        const uploadDate = new Date(test.upload_date).toLocaleString();
        const result = test.overall_result || 'N/A';
        const testTypeName = test.test_type === 'mvic' ? 'MVIC' : 'MLC';
        
        return `
            <div class="test-card" onclick="viewTestDetail(${test.id}, '${test.test_type}')">
                <h4>${testTypeName} Test #${test.id}</h4>
                <div class="test-card-info">👤 Operator: ${test.operator}</div>
                <div class="test-card-info">📅 Test Date: ${testDate}</div>
                <div class="test-card-info">⬆️ Upload Date: ${uploadDate}</div>
                <div class="test-card-info">Result: <strong>${result}</strong></div>
            </div>
        `;
    }).join('');
}

async function viewTestDetail(testId, testType = 'mlc') {
    loadingSection.style.display = 'block';
    
    try {
        // Use the correct endpoint based on test type
        const endpoint = testType === 'mvic' 
            ? `${API_BASE_URL}/mvic-test-sessions/${testId}`
            : `${API_BASE_URL}/mlc-test-sessions/${testId}`;
        
        const response = await fetch(endpoint);
        const test = await response.json();
        
        // Add test type to the test object
        test.test_type = testType;
        
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
    document.getElementById('detailFilename').textContent = `Operator: ${test.operator}`;
    
    const testDate = test.test_date ? 
        new Date(test.test_date).toLocaleString() : 
        'Unknown';
    document.getElementById('detailDate').textContent = testDate;
    
    const uploadDate = new Date(test.upload_date).toLocaleString();
    document.getElementById('detailUploadDate').textContent = uploadDate;
    
    const summaryCard = document.querySelector('.summary-card');
    
    // Helper function to format numbers - 2 decimal places
    const fmt = (val) => val != null ? (typeof val === 'number' ? val.toFixed(2) : val) : 'N/A';
    
    // Display based on test type
    if (test.test_type === 'mvic') {
        // MVIC test display
        summaryCard.innerHTML = `
            <h3 style="font-size: 0.90em !important; margin-bottom: 1px;">Résultats MVIC</h3>
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
        `;
    } else {
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
        `;
    }
    
    // Hide visualizations and results table for both MLC and MVIC tests
    document.querySelector('.visualization-section').style.display = 'none';
    document.querySelector('.results-table-section').style.display = 'none';
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
    
    const testTypeName = selectedTest.test_type === 'mvic' ? 'MVIC' : 'MLC';
    
    if (!confirm(`Are you sure you want to delete ${testTypeName} Test #${selectedTest.id}?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        // Use correct endpoint based on test type
        const endpoint = selectedTest.test_type === 'mvic'
            ? `${API_BASE_URL}/mvic-test-sessions/${selectedTest.id}`
            : `${API_BASE_URL}/mlc-test-sessions/${selectedTest.id}`;
        
        const response = await fetch(endpoint, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete test');
        }
        
        alert(`✅ ${testTypeName} test deleted successfully`);
        
        // Close detail view and reload tests
        closeTestDetail();
        loadTests();
        loadDatabaseStats();
        
    } catch (error) {
        console.error('Error deleting test:', error);
        alert('Error deleting test');
    }
}

async function downloadTestReport() {
    // Prompt for date range
    const startDate = prompt('Enter start date (YYYY-MM-DD) or leave empty for all:');
    const endDate = prompt('Enter end date (YYYY-MM-DD) or leave empty for all:');
    
    try {
        // Show loading indicator
        downloadReportBtn.disabled = true;
        downloadReportBtn.textContent = '⏳ Generating PDF...';
        
        let url = `${API_BASE_URL}/mlc-reports/trend`;
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate report');
        }
        
        // Download the PDF
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `mlc_report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        
        alert('✅ PDF report downloaded successfully');
        
    } catch (error) {
        console.error('Error downloading report:', error);
        alert(`Error generating PDF report: ${error.message}`);
    } finally {
        downloadReportBtn.disabled = false;
        downloadReportBtn.textContent = '📄 Download PDF Report';
    }
}

async function generateTrendReport() {
    try {
        // Show loading indicator
        generateTrendReportBtn.disabled = true;
        generateTrendReportBtn.textContent = '⏳ Generating Trend Report...';
        
        // Get date filters if set
        const startDate = startDateInput.value || null;
        const endDate = endDateInput.value || null;
        
        // For now, generate report for MLC tests (you can make this dynamic later)
        let url = `${API_BASE_URL}/reports/trend/mlc_leaf_jaw`;
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate trend report');
        }
        
        // Download the PDF
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `trend_report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
        
        alert('✅ Trend report downloaded successfully');
        
    } catch (error) {
        console.error('Error generating trend report:', error);
        alert(`Error generating trend report: ${error.message}`);
    } finally {
        generateTrendReportBtn.disabled = false;
        generateTrendReportBtn.textContent = '📊 Generate Trend Report (All Tests)';
    }
}
