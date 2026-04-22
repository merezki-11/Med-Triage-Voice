let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const recordBtn = document.getElementById('recordBtn');
const recordText = document.getElementById('recordText');
const waves = document.getElementById('waves');
const audioUpload = document.getElementById('audioUpload');

const loading = document.getElementById('loading');
const results = document.getElementById('results');

// UI Elements for data
const transcriptText = document.getElementById('transcriptText');
const langTag = document.getElementById('lang-tag');
const patientName = document.getElementById('patientName');
const severityLevel = document.getElementById('severityLevel');
const symptomsList = document.getElementById('symptomsList');
const durationText = document.getElementById('durationText');
const recommendedTriage = document.getElementById('recommendedTriage');

recordBtn.addEventListener('click', async () => {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
});

audioUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        processAudio(file);
    }
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.addEventListener('dataavailable', event => {
            audioChunks.push(event.data);
        });

        mediaRecorder.addEventListener('stop', () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            // Convert to a File object
            const file = new File([audioBlob], "recording.webm", { type: 'audio/webm' });
            processAudio(file);
            
            // Stop tracks to release mic
            stream.getTracks().forEach(track => track.stop());
        });

        mediaRecorder.start();
        isRecording = true;
        
        recordBtn.classList.add('recording');
        recordText.innerText = 'Stop Recording';
        waves.classList.add('active');
        recordBtn.querySelector('.fa-microphone').classList.replace('fa-microphone', 'fa-stop');
        
    } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Could not access microphone. Ensure permissions are granted.");
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        recordBtn.classList.remove('recording');
        recordText.innerText = 'Start Recording';
        waves.classList.remove('active');
        recordBtn.querySelector('.fa-stop').classList.replace('fa-stop', 'fa-microphone');
    }
}

async function processAudio(file) {
    // Hide results and show loader
    results.classList.add('hidden');
    loading.classList.add('active');
    
    const formData = new FormData();
    formData.append('audio', file);

    try {
        const response = await fetch('/api/process-audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Server error occurred");
        }
        
        displayResults(data);
        
    } catch (error) {
        console.error("Error processing audio:", error);
        alert("Error: " + error.message);
    } finally {
        loading.classList.remove('active');
    }
}

function displayResults(data) {
    // Transcript
    transcriptText.innerText = data.transcript;
    langTag.innerText = data.language || "Unknown";
    
    // Clinical Data
    const cData = data.clinical_data;
    
    if (cData && cData.error) {
        patientName.innerText = "Error extracting data: " + cData.error;
        durationText.innerText = "N/A";
        recommendedTriage.innerText = "N/A";
        severityLevel.innerText = "Unknown";
        symptomsList.innerHTML = "";
        results.classList.remove('hidden');
        return;
    }
    
    patientName.innerText = cData.patient_name || "Unknown";
    durationText.innerText = cData.duration || "N/A";
    recommendedTriage.innerText = cData.recommended_triage || "Requires clinician review.";
    
    // Symptoms tags
    symptomsList.innerHTML = "";
    if (Array.isArray(cData.primary_symptoms)) {
        cData.primary_symptoms.forEach(sym => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.innerText = sym;
            symptomsList.appendChild(span);
        });
    }
    
    // Severity badge
    const sevString = (cData.severity_level || "").toLowerCase();
    
    let matchedClass = 'severity-medium'; // default
    if (sevString.includes('low')) matchedClass = 'severity-low';
    if (sevString.includes('high')) matchedClass = 'severity-high';
    if (sevString.includes('critical')) matchedClass = 'severity-critical';
    
    severityLevel.className = `value badge ${matchedClass}`;
    severityLevel.innerText = cData.severity_level || "Unknown";
    
    // Show results
    results.classList.remove('hidden');
}
