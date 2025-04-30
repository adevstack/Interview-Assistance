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
    
    // Set any other available properties to maximize permissiveness
    // These are experimental and may not be supported in all browsers
    try {
        // @ts-ignore - These properties may not be in the type definitions
        if (typeof recognition.profanityFilter !== 'undefined') {
            recognition.profanityFilter = false;
        }
    } catch (e) {
        console.log('Ignored setting experimental speech recognition properties:', e);
    }
    
    // Handle speech recognition results with multiple alternatives
    recognition.onresult = function(event) {
        let interimTranscript = '';
        let finalTranscript = '';
        
        // For debugging - log the entire results object
        console.log('Full speech recognition results:', JSON.stringify(event.results));
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            // Check if we have multiple alternatives
            const numAlternatives = event.results[i].length;
            console.log(`Result ${i} has ${numAlternatives} alternatives`);
            
            // Try each alternative in order of priority, then confidence
            let bestTranscript = '';
            let bestConfidence = -1;
            let foundPreferredWord = false;
            
            // Security/fraud-specific words to prioritize regardless of confidence
            const priorityWords = [
                {search: "scammed", priority: 1},
                {search: "scammer", priority: 1},
                {search: "phishing", priority: 1},
                {search: "fraud", priority: 1},
                {search: "cybersecurity", priority: 1},
                {search: "attack", priority: 1}
            ];
            
            // Check all alternatives to find the best one
            for (let alt = 0; alt < numAlternatives; alt++) {
                const currentTranscript = event.results[i][alt].transcript;
                const currentConfidence = event.results[i][alt].confidence;
                
                console.log(`Alternative ${alt}: "${currentTranscript}" (confidence: ${currentConfidence})`);
                
                // Check if this alternative contains any priority words we want to favor
                let hasPriorityWord = false;
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
                interimTranscript += bestTranscript;
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
            
            // Only add space if needed between existing text and new text
            if (targetTextarea.value) {
                const lastChar = targetTextarea.value.slice(-1);
                if (lastChar !== ' ' && lastChar !== '\n') {
                    targetTextarea.value += ' ';
                }
            }
            
            targetTextarea.value += cleanFinalTranscript;
            
            // Simulate user input to trigger any input events
            const inputEvent = new Event('input', { bubbles: true });
            targetTextarea.dispatchEvent(inputEvent);
            
            // Also log what was added to help with debugging
            console.log(`Added to textarea: "${cleanFinalTranscript}"`);
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
