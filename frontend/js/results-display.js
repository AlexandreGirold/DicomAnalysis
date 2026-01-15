/**
 * Test Results Display
 */

function displayTestResults(result) {
    const testResultsSection = document.getElementById('testResultsSection');
    
    testResultsSection.style.display = 'block';
    testResultsSection.scrollIntoView({ behavior: 'smooth' });
    
    document.getElementById('resultTestName').textContent = result.test_name;
    
    const statusElement = document.getElementById('resultOverallStatus');
    statusElement.textContent = result.overall_result;
    statusElement.className = `overall-status ${result.overall_result.toLowerCase()}`;
    
    const resultsHtml = Object.entries(result.results).map(([name, res]) => `
        <div class="result-row ${res.status.toLowerCase()}">
            <span class="result-name">${name.replace(/_/g, ' ')}</span>
            <span class="result-value">${res.value} ${res.unit || ''}</span>
            ${res.tolerance ? `<span class="result-tolerance">${res.tolerance}</span>` : ''}
            <span class="result-status ${res.status.toLowerCase()}">${res.status}</span>
        </div>
    `).join('');
    document.getElementById('testResults').innerHTML = resultsHtml;
    
    if (result.visualizations && result.visualizations.length > 0) {
        displayVisualizations(result.visualizations);
    } else {
        document.getElementById('testVisualizations').style.display = 'none';
    }
    
    // Reset and show the save button for new test
    const saveBtn = document.getElementById('saveTestBtn');
    if (saveBtn) {
        // Reset button state
        saveBtn.style.display = 'inline-block';
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save to Database';
        saveBtn.className = 'btn btn-success';
        console.log('Save button reset and shown for new test');
    }
    
    // Store the result for saving later
    window.CURRENT_TEST_RESULT = result;
}

function displayVisualizations(visualizations) {
    const visualizationsSection = document.getElementById('testVisualizations');
    
    if (!visualizations || visualizations.length === 0) {
        visualizationsSection.style.display = 'none';
        return;
    }
    
    visualizationsSection.style.display = 'block';
    window.APP_STATE.allVisualizations = visualizations;
    window.APP_STATE.currentVisualizationIndex = 0;
    
    displayCurrentVisualization();
}

function displayCurrentVisualization() {
    const visualizationsList = document.getElementById('visualizationsList');
    const viz = window.APP_STATE.allVisualizations[window.APP_STATE.currentVisualizationIndex];
    
    const navControls = window.APP_STATE.allVisualizations.length > 1 ? `
        <div class="visualization-nav">
            <button class="nav-btn" onclick="previousVisualization()" ${window.APP_STATE.currentVisualizationIndex === 0 ? 'disabled' : ''}>
                ← Previous
            </button>
            <span class="nav-counter">${window.APP_STATE.currentVisualizationIndex + 1} / ${window.APP_STATE.allVisualizations.length}</span>
            <button class="nav-btn" onclick="nextVisualization()" ${window.APP_STATE.currentVisualizationIndex === window.APP_STATE.allVisualizations.length - 1 ? 'disabled' : ''}>
                Next →
            </button>
        </div>
    ` : '';
    
    const statsHtml = viz.statistics ? `
        <div class="file-status-bar">
            <span class="file-status-label">Test Result:</span>
            <span class="file-status-badge ${viz.statistics.status.toLowerCase()}">${viz.statistics.status}</span>
            <div class="blade-stats">
                <span class="blade-stat">Total: <strong>${viz.statistics.total_blades}</strong></span>
                <span class="blade-stat success">OK: <strong>${viz.statistics.ok_blades}</strong></span>
                <span class="blade-stat danger">Failed: <strong>${viz.statistics.out_of_tolerance}</strong></span>
                <span class="blade-stat info">Closed: <strong>${viz.statistics.closed_blades}</strong></span>
            </div>
        </div>
    ` : '';
    
    visualizationsList.innerHTML = `
        ${navControls}
        <div class="visualization-item">
            <h5>${viz.name}</h5>
            ${statsHtml}
            ${viz.type === 'image' ? 
                `<img src="${viz.data}" alt="${viz.name}" class="visualization-image" onclick="openImageModal('${viz.data}', '${viz.name}')">` :
                `<div class="visualization-data">${viz.data}</div>`
            }
        </div>
    `;
}

function nextVisualization() {
    if (window.APP_STATE.currentVisualizationIndex < window.APP_STATE.allVisualizations.length - 1) {
        window.APP_STATE.currentVisualizationIndex++;
        displayCurrentVisualization();
    }
}

function previousVisualization() {
    if (window.APP_STATE.currentVisualizationIndex > 0) {
        window.APP_STATE.currentVisualizationIndex--;
        displayCurrentVisualization();
    }
}

function nextVisualization() {
    if (window.APP_STATE.currentVisualizationIndex < window.APP_STATE.allVisualizations.length - 1) {
        window.APP_STATE.currentVisualizationIndex++;
        displayCurrentVisualization();
    }
}

function openImageModal(imageSrc, title) {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="image-modal-content">
            <div class="image-modal-header">
                <h3>${title}</h3>
                <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
            </div>
            <img src="${imageSrc}" alt="${title}" class="full-size-image">
        </div>
    `;
    
    modal.onclick = function(event) {
        if (event.target === modal) {
            modal.remove();
        }
    };
    
    document.body.appendChild(modal);
}
