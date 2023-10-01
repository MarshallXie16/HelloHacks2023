document.getElementById("microphoneIcon").addEventListener("click", startRecording);

let recordingStatus = document.getElementById("recordingStatus");
let audioChunks = [];
let mediaRecorder;

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordingStatus.textContent = "Recording...";
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      const audioUrl = URL.createObjectURL(audioBlob);
      document.getElementById("audioElement").src = audioUrl;
      recordingStatus.textContent = "Recording complete";
    };

    mediaRecorder.start();
  } catch (error) {
    console.error("Error accessing microphone:", error);
    recordingStatus.textContent = "Error accessing microphone. Check console for details.";
  }
}

// Stop recording when the page is closed or navigated away
window.addEventListener("beforeunload", () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
});
