let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordButton = document.querySelector('.recorder');
let filledContent = document.querySelector('.filled-content');
let addJournalButton = document.querySelector('.add-journal-entry');
let formContainer = document.querySelector('.journal-entry-form');
let moods = document.querySelectorAll(".mood");
let moodInput = document.getElementById("selectedMood");
let recordButtonButton = document.querySelector('.record-button');

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
        recordButtonButton.classList.toggle('play');
        isRecording = true;
    } else {
        // Stop recording audio
        mediaRecorder.stop();
        recordButtonButton.classList.toggle('stop');
        isRecording = false;
    }
}

// send data to backend asynchronously
async function sendDataToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    document.getElementById('spinner').style.display = 'block';
    recordButtonButton.style.display = 'none';

    // submit data to flask backend via POST
    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();

    document.getElementById('spinner').style.display = 'none';

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
    formContainer.style.display = "flex";
    console.log("add-button clicked");
  });
  
// close form
let exitButton = document.querySelector('.exit');
exitButton.addEventListener('click', () => {
  formContainer.style.display = 'none';
});


// selects mood
moods.forEach(mood => {
    mood.addEventListener("click", function() {
        const selectedMood = this.getAttribute('data-mood');
        moodInput.value = selectedMood;
        console.log(moodInput.value);

        // Visually shows which mood has been selected
        moods.forEach(mood => mood.classList.remove('selected'));
        this.classList.add('selected');
    });
});


// adds event listeners for all delete buttons
function addDeleteEventListeners() {
    let deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach((deleteButton) => {
        deleteButton.addEventListener('click', async () => {
            console.log(deleteButton);
            console.log('clicked');
            let idStr = deleteButton.classList[1];
            
            // Send an HTTP DELETE request to Flask
            try {
                let routeID = parseInt(idStr.slice(5));  // slice off the "entry-" prefix
                let response = await fetch(`/delete_entry/${routeID}`, {
                    method: 'DELETE'
                });

                // Check if the response is OK
                if (response.ok) {
                    let deletedEntry = document.querySelector(`#${idStr}`);
                    deletedEntry.remove();
                } else {
                    console.error('Failed to delete entry');
                }
            } catch (error) {
                console.error('Error occurred:', error);
            }
        });
    });
}

addDeleteEventListeners();