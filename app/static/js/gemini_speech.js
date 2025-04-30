/**
 * Advanced speech recognition with Gemini API integration
 * This provides an alternative to the browser's built-in speech recognition
 * with more accurate transcription particularly for specialized vocabulary.
 */

class GeminiSpeechRecognition {
    constructor(statusElement, audioFormat = 'audio/webm') {
        this.statusElement = statusElement;
        this.isRecording = false;
        this.audioFormat = audioFormat;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.onResultCallback = null;
        this.onEndCallback = null;
        this.onErrorCallback = null;
    }

    /**
     * Set callback for when transcription results are available
     */
    set onresult(callback) {
        this.onResultCallback = callback;
    }

    /**
     * Set callback for when recognition ends
     */
    set onend(callback) {
        this.onEndCallback = callback;
    }

    /**
     * Set callback for errors
     */
    set onerror(callback) {
        this.onErrorCallback = callback;
    }

    /**
     * Start recording audio for Gemini speech recognition
     */
    start() {
        if (this.isRecording) {
            console.warn('Speech recognition already started');
            return;
        }
        
        this.isRecording = true;
        this.audioChunks = [];
        
        // Request microphone access
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.mediaRecorder = new MediaRecorder(stream, { mimeType: this.audioFormat });
                
                // Store audio chunks as they become available
                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        this.audioChunks.push(event.data);
                    }
                };
                
                // When recording stops, send data to Gemini API
                this.mediaRecorder.onstop = () => {
                    this.processAudioWithGemini();
                    
                    // Close the microphone stream
                    stream.getTracks().forEach(track => track.stop());
                    
                    if (this.onEndCallback) {
                        this.onEndCallback();
                    }
                };
                
                // Start recording
                this.mediaRecorder.start(1000); // Collect data in 1-second chunks
                
                if (this.statusElement) {
                    this.statusElement.textContent = 'Listening with Gemini...';
                }
                
                console.log('Gemini speech recognition started');
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                this.isRecording = false;
                
                if (this.statusElement) {
                    this.statusElement.textContent = 'Error accessing microphone';
                }
                
                if (this.onErrorCallback) {
                    this.onErrorCallback({ error: 'microphone-access-error', details: error });
                }
            });
    }
    
    /**
     * Stop recording audio
     */
    stop() {
        if (!this.isRecording || !this.mediaRecorder) {
            return;
        }
        
        this.isRecording = false;
        
        try {
            this.mediaRecorder.stop();
            console.log('Gemini speech recognition stopped');
            
            if (this.statusElement) {
                this.statusElement.textContent = 'Processing with Gemini...';
            }
        } catch (error) {
            console.error('Error stopping Gemini speech recognition:', error);
            
            if (this.onErrorCallback) {
                this.onErrorCallback({ error: 'stop-error', details: error });
            }
        }
    }
    
    /**
     * Process recorded audio with Gemini API for transcription
     */
    processAudioWithGemini() {
        if (this.audioChunks.length === 0) {
            console.warn('No audio recorded');
            
            if (this.onErrorCallback) {
                this.onErrorCallback({ error: 'no-audio', details: 'No audio was recorded' });
            }
            return;
        }
        
        // Create a blob from the audio chunks
        const audioBlob = new Blob(this.audioChunks, { type: this.audioFormat });
        console.log(`Audio size: ${audioBlob.size} bytes`);
        
        // Update status to show we're processing
        if (this.statusElement) {
            this.statusElement.textContent = 'Processing speech with Gemini...';
        }
        
        // Convert blob to base64 for API submission
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1]; // Remove data URL prefix
            
            // Show a spinner or indication that processing is happening
            if (this.statusElement) {
                this.statusElement.innerHTML = '<strong>Processing with Gemini...</strong> <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                this.statusElement.style.color = '#ff9900';  // Orange color to indicate processing
            }
            
            // Send to our backend endpoint that will forward to Gemini API
            fetch('/api/speech_recognition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audio_data: base64Audio,
                    audio_format: this.audioFormat
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Gemini transcription result:', data);
                
                // Display the raw transcription temporarily in the status
                if (this.statusElement && data.transcript) {
                    this.statusElement.innerHTML = '<strong>Recognized:</strong> <span style="color: green;">' + data.transcript + '</span>';
                    this.statusElement.style.color = 'black';
                    this.statusElement.style.padding = '10px';
                    this.statusElement.style.border = '1px solid #ddd';
                    this.statusElement.style.borderRadius = '5px';
                    this.statusElement.style.backgroundColor = '#f8f9fa';
                    
                    // Clear the styling after showing for a while
                    setTimeout(() => {
                        if (this.statusElement) {
                            this.statusElement.textContent = '';
                            this.statusElement.style.padding = '';
                            this.statusElement.style.border = '';
                            this.statusElement.style.borderRadius = '';
                            this.statusElement.style.backgroundColor = '';
                        }
                    }, 8000);
                }
                
                if (this.onResultCallback && data.transcript) {
                    // Create a synthetic result object that mimics the browser's SpeechRecognition format
                    const syntheticResult = {
                        results: [
                            [{
                                transcript: data.transcript,
                                confidence: 0.95, // Gemini is generally high confidence
                                isFinal: true
                            }]
                        ]
                    };
                    syntheticResult.results[0].isFinal = true;
                    
                    this.onResultCallback(syntheticResult);
                }
            })
            .catch(error => {
                console.error('Error with Gemini transcription:', error);
                
                if (this.statusElement) {
                    this.statusElement.textContent = 'Transcription error';
                }
                
                if (this.onErrorCallback) {
                    this.onErrorCallback({ error: 'transcription-error', details: error });
                }
            });
        };
    }
}

/**
 * Create a hybrid voice recognition system that tries to use Gemini first,
 * but falls back to the browser's built-in speech recognition if needed.
 */
function createHybridSpeechRecognition(statusElement) {
    // First try to detect if our browser supports MediaRecorder for Gemini integration
    let supportsMediaRecorder = false;
    
    try {
        supportsMediaRecorder = 'MediaRecorder' in window && 
            MediaRecorder.isTypeSupported('audio/webm');
    } catch (e) {
        console.warn('MediaRecorder not available, using browser speech recognition only');
    }
    
    // Default to browser's built-in recognition
    let recognition = null;
    
    if (supportsMediaRecorder) {
        try {
            // Create Gemini-powered recognition
            recognition = new GeminiSpeechRecognition(statusElement);
            console.log('Using Gemini speech recognition');
        } catch (e) {
            console.error('Error creating Gemini speech recognition:', e);
            supportsMediaRecorder = false;
        }
    }
    
    if (!supportsMediaRecorder) {
        // Fall back to browser's built-in recognition
        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.maxAlternatives = 5;
            
            try {
                // Try to disable profanity filter
                recognition.profanityFilter = false;
            } catch (e) {
                console.warn('Could not disable profanity filter');
            }
            
            console.log('Using browser speech recognition');
        } catch (e) {
            console.error('Speech recognition not available:', e);
            
            if (statusElement) {
                statusElement.textContent = 'Speech recognition not available';
            }
            
            return null;
        }
    }
    
    return recognition;
}