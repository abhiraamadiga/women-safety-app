// Sub-options data
const subOptions = {
    who: {
        family: ['Parents', 'Siblings', 'Extended family members', 'In-laws'],
        strangers: ['Unknown person', 'Group of strangers'],
        friends: ['Close friend', 'Acquaintance', "Friend's family member"],
        partner: ['Current partner/spouse', 'Ex-partner/spouse', 'Dating partner'],
        colleagues: ['Supervisor/Boss', 'Co-worker', 'Client/Customer'],
        others: ['Other (please specify in additional details)']
    },
    incident: {
        verbal_abuse: ['Threats', 'Insults/Name-calling', 'Yelling/Screaming'],
        physical_threat: ['Threatening gestures', 'Intimidation', 'Blocking path'],
        harassment: ['Sexual harassment', 'Unwanted touching', 'Following/Trailing'],
        stalking: ['Physical stalking', 'Cyber stalking', 'Persistent unwanted contact'],
        online_bullying: ['Threatening messages', 'Sharing private information', 'Fake profiles/Impersonation'],
        others: ['Other (please specify in additional details)']
    },
    location: {
        home: ['Own home', 'Family home', "Partner's home"],
        school: ['Classroom', 'Campus grounds', 'Hostel/Dormitory'],
        workplace: ['Office', 'Meeting room', 'Work event'],
        public_place: ['Street/Road', 'Public transport', 'Park', 'Mall/Market'],
        online: ['Social media', 'Messaging apps', 'Email', 'Gaming platform'],
        others: ['Other (please specify in additional details)']
    }
};

function showSubOptions(category) {
    const selectElement = document.getElementById(category === 'who' ? 'whoInvolved' : 
                                                 category === 'incident' ? 'incidentType' : 
                                                 'location');
    const selectedValue = selectElement.value;
    const subOptionsDiv = document.getElementById(`${category}_sub_options`);
    const subSelect = document.getElementById(category === 'who' ? 'whoSubOption' : 
                                             category === 'incident' ? 'incidentSubType' : 
                                             'locationDetail');
    
    if (selectedValue && selectedValue !== 'prefer_not_say' && subOptions[category][selectedValue]) {
        // Clear existing options
        subSelect.innerHTML = '<option value="">Select...</option>';
        
        // Add new options
        subOptions[category][selectedValue].forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.toLowerCase().replace(/\s+/g, '_');
            optionElement.textContent = option;
            subSelect.appendChild(optionElement);
        });
        
        subOptionsDiv.style.display = 'block';
    } else {
        subOptionsDiv.style.display = 'none';
    }
}

function toggleImpactDetails(type) {
    const detailsDiv = document.getElementById(`${type}_details`);
    const checkbox = document.getElementById(type === 'emotional' ? 'impact1' : 'impact2');
    
    if (checkbox.checked) {
        detailsDiv.style.display = 'block';
    } else {
        detailsDiv.style.display = 'none';
    }
}

function showFrequency() {
    document.getElementById('frequency_section').style.display = 'block';
}

function hideFrequency() {
    document.getElementById('frequency_section').style.display = 'none';
}

function showUpload() {
    document.getElementById('upload_section').style.display = 'block';
}

function hideUpload() {
    document.getElementById('upload_section').style.display = 'none';
}

// File preview functionality
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('evidenceFiles');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const preview = document.getElementById('file_preview');
            preview.innerHTML = '';
            
            if (this.files.length > 0) {
                const fileList = document.createElement('ul');
                fileList.className = 'list-group mt-2';
                
                Array.from(this.files).forEach(file => {
                    const listItem = document.createElement('li');
                    listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    listItem.innerHTML = `
                        <span><i class="bi bi-file-earmark"></i> ${file.name}</span>
                        <span class="badge bg-secondary">${(file.size / 1024).toFixed(2)} KB</span>
                    `;
                    fileList.appendChild(listItem);
                });
                
                preview.appendChild(fileList);
            }
        });
    }
    
    // Set max date to today for date input
    const dateInput = document.querySelector('input[name="incident_date"]');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('max', today);
    }
});

// Form validation
document.getElementById('incidentForm').addEventListener('submit', function(e) {
    const requiredFields = this.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    if (!isValid) {
        e.preventDefault();
        alert('Please fill in all required fields.');
    }
});
