/**
 * Form Building and Field Management
 */

function buildFormFields(fields) {
    const formFields = document.getElementById('formFields');
    const currentFormData = window.APP_STATE.currentFormData;
    
    formFields.innerHTML = fields.map(field => {
        switch (field.type) {
            case 'date':
                return buildDateField(field);
            case 'text':
                return buildTextField(field);
            case 'textarea':
                return buildTextAreaField(field);
            case 'number':
                return buildNumberField(field);
            case 'select':
                return buildSelectField(field);
            case 'file':
                return buildFileField(field);
            case 'section':
                return buildSectionField(field);
            case 'table':
                return buildTableField(field);
            case 'info':
                return buildInfoField(field);
            case 'hidden':
                return ''; // Hidden fields are managed by table inputs
            default:
                return '';
        }
    }).join('');
    
    // Add tolerance info if available
    if (currentFormData.tolerance) {
        formFields.innerHTML += `
            <div class="tolerance-info">
                <strong>Tolérance:</strong> ${currentFormData.tolerance}
            </div>
        `;
    }
}

function buildDateField(field) {
    return `
        <div class="form-group">
            <label for="${field.name}">${field.label}</label>
            <input type="date" id="${field.name}" name="${field.name}" 
                   ${field.required ? 'required' : ''} 
                   value="${field.default || ''}" 
                   class="form-input">
        </div>
    `;
}

function buildTextField(field) {
    return `
        <div class="form-group">
            <label for="${field.name}">${field.label}</label>
            <input type="text" id="${field.name}" name="${field.name}" 
                   ${field.required ? 'required' : ''} 
                   placeholder="${field.placeholder || ''}" 
                   class="form-input">
        </div>
    `;
}

function buildTextAreaField(field) {
    return `
        <div class="form-group">
            <label for="${field.name}">${field.label}</label>
            <textarea id="${field.name}" name="${field.name}" 
                      ${field.required ? 'required' : ''} 
                      placeholder="${field.placeholder || ''}" 
                      class="form-input"
                      rows="${field.rows || 4}"></textarea>
            ${field.details ? `<div class="field-details">${field.details}</div>` : ''}
        </div>
    `;
}

function buildNumberField(field) {
    return `
        <div class="form-group">
            <label for="${field.name}">${field.label}</label>
            <div class="input-with-unit">
                <input type="number" id="${field.name}" name="${field.name}" 
                       ${field.required ? 'required' : ''} 
                       ${field.min !== undefined ? `min="${field.min}"` : ''}
                       ${field.max !== undefined ? `max="${field.max}"` : ''}
                       ${field.step !== undefined ? `step="${field.step}"` : ''}
                       class="form-input">
                ${field.unit ? `<span class="unit">${field.unit}</span>` : ''}
            </div>
            ${field.details ? `<div class="field-details">${field.details}</div>` : ''}
        </div>
    `;
}

function buildSelectField(field) {
    return `
        <div class="form-group">
            <label for="${field.name}">${field.label}</label>
            <select id="${field.name}" name="${field.name}" 
                    ${field.required ? 'required' : ''} 
                    class="form-input form-select">
                <option value="">-- Sélectionner --</option>
                ${field.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
            </select>
            ${field.details ? `<div class="field-details">${field.details}</div>` : ''}
            ${field.tolerance ? `<div class="field-tolerance">Tolérance: ${field.tolerance}</div>` : ''}
        </div>
    `;
}

function buildFileField(field) {
    return `
        <div class="form-group">
            <label for="${field.name}">${field.label}</label>
            <input type="file" id="${field.name}" name="${field.name}" 
                   ${field.required ? 'required' : ''} 
                   ${field.accept ? `accept="${field.accept}"` : ''}
                   ${field.multiple ? 'multiple' : ''}
                   class="form-input file-input">
            ${field.description ? `<div class="field-description">${field.description}</div>` : ''}
        </div>
    `;
}

function buildSectionField(field) {
    return `
        <div class="form-section">
            <h3 class="section-title">${field.label}</h3>
            ${field.description ? `<p class="section-description">${field.description}</p>` : ''}
        </div>
    `;
}

function buildInfoField(field) {
    return `
        <div class="form-info">
            <p>${field.label}</p>
        </div>
    `;
}

function buildTableField(field) {
    if (!field.columns || !field.rows) {
        return '';
    }
    
    let tableHtml = `
        <div class="form-group table-group">
            <label>${field.label}</label>
            ${field.description ? `<div class="field-description">${field.description}</div>` : ''}
            <div class="table-wrapper">
                <table class="measurement-table">
                    <thead>
                        <tr>
    `;
    
    // Build header
    field.columns.forEach(col => {
        tableHtml += `<th>${col.label}</th>`;
    });
    tableHtml += `</tr></thead><tbody>`;
    
    // Build rows
    field.rows.forEach(row => {
        tableHtml += `<tr>`;
        
        // First column is the row label
        tableHtml += `<td class="row-label">${row.measure}</td>`;
        
        // Then the input fields
        row.fields.forEach((fieldName, idx) => {
            const col = field.columns[idx + 1]; // +1 because first column is label
            tableHtml += `
                <td>
                    <input type="number" 
                           id="${fieldName}" 
                           name="${fieldName}" 
                           ${field.required ? 'required' : ''} 
                           step="${col.step || '0.001'}" 
                           value="${field.required ? '' : '0'}"
                           class="table-input"
                           placeholder="0.000">
                </td>
            `;
        });
        
        tableHtml += `</tr>`;
    });
    
    tableHtml += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return tableHtml;
}
