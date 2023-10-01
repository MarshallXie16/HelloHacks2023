let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordButton = document.querySelector('.recorder');
let filledContent = document.querySelector('.filled-content');
let addJournalButton = document.querySelector('.add-journal-entry');
let formContainer = document.querySelector('.journal-entry-form');

// toggles the recording button
async function toggleRecording() {
    if (!isRecording) {

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            sendDataToServer(audioBlob);
        };
        // start recording audio
        mediaRecorder.start();
        document.querySelector('[onclick="toggleRecording()"]').textContent = 'Recording...';
        isRecording = true;
    } else {
        // Stop recording audio
        mediaRecorder.stop();
        document.querySelector('[onclick="toggleRecording()"]').textContent = 'Record';
        isRecording = false;
    }
}

// send data to backend asynchronously
async function sendDataToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    // submit data to flask backend via POST
    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();

    // reset recorded audio chunks
    audioChunks = [];

    // Hide record button, show form
    recordButton.style.display = 'none';
    filledContent.classList.add('active');
    
    // Update the DOM with the received summary and feedback
    if (data.summary) {
        $('#summary').text(data.summary);
    }
    if (data.feedback) {
        $('#feedback').text(data.feedback);
    }
}

// When add-journal-entry is clicked, show journal entry form
addJournalButton.addEventListener('click', () => {
    formContainer.style.display = "block";
    console.log("add-button clicked");
  });
  
// close form
let exitButton = document.querySelector('.exit');
exitButton.addEventListener('click', () => {
  formContainer.style.display = 'none';
});