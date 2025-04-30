/**
 * Enhanced voice input functionality for interview answers
 * - Captures all speech including controversial content
 * - Improved handling for when other audio is playing
 * - Restart capability when recognition ends unexpectedly
 * - Auto-submit after silence for 7 seconds
 * - Displays interim transcription in the text area
 */
function initVoiceInput(toggleButton, targetTextarea, statusElement) {
    let recognition;
    let isRecording = false;
    let restartCount = 0;
    const MAX_RESTARTS = 5;
    let lastSpeechTime = Date.now();
    let quietTimeoutId = null;
    
    // First try to use our advanced hybrid speech recognition with Gemini support
    try {
        console.log('Attempting to create hybrid speech recognition with Gemini support');
        recognition = createHybridSpeechRecognition(statusElement);
        
        if (recognition) {
            console.log('Successfully created hybrid speech recognition with Gemini support');
        } else {
            throw new Error('Failed to create hybrid speech recognition');
        }
    } catch (e) {
        console.error('Error creating hybrid speech recognition, falling back to browser only:', e);
        
        // Fall back to browser's built-in recognition
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
        } else if ('SpeechRecognition' in window) {
            recognition = new SpeechRecognition();
        } else {
            console.error('Speech recognition not supported');
            return;
        }
    }
    
    // Configure recognition with maximum permissiveness and no content filtering
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    // Attempt to disable any potential content filtering
    if (typeof recognition.maxAlternatives === 'number') {
        recognition.maxAlternatives = 5; // Get multiple alternatives to increase chances of capturing filtered content
    }
    
    // Try to make recognition more sensitive
    if (typeof recognition.audioThreshold === 'number') {
        recognition.audioThreshold = 0; // Set to lowest possible value
    }
    
    // Try to disable profanity filter if possible
    try {
        recognition.profanityFilter = false;
    } catch (e) {
        console.warn('Could not disable profanity filter');
    }
    
    // Enhanced text cleaning with best transcript selection for controversial content
    let finalTranscript = '';
    let interimTranscript = '';
    
    // Function to check for quiet time and auto-submit
    function checkForQuietTime() {
        if (!isRecording) return;
        
        const currentTime = Date.now();
        const timeSinceLastSpeech = currentTime - lastSpeechTime;
        
        // If quiet for more than 7 seconds and we have some transcript, auto-submit
        if (timeSinceLastSpeech > 7000 && targetTextarea && targetTextarea.value.trim().length > 0) {
            console.log('Auto-submitting after quiet period:', timeSinceLastSpeech);
            
            // Auto-submit the form
            const form = targetTextarea.closest('form');
            if (form) {
                // Stop recording first
                stopRecording();
                // Then submit the form
                setTimeout(() => {
                    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }, 100);
            }
        } else {
            // Check again in 1 second
            quietTimeoutId = setTimeout(checkForQuietTime, 1000);
        }
    }
    
    // Special words to prioritize if multiple transcription alternatives exist
    const priorityWords = [
        { search: 'scammed', replace: 'scammed' },
        { search: 'phishing', replace: 'phishing' },
        { search: 'hacker', replace: 'hacker' },
        { search: 'unsecured', replace: 'unsecured' },
        { search: 'credentials', replace: 'credentials' },
        { search: 'vulnerable', replace: 'vulnerable' }
    ];
    
    recognition.onresult = function(event) {
        // Reset last speech time when we get a result
        lastSpeechTime = Date.now();
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            // Find the best transcript from all alternatives
            let bestTranscript = '';
            let bestConfidence = 0;
            let foundPreferredWord = false;
            
            // If alternatives are available, try to find the best one
            const numAlternatives = event.results[i].length || 1;
            
            for (let alt = 0; alt < numAlternatives; alt++) {
                const currentTranscript = event.results[i][alt].transcript;
                const currentConfidence = event.results[i][alt].confidence || 0.5;
                let hasPriorityWord = false;
                
                // Check if this alternative contains any priority words
                for (const priority of priorityWords) {
                    if (currentTranscript.toLowerCase().includes(priority.search)) {
                        console.log(`Found priority word "${priority.search}" in alternative ${alt}`);
                        hasPriorityWord = true;
                        
                        // If we found a priority word and haven't found one before,
                        // or if this has higher confidence than our previous priority word choice
                        if (!foundPreferredWord || currentConfidence > bestConfidence) {
                            bestConfidence = currentConfidence;
                            bestTranscript = currentTranscript;
                            foundPreferredWord = true;
                        }
                        break;
                    }
                }
                
                // If no priority word was found in this alternative, use standard confidence scoring
                if (!hasPriorityWord && !foundPreferredWord && currentConfidence > bestConfidence) {
                    bestConfidence = currentConfidence;
                    bestTranscript = currentTranscript;
                }
                
                // Look for markers indicating potential content filtering/censoring
                const censoringIndicators = [
                    'unprofessional', 'inappropriate', 'unacceptable', 'profanity', 
                    'demonstrates', 'lack of', 'workplace', 'setting', 'empathy',
                    'judgment', 'immediately disqualify', 'candidate', 
                    'shows no', 'understanding', 'address', 'constructively'
                ];
                
                // Check if this transcript contains indicators of censored content
                const containsCensoringIndicators = censoringIndicators.some(
                    keyword => currentTranscript.toLowerCase().includes(keyword)
                );
                
                if (containsCensoringIndicators) {
                    console.log(`Detected potential censoring in transcript: "${currentTranscript}"`);
                    // Prioritize transcripts that mention these keywords as they likely represent feedback about censored content
                    bestTranscript = currentTranscript;
                    break;
                }
                
                // Attempt to detect "stopped transcription" - common when speech recognition encounters censored content
                if (currentTranscript.trim().endsWith('shows') || 
                    currentTranscript.trim().endsWith('shows no') ||
                    currentTranscript.trim().endsWith('...') ||
                    currentTranscript.trim().endsWith('the answer shows')) {
                    console.log(`Detected possibly truncated censored content: "${currentTranscript}"`);
                    
                    // Append a marker so the user knows transcription may have been cut off
                    bestTranscript = currentTranscript + " [TRANSCRIPTION MAY BE INCOMPLETE DUE TO CONTENT FILTERING]";
                    break;
                }
            }
            
            // Use the best transcript
            if (event.results[i].isFinal) {
                // Remove extra spaces from the transcript
                const cleanTranscript = bestTranscript.trim();
                finalTranscript += cleanTranscript + ' ';
            } else {
                interimTranscript = bestTranscript;
                
                // Also display interim results in the textarea so the user can see what's being transcribed
                if (targetTextarea) {
                    // Store the current final transcript
                    const currentFinalText = finalTranscript.trim();
                    
                    // Show both the final and interim text in the textarea
                    targetTextarea.value = currentFinalText + (currentFinalText ? ' ' : '') + interimTranscript;
                    
                    // Set cursor to the end
                    targetTextarea.scrollTop = targetTextarea.scrollHeight;
                }
            }
        }
        
        // Update textarea content - now accepts all recognized speech
        if (finalTranscript) {
            // Reset restart count on successful recognition
            restartCount = 0;
            
            // Clean up the transcript by removing duplicate spaces and fixing common speech recognition issues
            let cleanFinalTranscript = finalTranscript.trim();
            
            // Create a display element to show both versions if they don't match
            // This will be used to create a confirmation UI 
            let originalText = cleanFinalTranscript;
            
            // Only apply fixes for fishing/phishing which are well-known terms
            cleanFinalTranscript = cleanFinalTranscript
                // Fix common security term recognition issues
                .replace(/\bfish attack\b/gi, "phish attack")
                .replace(/\bfishing attack\b/gi, "phishing attack")
                
                // Fix "a lot" recognition issues
                .replace(/ lot of /gi, " a lot of ")
                // Fix "like" recognition issues
                .replace(/ life /gi, " like ")
                // Fix "by" recognition issues
                .replace(/ buy /gi, " by ")
                // Fix "some" vs "someone" recognition issues
                .replace(/some scammed/gi, "someone scammed")
                // Remove multiple spaces
                .replace(/\s{2,}/g, " ");
                
            // Show the original and scammed versions in the status display
            if (originalText.includes("scared") || originalText.includes("scant") || originalText.includes("scand")) {
                // Add a message that the user can manually correct if needed
                statusElement.innerHTML = 'Speech recognized. If you meant "scammed" instead of "scared", click here to correct.';
                
                // Make it clickable to replace scared with scammed if desired
                statusElement.style.cursor = 'pointer';
                statusElement.onclick = function() {
                    let scammedVersion = targetTextarea.value
                        .replace(/scared/gi, "scammed")
                        .replace(/\bscant\b/gi, "scammed")
                        .replace(/\bscand\b/gi, "scammed");
                    targetTextarea.value = scammedVersion;
                    statusElement.innerHTML = 'Text corrected to use "scammed"';
                    statusElement.onclick = null;
                    statusElement.style.cursor = 'default';
                };
            }
            
            // Clear any previous content and set the final transcript
            targetTextarea.value = cleanFinalTranscript;
            
            // Simulate user input to trigger any input events
            const inputEvent = new Event('input', { bubbles: true });
            targetTextarea.dispatchEvent(inputEvent);
            
            // Also log what was added to help with debugging
            console.log(`Added to textarea: "${cleanFinalTranscript}"`);
        }
        
        // Show interim transcript in status element
        if (interimTranscript) {
            statusElement.innerHTML = '<strong>Listening:</strong> ' + interimTranscript;
            statusElement.style.color = '#007bff'; // Make the interim text blue for visibility
        } else if (isRecording) {
            statusElement.innerHTML = '<strong>Listening...</strong> (speak now)';
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
                            statusElement.innerHTML = '<strong>Listening...</strong> (speak now)';
                            statusElement.style.color = '#007bff';
                            statusElement.style.padding = '5px';
                            statusElement.style.borderRadius = '3px';
                            statusElement.style.backgroundColor = '#f0f8ff';
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
        lastSpeechTime = Date.now(); // Reset the last speech time
        
        // Start the quiet time checker
        if (quietTimeoutId) clearTimeout(quietTimeoutId);
        quietTimeoutId = setTimeout(checkForQuietTime, 1000);
        
        try {
            recognition.start();
            console.log('Speech recognition started');
            
            toggleButton.innerHTML = '<i class="fas fa-microphone-slash"></i> Stop Voice';
            toggleButton.classList.remove('btn-outline-primary');
            toggleButton.classList.add('btn-danger');
            statusElement.classList.remove('d-none');
            statusElement.innerHTML = '<strong>Listening...</strong> (speak now)';
            statusElement.style.color = '#007bff';
            statusElement.style.padding = '5px';
            statusElement.style.borderRadius = '3px';
            statusElement.style.backgroundColor = '#f0f8ff';
        } catch (e) {
            console.error('Error starting speech recognition:', e);
            isRecording = false;
            statusElement.textContent = 'Failed to start voice input';
        }
    }
    
    // Stop recording
    function stopRecording() {
        isRecording = false;
        
        // Clear any quiet time timeout
        if (quietTimeoutId) {
            clearTimeout(quietTimeoutId);
            quietTimeoutId = null;
        }
        
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
    
    // Auto-start voice input after model speaks
    if (typeof speechSynthesisManager !== 'undefined') {
        const originalSpeak = speechSynthesisManager.speak;
        
        speechSynthesisManager.speak = function(text, callback) {
            originalSpeak.call(speechSynthesisManager, text, function() {
                // After the model finishes speaking, wait a moment and start recording
                setTimeout(() => {
                    if (!isRecording) {
                        console.log('Auto-starting voice input after model speech');
                        startRecording();
                    }
                }, 500);
                
                // Still call the original callback if provided
                if (callback) callback();
            });
        };
    }
}