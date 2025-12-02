/**
 * JobApp - Cover Letter Generator
 * Client-side JavaScript with SSE streaming
 */

// DOM Elements
const form = document.getElementById('generate-form');
const submitBtn = document.getElementById('submit-btn');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const errorSection = document.getElementById('error-section');

// State
let currentMode = 'url'; // 'url' or 'manual'
let isSubmitting = false;
let promptLoaded = false;

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    setupFormSubmit();
    setupFileUpload();
    setupModeToggle();
    setupResetButtons();
    setupAdvancedSection();
}

// Form submission with SSE streaming
async function handleSubmit(e) {
    e.preventDefault();
    
    // Prevent double submission
    if (isSubmitting) return;
    
    // Validate form
    if (!validateForm()) return;
    
    // Disable submit button
    isSubmitting = true;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Generating...';
    
    // Show progress, hide form
    showProgress();
    resetProgressSteps();
    
    // Build form data
    const formData = new FormData(form);
    
    // Remove unused fields based on mode
    if (currentMode === 'url') {
        formData.delete('job_description');
        formData.delete('job_title');
        formData.delete('company_name');
    } else {
        formData.delete('job_url');
    }
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            showError('Server error. Please try again.');
            return;
        }
        
        // Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // Parse SSE events from buffer
            const events = buffer.split('\n\n');
            buffer = events.pop(); // Keep incomplete event in buffer
            
            for (const eventStr of events) {
                if (!eventStr.trim()) continue;
                
                const lines = eventStr.split('\n');
                let eventType = 'message';
                let eventData = '';
                
                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        eventType = line.slice(7);
                    } else if (line.startsWith('data: ')) {
                        eventData = line.slice(6);
                    }
                }
                
                if (eventData) {
                    handleSSEEvent(eventType, JSON.parse(eventData));
                }
            }
        }
    } catch (err) {
        console.error('Error:', err);
        showError('Network error. Please check your connection and try again.');
    } finally {
        // Re-enable submit button
        isSubmitting = false;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Generate Cover Letter';
    }
}

function handleSSEEvent(eventType, data) {
    switch (eventType) {
        case 'progress':
            markStepActive(data.step);
            break;
        case 'complete':
            markAllStepsComplete();
            setTimeout(() => showResult(data), 300);
            break;
        case 'error':
            showError(data.error);
            break;
    }
}

function markStepActive(step) {
    const allSteps = document.querySelectorAll('.step');
    let foundCurrent = false;
    
    allSteps.forEach(s => {
        const stepName = s.dataset.step;
        
        if (stepName === step) {
            foundCurrent = true;
            s.classList.add('active');
            s.classList.remove('complete');
        } else if (!foundCurrent) {
            // Previous steps are complete
            s.classList.remove('active');
            s.classList.add('complete');
        } else {
            // Future steps are pending
            s.classList.remove('active', 'complete');
        }
    });
}

function markAllStepsComplete() {
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
        step.classList.add('complete');
    });
}

function resetProgressSteps() {
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'complete');
    });
}

// Validation
function validateForm() {
    // Check resume is selected
    const resumeInput = document.getElementById('resume');
    if (!resumeInput.files.length) {
        alert('Please upload your resume PDF');
        return false;
    }
    
    // Check job info based on mode
    if (currentMode === 'url') {
        const jobUrl = document.getElementById('job_url').value.trim();
        if (!jobUrl) {
            alert('Please enter a job posting URL');
            return false;
        }
    } else {
        const jobTitle = document.getElementById('job_title').value.trim();
        const companyName = document.getElementById('company_name').value.trim();
        const jobDescription = document.getElementById('job_description').value.trim();
        
        if (!jobTitle || !companyName || !jobDescription) {
            alert('Please fill in job title, company name, and description');
            return false;
        }
    }
    
    return true;
}

// File upload with drag-and-drop
function setupFileUpload() {
    const dropzone = document.getElementById('resume-dropzone');
    const fileInput = document.getElementById('resume');
    const filenameDisplay = document.getElementById('resume-filename');
    
    // Drag events
    ['dragenter', 'dragover'].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });
    
    ['dragleave', 'drop'].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });
    
    // Drop handler
    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length && files[0].type === 'application/pdf') {
            fileInput.files = files;
            showFilename(files[0].name);
        }
    });
    
    // Click handler
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            showFilename(fileInput.files[0].name);
        }
    });
    
    function showFilename(name) {
        filenameDisplay.textContent = name;
        filenameDisplay.classList.add('visible');
    }
}

// Toggle between URL and Manual input modes
function setupModeToggle() {
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    const urlMode = document.getElementById('url-mode');
    const manualMode = document.getElementById('manual-mode');
    
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            currentMode = mode;
            
            // Update button states
            toggleBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show/hide input sections
            if (mode === 'url') {
                urlMode.classList.remove('hidden');
                manualMode.classList.add('hidden');
            } else {
                urlMode.classList.add('hidden');
                manualMode.classList.remove('hidden');
            }
        });
    });
}

// UI State functions
function showProgress() {
    form.classList.add('hidden');
    progressSection.classList.remove('hidden');
    resultSection.classList.add('hidden');
    errorSection.classList.add('hidden');
}

function showResult(data) {
    progressSection.classList.add('hidden');
    resultSection.classList.remove('hidden');
    
    document.getElementById('result-title').textContent = data.job_title;
    document.getElementById('result-company').textContent = data.company;
    document.getElementById('download-btn').href = data.download_url;
}

function showError(message) {
    progressSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
}

function resetForm() {
    form.reset();
    form.classList.remove('hidden');
    progressSection.classList.add('hidden');
    resultSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    
    // Reset file display
    const filenameDisplay = document.getElementById('resume-filename');
    filenameDisplay.textContent = '';
    filenameDisplay.classList.remove('visible');
    
    // Reset to URL mode
    currentMode = 'url';
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === 'url');
    });
    document.getElementById('url-mode').classList.remove('hidden');
    document.getElementById('manual-mode').classList.add('hidden');
    
    // Reset advanced settings accordion to closed state
    const advancedContent = document.getElementById('advanced-content');
    const advancedIcon = document.querySelector('#advanced-toggle .toggle-icon');
    advancedContent.classList.add('hidden');
    advancedIcon.classList.remove('open');
    promptLoaded = false; // Re-fetch prompt on next open
    
    resetProgressSteps();
}

function setupFormSubmit() {
    form.addEventListener('submit', handleSubmit);
}

function setupResetButtons() {
    document.getElementById('reset-btn').addEventListener('click', resetForm);
    document.getElementById('retry-btn').addEventListener('click', resetForm);
}

// Advanced Settings - Prompt Editor
function setupAdvancedSection() {
    const toggle = document.getElementById('advanced-toggle');
    const content = document.getElementById('advanced-content');
    const icon = toggle.querySelector('.toggle-icon');
    const promptTextarea = document.getElementById('prompt');
    const saveBtn = document.getElementById('save-prompt-btn');
    const status = document.getElementById('prompt-status');
    
    // Toggle accordion
    toggle.addEventListener('click', async () => {
        const isHidden = content.classList.contains('hidden');
        content.classList.toggle('hidden');
        icon.classList.toggle('open', isHidden);
        
        // Load prompt on first open
        if (isHidden && !promptLoaded) {
            promptTextarea.value = 'Loading...';
            try {
                const response = await fetch('/api/prompt');
                const data = await response.json();
                promptTextarea.value = data.prompt;
                promptLoaded = true;
            } catch (err) {
                promptTextarea.value = 'Failed to load prompt. Please try again.';
            }
        }
    });
    
    // Save prompt
    saveBtn.addEventListener('click', async () => {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        status.textContent = '';
        status.className = 'prompt-status';
        
        try {
            const response = await fetch('/api/prompt', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: promptTextarea.value })
            });
            
            if (response.ok) {
                status.textContent = 'Saved!';
                status.classList.add('success');
            } else {
                const data = await response.json();
                status.textContent = data.detail || 'Failed to save';
                status.classList.add('error');
            }
        } catch (err) {
            status.textContent = 'Network error';
            status.classList.add('error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Changes';
            
            // Clear status after 3 seconds
            setTimeout(() => {
                status.textContent = '';
                status.className = 'prompt-status';
            }, 3000);
        }
    });
}
