/**
 * Text-to-speech functionality for interview questions
 */

class SpeechSynthesisManager {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isSpeaking = false;
        this.utterance = null;
        
        // Check for browser support
        this.isSupported = 'speechSynthesis' in window;
        
        // Set default voice
        this.voice = null;
        this.setDefaultVoice();
    }
    
    // Load and set default voice
    setDefaultVoice() {
        if (!this.isSupported) return;
        
        // Get available voices (might load asynchronously)
        const setVoice = () => {
            const voices = this.synth.getVoices();
            if (voices.length === 0) return;
            
            // Prefer English voices with higher quality
            // Try to find premium/enhanced voices first
            const preferredVoices = [
                // Look for high-quality English voices first
                v => v.name.includes('Premium') && v.lang.startsWith('en'),
                v => v.name.includes('Enhanced') && v.lang.startsWith('en'),
                v => v.name.includes('Neural') && v.lang.startsWith('en'),
                
                // Then any English voice
                v => v.lang.startsWith('en'),
                
                // Then any voice as fallback
                v => true
            ];
            
            // Find the first voice that matches our preferences
            for (const predicate of preferredVoices) {
                const voice = voices.find(predicate);
                if (voice) {
                    this.voice = voice;
                    console.log('Selected voice:', voice.name);
                    break;
                }
            }
        };
        
        // Some browsers load voices asynchronously
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = setVoice;
        }
        
        // Try to set immediately in case voices are already loaded
        setVoice();
    }
    
    // Speak text aloud with handling for content filtering
    speak(text, callback) {
        if (!this.isSupported || !text) {
            if (callback) callback();
            return;
        }
        
        console.log('Original text to speak:', JSON.stringify(text));
        
        // Browsers often filter content in text-to-speech
        // To avoid this, we'll use a chunked approach for all text
        this.speakInChunks(text, callback);
    }
    
    // Break text into chunks and speak them individually to avoid content filtering
    speakInChunks(text, finalCallback) {
        console.log('Using chunked approach for all text to avoid filtering');
        
        // Break text into meaningful chunks at sentence boundaries
        // Sentences are more likely to be spoken naturally than arbitrary chunks
        const sentences = text
            .replace(/([.?!])\s+/g, '$1|')  // Split on sentence endings
            .split('|')
            .filter(s => s.trim());  // Remove empty strings
        
        console.log(`Text split into ${sentences.length} phrase chunks`);
        
        // Function to speak each chunk in sequence
        const speakNextChunk = (index) => {
            if (index >= sentences.length) {
                if (finalCallback) finalCallback();
                return;
            }
            
            const chunk = sentences[index].trim();
            if (!chunk) {
                speakNextChunk(index + 1);
                return;
            }
            
            console.log(`Speaking chunk ${index+1}/${sentences.length}: ${JSON.stringify(chunk)}`);
            
            // Create a new utterance for each chunk
            const utterance = new SpeechSynthesisUtterance(chunk);
            
            // Set voice if we have one
            if (this.voice) {
                utterance.voice = this.voice;
            }
            
            // Configure speech parameters for clarity
            utterance.rate = 0.9;  // Slightly slower for clarity
            utterance.pitch = 1.0; // Normal pitch
            utterance.volume = 1.0; // Full volume
            
            // Events
            utterance.onend = () => {
                speakNextChunk(index + 1);
            };
            
            utterance.onerror = (e) => {
                console.error('Speech synthesis error:', e);
                speakNextChunk(index + 1);
            };
            
            // Speak the current chunk
            this.synth.speak(utterance);
        };
        
        // Start speaking the first chunk
        speakNextChunk(0);
    }
    
    // Stop speaking
    stop() {
        if (this.isSupported) {
            this.synth.cancel();
        }
    }
    
    // Toggle pause/resume
    togglePause() {
        if (!this.isSupported) return;
        
        if (this.synth.speaking) {
            if (this.synth.paused) {
                this.synth.resume();
            } else {
                this.synth.pause();
            }
        }
    }
}

/**
 * Global instance for use in the application
 */
const speechSynthesisManager = new SpeechSynthesisManager();

/**
 * Automatically speak the interview question in chat interface
 */
function initSpeechForInterviewQuestions() {
    document.addEventListener('DOMContentLoaded', function() {
        // Find all interviewer messages (questions)
        const interviewerMessages = document.querySelectorAll('.chat-message.interviewer .message-content p');
        
        // Add speak button to each interviewer message
        interviewerMessages.forEach((message) => {
            const speakButton = document.createElement('button');
            speakButton.className = 'btn btn-sm btn-outline-secondary speak-btn ms-2';
            speakButton.innerHTML = '<i class="fas fa-volume-up"></i>';
            speakButton.title = 'Read this question aloud';
            speakButton.onclick = function() {
                const text = message.textContent.trim();
                speechSynthesisManager.speak(text);
            };
            
            // Add button after the message
            message.parentNode.appendChild(speakButton);
        });
        
        // Auto-speak the most recent question
        if (interviewerMessages.length > 0) {
            const latestQuestion = interviewerMessages[interviewerMessages.length - 1];
            const text = latestQuestion.textContent.trim();
            speechSynthesisManager.speak(text);
        }
    });
}

// Initialize immediately
initSpeechForInterviewQuestions();