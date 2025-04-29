/**
 * Voice input functionality for interview answers
 */
function initVoiceInput(toggleButton, targetTextarea, statusElement) {
    let recognition;
    let isRecording = false;
    
    // Initialize SpeechRecognition
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
    } else if ('SpeechRecognition' in window) {
        recognition = new SpeechRecognition();
    } else {
        console.error('Speech recognition not supported');
        return;
    }
    
    // Configure recognition
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    // Handle results
    recognition.onresult = function(event) {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update textarea content
        if (finalTranscript) {
            // If there's already text, add a space before new content
            if (targetTextarea.value && !targetTextarea.value.endsWith(' ')) {
                targetTextarea.value += ' ';
            }
            targetTextarea.value += finalTranscript;
        }
        
        // Show interim results (optional)
        // Could display somewhere temporarily
    };
    
    // Handle errors
    recognition.onerror = function(event) {
        console.error('Speech recognition error', event.error);
        stopRecording();
    };
    
    // Handle end of speech recognition
    recognition.onend = function() {
        // Only stop the UI if we're not starting again
        if (isRecording) {
            stopRecording();
        }
    };
    
    // Toggle recording
    toggleButton.addEventListener('click', function() {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });
    
    // Start recording
    function startRecording() {
        isRecording = true;
        recognition.start();
        toggleButton.innerHTML = '<i class="fas fa-microphone-slash"></i> Stop Voice';
        toggleButton.classList.remove('btn-outline-primary');
        toggleButton.classList.add('btn-danger');
        statusElement.classList.remove('d-none');
    }
    
    // Stop recording
    function stopRecording() {
        isRecording = false;
        recognition.stop();
        toggleButton.innerHTML = '<i class="fas fa-microphone"></i> Voice Input';
        toggleButton.classList.remove('btn-danger');
        toggleButton.classList.add('btn-outline-primary');
        statusElement.classList.add('d-none');
    }
}
