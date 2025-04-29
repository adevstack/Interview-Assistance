/**
 * Enhanced voice input functionality for interview answers
 * - Captures all speech including controversial content
 * - Improved handling for when other audio is playing
 * - Restart capability when recognition ends unexpectedly
 */
function initVoiceInput(toggleButton, targetTextarea, statusElement) {
    let recognition;
    let isRecording = false;
    let restartCount = 0;
    const MAX_RESTARTS = 5;
    
    // Initialize SpeechRecognition
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
    } else if ('SpeechRecognition' in window) {
        recognition = new SpeechRecognition();
    } else {
        console.error('Speech recognition not supported');
        return;
    }
    
    // Configure recognition with maximum permissiveness
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    // Try to make recognition more sensitive
    if (typeof recognition.audioThreshold === 'number') {
        recognition.audioThreshold = 0; // Set to lowest possible value
    }
    
    // Handle speech recognition results
    recognition.onresult = function(event) {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            // Get the transcript and confidence
            const transcript = event.results[i][0].transcript;
            const confidence = event.results[i][0].confidence;
            
            console.log(`Speech recognized with confidence: ${confidence}`);
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update textarea content - now accepts all recognized speech
        if (finalTranscript) {
            // Reset restart count on successful recognition
            restartCount = 0;
            
            // If there's already text, add a space before new content
            if (targetTextarea.value && !targetTextarea.value.endsWith(' ')) {
                targetTextarea.value += ' ';
            }
            targetTextarea.value += finalTranscript;
            
            // Simulate user input to trigger any input events
            const inputEvent = new Event('input', { bubbles: true });
            targetTextarea.dispatchEvent(inputEvent);
        }
        
        // Show interim transcript in status element
        if (interimTranscript) {
            statusElement.textContent = 'Listening: ' + interimTranscript;
        }
    };
    
    // Handle errors with better logging and auto-restart
    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        console.log('Error details:', event);
        
        if (event.error === 'no-speech' || event.error === 'audio-capture') {
            // These errors can be temporary - try restarting
            if (isRecording && restartCount < MAX_RESTARTS) {
                console.log('Attempting to restart recognition after error');
                restartRecognition();
            } else {
                stopRecording();
                statusElement.textContent = 'Voice input error: ' + event.error;
            }
        } else {
            stopRecording();
            statusElement.textContent = 'Voice input error: ' + event.error;
        }
    };
    
    // Handle end of speech recognition with auto-restart
    recognition.onend = function() {
        console.log('Speech recognition ended');
        
        // If we're supposed to be recording, restart the recognition
        if (isRecording) {
            if (restartCount < MAX_RESTARTS) {
                console.log('Automatically restarting speech recognition');
                restartRecognition();
            } else {
                console.log('Max restarts reached, stopping recording');
                stopRecording();
                statusElement.textContent = 'Voice input stopped (max restarts reached)';
            }
        }
    };
    
    // Restart recognition after a brief pause
    function restartRecognition() {
        restartCount++;
        console.log(`Restarting recognition (attempt ${restartCount})`);
        
        setTimeout(() => {
            if (isRecording) {
                try {
                    // First make sure recognition is stopped before restarting
                    try {
                        recognition.stop();
                    } catch (stopError) {
                        console.log('Ignore stop error during restart:', stopError);
                    }
                    
                    // Wait a moment before restarting
                    setTimeout(() => {
                        if (isRecording) {
                            recognition.start();
                            statusElement.textContent = 'Listening...';
                        }
                    }, 100);
                } catch (e) {
                    console.error('Error restarting recognition:', e);
                    stopRecording();
                }
            }
        }, 300);
    }
    
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
        restartCount = 0;
        
        try {
            recognition.start();
            console.log('Speech recognition started');
            
            toggleButton.innerHTML = '<i class="fas fa-microphone-slash"></i> Stop Voice';
            toggleButton.classList.remove('btn-outline-primary');
            toggleButton.classList.add('btn-danger');
            statusElement.classList.remove('d-none');
            statusElement.textContent = 'Listening...';
        } catch (e) {
            console.error('Error starting speech recognition:', e);
            isRecording = false;
            statusElement.textContent = 'Failed to start voice input';
        }
    }
    
    // Stop recording
    function stopRecording() {
        isRecording = false;
        
        try {
            recognition.stop();
            console.log('Speech recognition stopped');
        } catch (e) {
            console.error('Error stopping speech recognition:', e);
        }
        
        toggleButton.innerHTML = '<i class="fas fa-microphone"></i> Voice Input';
        toggleButton.classList.remove('btn-danger');
        toggleButton.classList.add('btn-outline-primary');
        statusElement.textContent = '';
    }
}
