/**
 * Trends Analysis - Frontend JavaScript
 * Handles trend report generation and preview for quality control tests
 */

let currentTrendData = null;

// Initialize date inputs to last 30 days
function initializeDateInputs() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    // Format dates as YYYY-MM-DD for input fields
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    document.getElementById('endDateInput').value = formatDate(endDate);
    document.getElementById('startDateInput').value = formatDate(startDate);
    
    console.log('Initialized date range:', formatDate(startDate), 'to', formatDate(endDate));
}

// Reset form to initial state
function resetForm() {
    initializeDateInputs();
    document.getElementById('testTypeSelect').value = '';
    document.getElementById('previewSection').classList.remove('active');
    document.getElementById('generatePdfBtn').disabled = true;
    currentTrendData = null;
}

// Load preview data
async function loadPreview() {
    const testType = document.getElementById('testTypeSelect').value;
    const startDate = document.getElementById('startDateInput').value;
    const endDate = document.getElementById('endDateInput').value;
    
    // Validation
    if (!testType) {
        alert('Veuillez sélectionner un type de test');
        return;
    }
    
    if (!startDate || !endDate) {
        alert('Veuillez sélectionner une plage de dates');
        return;
    }
    
    if (new Date(startDate) > new Date(endDate)) {
        alert('La date de début doit être antérieure à la date de fin');
        return;
    }
    
    console.log('=== LOADING PREVIEW ===');
    console.log('Test Type:', testType);
    console.log('Start Date:', startDate);
    console.log('End Date:', endDate);
    
    // Show loading
    showLoading(true);
    
    try {
        // Fetch trend data from backend
        const endpoint = getEndpointForTestType(testType);
        const url = `${window.APP_CONFIG.API_BASE_URL}${endpoint}?start_date=${startDate}&end_date=${endDate}&format=json`;
        console.log('Fetching URL:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        currentTrendData = await response.json();
        console.log('Received data:', currentTrendData);
        console.log('Number of tests:', currentTrendData.tests.length);
        
        // Display preview
        displayPreview(currentTrendData);
        
        // Enable PDF generation button
        document.getElementById('generatePdfBtn').disabled = false;
        
    } catch (error) {
        console.error('Error loading trend data:', error);
        alert(`Erreur lors du chargement des données: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Get API endpoint for test type
function getEndpointForTestType(testType) {
    const endpoints = {
        'leaf_position': '/reports/leaf-position-trend',
        'piqt': '/reports/piqt-trend',
        'mvic_fente': '/reports/mvic-fente-trend',
        'mlc_leaf_jaw': '/reports/mlc-leaf-jaw-trend'
    };
    
    return endpoints[testType] || '/reports/leaf-position-trend';
}

// Display preview data
function displayPreview(data) {
    // Show preview section
    document.getElementById('previewSection').classList.add('active');
    
    // Display statistics
    displayStatistics(data);
    
    // Display test list
    displayTestList(data.tests);
}

// Display statistics cards
function displayStatistics(data) {
    const statsGrid = document.getElementById('statsGrid');
    statsGrid.innerHTML = '';
    
    // Calculate stats
    const totalTests = data.tests.length;
    const passedTests = data.tests.filter(t => t.overall_result === 'PASS').length;
    const failedTests = totalTests - passedTests;
    const passRate = totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(1) : 0;
    
    // Blade-specific stats (for leaf_position)
    let totalBlades = 0;
    let okBlades = 0;
    if (data.blade_trends) {
        totalBlades = Object.keys(data.blade_trends).length;
        // Count blades that have at least one OK measurement
        Object.values(data.blade_trends).forEach(bladeMeasurements => {
            const hasOk = bladeMeasurements.some(m => m.is_valid === 'OK');
            if (hasOk) okBlades++;
        });
    }
    
    // Create stat cards
    const stats = [
        {
            value: totalTests,
            label: 'Tests Analysés',
            color: '#007bff'
        },
        {
            value: passedTests,
            label: 'Tests Réussis',
            color: '#28a745'
        },
        {
            value: failedTests,
            label: 'Tests Échoués',
            color: '#dc3545'
        },
        {
            value: `${passRate}%`,
            label: 'Taux de Réussite',
            color: passRate >= 90 ? '#28a745' : passRate >= 70 ? '#ffc107' : '#dc3545'
        }
    ];
    
    // Add blade-specific stats if available
    if (totalBlades > 0) {
        stats.push({
            value: totalBlades,
            label: 'Lames Analysées',
            color: '#17a2b8'
        });
        stats.push({
            value: okBlades,
            label: 'Lames OK',
            color: '#28a745'
        });
    }
    
    // Render stats
    stats.forEach(stat => {
        const statCard = document.createElement('div');
        statCard.className = 'stat-card';
        statCard.style.borderLeftColor = stat.color;
        statCard.innerHTML = `
            <div class="stat-value" style="color: ${stat.color}">${stat.value}</div>
            <div class="stat-label">${stat.label}</div>
        `;
        statsGrid.appendChild(statCard);
    });
}

// Display test list table
function displayTestList(tests) {
    const tbody = document.getElementById('testListBody');
    tbody.innerHTML = '';
    
    if (!tests || tests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #6c757d;">Aucun test trouvé pour cette période</td></tr>';
        return;
    }
    
    // Sort tests by date (most recent first)
    tests.sort((a, b) => new Date(b.test_date) - new Date(a.test_date));
    
    const testType = document.getElementById('testTypeSelect').value;
    
    tests.forEach(test => {
        const row = tbody.insertRow();
        row.style.cursor = 'pointer';
        
        // Support both test_id and id field names
        const testId = test.test_id || test.id;
        
        // Add click handler to open test detail page
        row.addEventListener('click', () => {
            openTestDetail(testId, testType);
        });
        
        // ID
        const idCell = row.insertCell();
        idCell.textContent = `#${testId}`;
        idCell.style.fontWeight = 'bold';
        idCell.style.color = '#1976d2';
        
        // Date
        const dateCell = row.insertCell();
        dateCell.textContent = new Date(test.test_date).toLocaleDateString('fr-FR');
        
        // Operator
        const operatorCell = row.insertCell();
        operatorCell.textContent = test.operator || 'N/A';
        
        // Result
        const resultCell = row.insertCell();
        const badgeClass = test.overall_result === 'PASS' ? 'badge-pass' : 
                          test.overall_result === 'FAIL' ? 'badge-fail' : 'badge-warning';
        resultCell.innerHTML = `<span class="badge ${badgeClass}">${test.overall_result}</span>`;
        
        // Notes
        const notesCell = row.insertCell();
        notesCell.textContent = test.notes || '-';
        notesCell.style.maxWidth = '300px';
        notesCell.style.overflow = 'hidden';
        notesCell.style.textOverflow = 'ellipsis';
        notesCell.style.whiteSpace = 'nowrap';
        if (test.notes) {
            notesCell.title = test.notes;
        }
    });
}

// Open test detail page (same as in review page)
function openTestDetail(testId, testType) {
    // Map test types to their display pages
    const displayPages = {
        'leaf_position': '/static/result_displays/leaf_position_display.html',
        'mvic_fente_v2': '/static/result_displays/mvic_fente_v2_display.html',
        'mlc_leaf_jaw': '/static/result_displays/mlc_leaf_jaw_display.html',
        'safety_systems': '/static/result_displays/safety_systems_display.html',
        'niveau_helium': '/static/result_displays/niveau_helium_display.html',
        'piqt': '/static/result_displays/piqt_display.html',
        'position_table_v2': '/static/result_displays/position_table_display.html',
        'alignement_laser': '/static/result_displays/alignement_laser_display.html',
        'quasar': '/static/result_displays/quasar_display.html',
        'indice_quality': '/static/result_displays/indice_quality_display.html',
        'mvic': '/static/result_displays/mvic_display.html'
    };
    
    const displayPage = displayPages[testType];
    
    if (displayPage) {
        // Open in new tab or same window
        window.open(`${displayPage}?id=${testId}`, '_blank');
    } else {
        console.warn(`No display page found for test type: ${testType}`);
        alert('Page de visualisation non disponible pour ce type de test');
    }
}

// Generate PDF report
async function generatePDF() {
    const testType = document.getElementById('testTypeSelect').value;
    const startDate = document.getElementById('startDateInput').value;
    const endDate = document.getElementById('endDateInput').value;
    
    if (!currentTrendData) {
        alert('Veuillez d\'abord charger l\'aperçu des données');
        return;
    }
    
    if (!currentTrendData.tests || currentTrendData.tests.length === 0) {
        alert('Aucune donnée disponible pour générer le rapport');
        return;
    }
    
    // Show loading
    showLoading(true, 'Génération du PDF en cours...');
    
    try {
        let url, filename;
        
        // Route based on test type
        if (testType === 'leaf_position') {
            // Use the leaf-position-trend endpoint with format=pdf
            url = `${window.APP_CONFIG.API_BASE_URL}/reports/leaf-position-trend?start_date=${startDate}&end_date=${endDate}&format=pdf`;
            filename = `leaf_position_trend_${startDate}_${endDate}.pdf`;
            console.log('Generating LeafPosition trend PDF from:', url);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            // Download PDF
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            
        } else if (testType === 'piqt') {
            // Use the piqt-trend endpoint with format=pdf
            url = `${window.APP_CONFIG.API_BASE_URL}/reports/piqt-trend?start_date=${startDate}&end_date=${endDate}&format=pdf`;
            filename = `piqt_trend_${startDate}_${endDate}.pdf`;
            console.log('Generating PIQT trend PDF from:', url);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            // Download PDF
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            
        } else {
            // Default: MLC blade compliance report
            const testIds = currentTrendData.tests.map(test => test.test_id);
            console.log('Generating PDF for test IDs:', testIds);
            
            // Get blade size filter from UI
            const bladeSizeSelect = document.getElementById('bladeSizeSelect');
            const bladeSize = bladeSizeSelect ? bladeSizeSelect.value : 'all';
            console.log('Blade size filter:', bladeSize);
            
            // Build URL with test_ids as query parameters
            const params = new URLSearchParams();
            testIds.forEach(id => params.append('test_ids', id));
            params.append('blade_size', bladeSize);
            
            url = `${window.APP_CONFIG.API_BASE_URL}/reports/mlc-blade-compliance?${params.toString()}`;
            console.log('Fetching PDF from:', url);
            
            const response = await fetch(url, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            // Download PDF
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `rapport_mlc_${startDate}_${endDate}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
        }
        
        alert('Rapport PDF généré avec succès !');
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert(`Erreur lors de la génération du PDF: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Show/hide loading overlay
function showLoading(show, message = 'Chargement des données...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingContent = overlay.querySelector('.loading-content p');
    
    if (show) {
        loadingContent.textContent = message;
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Trends page initialized');
    initializeDateInputs();
});
