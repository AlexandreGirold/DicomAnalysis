// API Configuration
const API_BASE_URL = window.location.origin;  // Use same origin as the page

// State
let selectedFiles = [];
let currentResults = null;
let currentTestId = null;

// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const saveBtn = document.getElementById('saveBtn');
const vizSelect = document.getElementById('vizSelect');
const visualizationDisplay = document.getElementById('visualizationDisplay');
const resultsTableBody = document.getElementById('resultsTableBody');
const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // Drag and drop
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    
    // File input
    fileInput.addEventListener('change', handleFileSelect);
    
    // Analyze button
    analyzeBtn.addEventListener('click', runAnalysis);
    
    // Save button
    saveBtn.addEventListener('click', saveToDatabase);
    
    // Visualization select
    vizSelect.addEventListener('change', displaySelectedVisualization);
    
    // Table filters
    searchInput.addEventListener('input', filterTable);
    statusFilter.addEventListener('change', filterTable);
}

function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function addFiles(files) {
    // Filter for DICOM files
    const dicomFiles = files.filter(f => f.name.toLowerCase().endsWith('.dcm'));
    
    if (dicomFiles.length === 0) {
        alert('Please select DICOM (.dcm) files only');
        return;
    }
    
    selectedFiles = [...selectedFiles, ...dicomFiles];
    updateFileList();
    analyzeBtn.disabled = selectedFiles.length === 0;
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    analyzeBtn.disabled = selectedFiles.length === 0;
}

function updateFileList() {
    if (selectedFiles.length === 0) {
        fileList.innerHTML = '<p class="placeholder-text">No files selected</p>';
        return;
    }
    
    fileList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <div>
                <div class="file-name">📄 ${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="remove-file" onclick="removeFile(${index})">✖</button>
        </div>
    `).join('');
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function runAnalysis() {
    if (selectedFiles.length === 0) {
        alert('Please select at least one DICOM file');
        return;
    }
    
    // Show loading
    loadingSection.style.display = 'block';
    resultsSection.style.display = 'none';
    analyzeBtn.disabled = true;
    
    try {
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const response = await fetch(`${API_BASE_URL}/analyze-batch`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        const data = await response.json();
        currentResults = data;
        currentTestId = data.test_id;
        
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        loadingSection.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}

function displayResults(data) {
    // Show results section
    resultsSection.style.display = 'block';
    
    // Update summary
    document.getElementById('totalBlades').textContent = data.summary.total_blades;
    document.getElementById('okBlades').textContent = data.summary.ok_blades;
    document.getElementById('outOfTolerance').textContent = data.summary.out_of_tolerance;
    document.getElementById('closedBlades').textContent = data.summary.closed_blades;
    
    // Populate visualization dropdown
    vizSelect.innerHTML = '<option value="">-- Select a visualization --</option>';
    if (data.visualizations && data.visualizations.length > 0) {
        data.visualizations.forEach((viz, index) => {
            const option = document.createElement('option');
            option.value = viz;
            option.textContent = `Visualization ${index + 1}`;
            vizSelect.appendChild(option);
        });
    }
    
    // Populate results table
    populateTable(data.results);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function populateTable(results) {
    resultsTableBody.innerHTML = results.map(r => {
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

function displaySelectedVisualization() {
    const selectedViz = vizSelect.value;
    
    if (!selectedViz) {
        visualizationDisplay.innerHTML = '<p class="placeholder-text">Select a visualization from the dropdown above</p>';
        return;
    }
    
    visualizationDisplay.innerHTML = `
        <img src="${API_BASE_URL}/visualization/${selectedViz}" alt="Blade Detection Visualization">
    `;
}

function filterTable() {
    const searchTerm = searchInput.value.toLowerCase();
    const statusValue = statusFilter.value.toLowerCase();
    
    const rows = resultsTableBody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const bladePair = row.cells[0].textContent.toLowerCase();
        const status = row.cells[4].textContent.trim().toLowerCase();
        
        const matchesSearch = bladePair.includes(searchTerm);
        const matchesStatus = !statusValue || status.includes(statusValue.replace('_', ' '));
        
        row.style.display = matchesSearch && matchesStatus ? '' : 'none';
    });
}

async function saveToDatabase() {
    if (!currentTestId) {
        alert('No test to save. The results were already saved automatically.');
        return;
    }
    
    alert('✅ Test results are already saved in the database!\n\nTest ID: ' + currentTestId + '\n\nYou can view them in the Review page.');
}
